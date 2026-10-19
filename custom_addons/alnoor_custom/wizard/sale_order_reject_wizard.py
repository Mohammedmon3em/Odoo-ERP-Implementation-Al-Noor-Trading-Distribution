from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrderRejectWizard(models.TransientModel):
    _name = 'sale.order.reject.wizard'
    _description = 'Reject High Value / Credit Limit Exceeded Order'

    order_id = fields.Many2one('sale.order', string="Sales Order", required=True)
    rejection_reason = fields.Text(string="Rejection Reason", required=True)

    def action_confirm_rejection(self):
        self.ensure_one()
        if not self.rejection_reason or not self.rejection_reason.strip():
            raise UserError(_("Rejection reason is mandatory (BR-107). Please enter a valid reason."))

        order = self.order_id
        # Check permissions (BR-103)
        is_approver = self.env.user.has_group('alnoor_custom.group_credit_limit_approver') or \
                      self.env.user.has_group('sales_team.group_sale_manager') or \
                      self.env.is_superuser()
        if not is_approver:
            raise UserError(_("Only a Sales Manager or General Manager can reject orders (BR-103)."))

        order.write({
            'approval_status': 'rejected',
            'rejected_by_id': self.env.user.id,
            'rejection_date': fields.Datetime.now(),
            'rejection_reason': self.rejection_reason.strip(),
        })

        order.message_post(
            body=_(
                "<b>Order Credit Limit Approval Rejected</b> by %(user)s.<br/><b>Reason:</b> %(reason)s",
                user=self.env.user.name,
                reason=self.rejection_reason.strip()
            ),
            subtype_xmlid="mail.mt_comment"
        )
        return {'type': 'ir.actions.act_window_close'}
