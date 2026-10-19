from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char(
        string="Customer Code",
        index=True,
        copy=False,
        help="Unique customer identifier code for Al Noor Trading."
    )

    customer_type = fields.Selection(
        [
            ('retail', 'Retail'),
            ('wholesale', 'Wholesale'),
            ('vip', 'VIP'),
        ],
        string="Customer Type",
        default='retail',
        tracking=True,
        help="Classification of customer for pricing, reporting, and credit policies."
    )

    @api.onchange('credit_limit')
    def _onchange_credit_limit_enable(self):
        for partner in self:
            if partner.credit_limit > 0:
                partner.use_partner_credit_limit = True
