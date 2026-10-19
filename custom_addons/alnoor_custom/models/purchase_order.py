from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_high_value_po = fields.Boolean(
        string="High Value Order (>= 50,000 SAR)",
        compute="_compute_is_high_value_po",
        store=True,
        help="Indicates if the purchase order total is greater than or equal to 50,000 SAR and requires Purchase Manager confirmation."
    )

    @api.depends('amount_total')
    def _compute_is_high_value_po(self):
        for order in self:
            order.is_high_value_po = (order.amount_total >= 50000.0)

    def _approval_allowed(self):
        """Returns whether the order qualifies to be confirmed/approved by the current user."""
        self.ensure_one()
        # If total amount is >= 50,000 SAR, strictly require Purchase Manager or General Manager
        if self.amount_total >= 50000.0:
            is_manager = self.env.user.has_group('purchase.group_purchase_manager') or \
                         self.env.user.has_group('alnoor_custom.group_credit_limit_approver') or \
                         self.env.is_superuser()
            return is_manager
        return super()._approval_allowed()

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            if order.amount_total >= 50000.0:
                is_manager = order._approval_allowed()
                if not is_manager:
                    order.write({'state': 'to approve'})
                    order.message_post(
                        body=_(
                            "<b>Purchase Manager Approval Required:</b> Order total (%(amount)s %(currency)s) is greater than or equal to 50,000 SAR. "
                            "Submitted to <b>Purchase Manager</b> for confirmation.",
                            amount=f"{order.amount_total:,.2f}",
                            currency=order.currency_id.name or "SAR"
                        ),
                        subtype_xmlid="mail.mt_comment"
                    )
                    raise UserError(_(
                        "Purchase Order Approval Required!\n"
                        "The total amount (%(amount)s %(currency)s) is greater than or equal to 50,000 SAR.\n"
                        "This order has been set to 'Waiting for Approval' and can ONLY be confirmed by the Purchase Manager.",
                        amount=f"{order.amount_total:,.2f}",
                        currency=order.currency_id.name or "SAR"
                    ))
        return super().button_confirm()

    def button_approve(self, force=False):
        for order in self:
            if order.amount_total >= 50000.0:
                is_manager = order._approval_allowed()
                if not is_manager:
                    raise UserError(_(
                        "Access Denied: Purchase orders of 50,000 SAR or more can only be confirmed/approved by the Purchase Manager or General Manager."
                    ))
        res = super().button_approve(force=force)
        for order in self:
            if order.amount_total >= 50000.0:
                order.message_post(
                    body=_(
                        "<b>High-Value Purchase Order Approved:</b> Confirmed by %(user)s on %(date)s.",
                        user=self.env.user.name,
                        date=fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ),
                    subtype_xmlid="mail.mt_comment"
                )
        return res
