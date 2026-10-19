{
    'name': 'Al Noor Trading Customizations',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Custom Odoo module developed specifically for Al Noor Trading & Distribution.',
    'description': """
Al Noor Trading & Distribution Custom ERP Module
================================================
- Customer Enhancements (Customer Code, Customer Type: Retail/Wholesale/VIP, Credit Limit)
- Sales Credit Limit Validation & Multi-Tier Approval Workflow
- Approval Status, Approval History (Approved By, Date, Notes / Rejected By, Date, Reason)
- Strict Business Rule Enforcement (BR-101 to BR-108)
- Reporting filters and dashboards
    """,
    'author': 'Al Noor Trading & Distribution',
    'website': 'https://www.alnoortrading.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'crm',
        'sale_management',
        'purchase',
        'stock',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/sale_order_reject_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'data/payment_term_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
