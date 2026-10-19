from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    approval_status = fields.Selection(
        [
            ('not_required', 'Not Required'),
            ('pending', 'Waiting for Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string="Approval Status",
        default='not_required',
        tracking=True,
        copy=False,
        help="Approval status based on customer credit limit check."
    )

    approved_by_id = fields.Many2one(
        'res.users',
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True
    )

    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
        copy=False,
        tracking=True
    )

    approval_notes = fields.Text(
        string="Approval Notes",
        copy=False
    )

    rejected_by_id = fields.Many2one(
        'res.users',
        string="Rejected By",
        readonly=True,
        copy=False,
        tracking=True
    )

    rejection_date = fields.Datetime(
        string="Rejection Date",
        readonly=True,
        copy=False,
        tracking=True
    )

    rejection_reason = fields.Text(
        string="Rejection Reason",
        copy=False,
        tracking=True
    )

    partner_credit_limit = fields.Float(
        related='partner_id.credit_limit',
        string="Customer Credit Limit",
        readonly=True
    )

    customer_type = fields.Selection(
        related='partner_id.customer_type',
        string="Customer Type",
        store=True,
        readonly=True
    )

    is_credit_limit_exceeded = fields.Boolean(
        string="Credit Limit Exceeded",
        compute='_compute_credit_limit_status',
        store=True
    )

    credit_limit_difference = fields.Monetary(
        string="Amount Over Limit",
        compute='_compute_credit_limit_status',
        store=True
    )

    @api.depends('partner_id', 'partner_id.credit_limit', 'partner_id.credit', 'amount_total')
    def _compute_credit_limit_status(self):
        for order in self:
            partner = order.partner_id
            limit = partner.credit_limit or 0.0
            if limit > 0:
                current_receivable = partner.credit or 0.0
                total_exposure = current_receivable + order.amount_total
                if total_exposure > limit or order.amount_total > limit:
                    order.is_credit_limit_exceeded = True
                    order.credit_limit_difference = max(total_exposure - limit, order.amount_total - limit)
                else:
                    order.is_credit_limit_exceeded = False
                    order.credit_limit_difference = 0.0
            else:
                order.is_credit_limit_exceeded = False
                order.credit_limit_difference = 0.0

    def action_request_approval(self):
        """Action for Salesperson to submit an order exceeding credit limit for approval."""
        for order in self:
            if not order.is_credit_limit_exceeded:
                order.approval_status = 'not_required'
                continue

            order.write({
                'approval_status': 'pending',
                'rejection_reason': False,
                'rejected_by_id': False,
                'rejection_date': False,
            })
            order.message_post(
                body=_(
                    "<b>Approval Requested:</b> Sales Order %(name)s exceeds customer credit limit (Limit: %(limit)s, Order: %(order)s). Waiting for Sales Manager / General Manager approval.",
                    name=order.name,
                    limit=order.partner_credit_limit,
                    order=order.amount_total
                ),
                subtype_xmlid="mail.mt_comment"
            )
        return True

    def action_approve_credit_limit(self):
        """Action for Manager to approve an order exceeding credit limit."""
        for order in self:
            # BR-102: Salesperson cannot approve their own order
            if order.user_id == self.env.user and not self.env.is_superuser():
                raise UserError(_("Salesperson cannot approve their own order (BR-102)."))

            # BR-103: Only Sales Manager or General Manager can approve
            is_approver = self.env.user.has_group('alnoor_custom.group_credit_limit_approver') or \
                          self.env.user.has_group('sales_team.group_sale_manager') or \
                          self.env.is_superuser()
            if not is_approver:
                raise UserError(_("Access Denied: Only a Sales Manager or General Manager can approve this order (BR-103)."))

            order.write({
                'approval_status': 'approved',
                'approved_by_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
            order.message_post(
                body=_(
                    "<b>Order Approved:</b> Credit limit exception approved by %(user)s on %(date)s (BR-105, BR-106).",
                    user=self.env.user.name,
                    date=fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ),
                subtype_xmlid="mail.mt_comment"
            )
        return True

    def action_reject_credit_limit(self):
        """Open the rejection wizard to enter the mandatory rejection reason (BR-107)."""
        self.ensure_one()
        is_approver = self.env.user.has_group('alnoor_custom.group_credit_limit_approver') or \
                      self.env.user.has_group('sales_team.group_sale_manager') or \
                      self.env.is_superuser()
        if not is_approver:
            raise UserError(_("Access Denied: Only a Sales Manager or General Manager can reject orders (BR-103)."))

        return {
            'name': _('Reject Credit Limit Exception'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    def action_confirm(self):
        """Override action_confirm to enforce BR-101 and BR-104."""
        for order in self:
            if order.is_credit_limit_exceeded and order.approval_status != 'approved':
                # BR-104: Rejected order cannot be confirmed unless re-submitted
                if order.approval_status == 'rejected':
                    raise UserError(_(
                        "Cannot confirm rejected order (BR-104)!\n"
                        "Reason: %(reason)s\n"
                        "Please request approval again for review before confirmation.",
                        reason=order.rejection_reason or _("No reason specified")
                    ))
                # BR-101: Cannot confirm if credit limit exceeded without approval
                order.write({'approval_status': 'pending'})
                raise UserError(_(
                    "Credit Limit Exceeded (BR-101)!\n"
                    "Customer credit limit: %(limit)s SAR.\n"
                    "Total exposure exceeds limit. Order has been moved to 'Waiting for Approval'.\n"
                    "Please request approval from your Sales Manager or General Manager.",
                    limit=order.partner_credit_limit
                ))

        return super().action_confirm()
