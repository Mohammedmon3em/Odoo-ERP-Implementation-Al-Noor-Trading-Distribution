# Configure Al Noor Trading Environment
wh = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1)
if wh:
    wh.name = 'Al Noor Main Warehouse'
    print(f"Warehouse updated to: {wh.name} ({wh.code})")

# Ensure Locations: WH/Input, WH/Stock, WH/Output, WH/Returns
stock_loc = wh.lot_stock_id # WH/Stock
parent_loc = wh.view_location_id

input_loc = env['stock.location'].search([('name', '=', 'Input'), ('location_id', '=', parent_loc.id)], limit=1)
if not input_loc:
    input_loc = env['stock.location'].create({
        'name': 'Input',
        'usage': 'internal',
        'location_id': parent_loc.id,
    })
print("Input Location:", input_loc.complete_name)

output_loc = env['stock.location'].search([('name', '=', 'Output'), ('location_id', '=', parent_loc.id)], limit=1)
if not output_loc:
    output_loc = env['stock.location'].create({
        'name': 'Output',
        'usage': 'internal',
        'location_id': parent_loc.id,
    })
print("Output Location:", output_loc.complete_name)

returns_loc = env['stock.location'].search([('name', '=', 'Returns'), ('location_id', '=', parent_loc.id)], limit=1)
if not returns_loc:
    returns_loc = env['stock.location'].create({
        'name': 'Returns',
        'usage': 'internal',
        'location_id': parent_loc.id,
    })
print("Returns Location:", returns_loc.complete_name)

# Assign Approver Group to Sales Manager & General Manager
approver_group = env.ref('alnoor_custom.group_credit_limit_approver')
sal_manager = env['res.users'].search([('login', '=', 'SalManager')], limit=1)
gen_manager = env['res.users'].search([('login', '=', 'GenManager')], limit=1)

if sal_manager and approver_group not in sal_manager.group_ids:
    sal_manager.write({'group_ids': [(4, approver_group.id)]})
    print("SalManager added to Credit Limit Approvers")

if gen_manager and approver_group not in gen_manager.group_ids:
    gen_manager.write({'group_ids': [(4, approver_group.id)]})
    print("GenManager added to Credit Limit Approvers")

# Configure Customers with Customer Code, Customer Type, and Credit Limits
customers_data = [
    {
        'name': 'ABC Electronics',
        'customer_code': 'CUST-001',
        'customer_type': 'wholesale',
        'credit_limit': 50000.0,
        'use_partner_credit_limit': True,
        'email': 'orders@abcelectronics.com',
        'phone': '+966501234567',
        'is_company': True,
    },
    {
        'name': 'Hasibat AlArab',
        'customer_code': 'CUST-002',
        'customer_type': 'wholesale',
        'credit_limit': 60000.0,
        'use_partner_credit_limit': True,
        'email': 'info@hasibat.com',
        'phone': '+966502345678',
        'is_company': True,
    },
    {
        'name': 'JabarTech',
        'customer_code': 'CUST-003',
        'customer_type': 'vip',
        'credit_limit': 80000.0,
        'use_partner_credit_limit': True,
        'email': 'procurement@jabartech.com',
        'phone': '+966503456789',
        'is_company': True,
    },
    {
        'name': 'Banda Retail',
        'customer_code': 'CUST-004',
        'customer_type': 'retail',
        'credit_limit': 20000.0,
        'use_partner_credit_limit': True,
        'email': 'banda@bandaretail.com',
        'phone': '+966504567890',
        'is_company': True,
    },
    {
        'name': 'ALOthaim Trading',
        'customer_code': 'CUST-005',
        'customer_type': 'vip',
        'credit_limit': 100000.0,
        'use_partner_credit_limit': True,
        'email': 'supply@alothaim.com',
        'phone': '+966505678901',
        'is_company': True,
    },
]

for cd in customers_data:
    cust = env['res.partner'].search(['|', ('name', '=', cd['name']), ('customer_code', '=', cd['customer_code'])], limit=1)
    if not cust:
        cust = env['res.partner'].create(cd)
        print(f"Created Customer: {cust.name} (Code: {cust.customer_code}, Limit: {cust.credit_limit})")
    else:
        cust.write(cd)
        print(f"Updated Customer: {cust.name} (Code: {cust.customer_code}, Limit: {cust.credit_limit})")

# Configure Vendor Al-Hamami
vendor = env['res.partner'].search([('name', 'ilike', 'Al-Hamami')], limit=1)
if vendor:
    vendor.write({
        'supplier_rank': 1,
        'customer_code': 'VEND-001',
        'email': 'sales@alhamami.com',
        'phone': '+966506789012',
    })
    print(f"Configured Vendor: {vendor.name}")

# Reordering Rule: Samsung Galaxy S26 (min 10, max 50)
samsung_tmpl = env['product.template'].search([('name', 'ilike', 'Samsung Galaxy')], limit=1)
if samsung_tmpl:
    product = samsung_tmpl.product_variant_ids[:1]
    if product:
        rule = env['stock.warehouse.orderpoint'].search([('product_id', '=', product.id)], limit=1)
        if not rule:
            rule = env['stock.warehouse.orderpoint'].create({
                'name': f'RR/{product.name}',
                'product_id': product.id,
                'location_id': stock_loc.id,
                'product_min_qty': 10.0,
                'product_max_qty': 50.0,
            })
            print(f"Created Reordering Rule: {rule.name} for {product.display_name} (Min: 10, Max: 50)")
        else:
            rule.write({
                'product_min_qty': 10.0,
                'product_max_qty': 50.0,
            })
            print(f"Updated Reordering Rule: {rule.name}")

env.cr.commit()
print("CONFIGURATION COMPLETED!")
