from odoo.exceptions import UserError

print("="*60)
print("TESTING PURCHASE ORDER >= 50,000 SAR APPROVAL WORKFLOW")
print("="*60)

pur_user = env['res.users'].search([('login', '=', 'PurUser')], limit=1)
pur_manager = env['res.users'].search([('login', '=', 'PurManager')], limit=1)
vendor = env['res.partner'].search([('supplier_rank', '>', 0)], limit=1) or env['res.partner'].search([('name', 'ilike', 'Al-Hamami')], limit=1)
laptop_prod = env['product.product'].search([('name', 'ilike', 'Dell Latitude')], limit=1)
router_prod = env['product.product'].search([('name', 'ilike', 'TP-Link')], limit=1)

assert pur_user, "PurUser must exist"
assert pur_manager, "PurManager must exist"
assert vendor, "Vendor must exist"

# 1. Under 50k SAR created and confirmed by PurUser
print("\n--- Test 1: PO under 50,000 SAR by Purchase Officer ---")
po_under = env['purchase.order'].with_user(pur_user).create({
    'partner_id': vendor.id,
    'order_line': [(0, 0, {
        'product_id': router_prod.id,
        'product_qty': 10.0,
        'price_unit': 240.0, # Total: 2,400 SAR < 50,000 SAR
    })],
})
print(f"PO {po_under.name} created. Total: {po_under.amount_total:,.2f} SAR. is_high_value_po: {po_under.is_high_value_po}")
assert not po_under.is_high_value_po
po_under.with_user(pur_user).button_confirm()
print(f"PO {po_under.name} state after PurUser confirm: {po_under.state}")
assert po_under.state == 'purchase', "Order under 50k should be confirmed directly"
print("[PASS] Test 1: PO under 50k confirmed directly by Purchase Officer.")

# 2. >= 50k SAR created by PurUser and confirmed by PurUser -> must be blocked and set to 'to approve'
print("\n--- Test 2: PO >= 50,000 SAR by Purchase Officer blocked & set to approve ---")
po_over = env['purchase.order'].with_user(pur_user).create({
    'partner_id': vendor.id,
    'order_line': [(0, 0, {
        'product_id': laptop_prod.id,
        'product_qty': 20.0,
        'price_unit': 3800.0, # Total: 76,000 SAR >= 50,000 SAR
    })],
})
print(f"PO {po_over.name} created. Total: {po_over.amount_total:,.2f} SAR. is_high_value_po: {po_over.is_high_value_po}")
assert po_over.is_high_value_po

blocked = False
try:
    po_over.with_user(pur_user).button_confirm()
except UserError as ue:
    blocked = True
    print(f"Expected UserError caught: {ue}")

print(f"PO {po_over.name} state: {po_over.state}")
assert blocked, "Purchase officer must be blocked from directly confirming high-value PO"
assert po_over.state == 'to approve', "Order must be in 'to approve' state"
print("[PASS] Test 2: High-value PO blocked and placed in 'to approve' state.")

# 3. PurUser attempts to approve the order -> must fail with Access Denied
print("\n--- Test 3: Purchase Officer cannot approve high-value PO ---")
pur_user_approved = False
try:
    po_over.with_user(pur_user).button_approve()
except UserError as ue:
    print(f"Expected Access Denied caught: {ue}")
    pur_user_approved = False
else:
    pur_user_approved = True

assert not pur_user_approved, "PurUser must NOT be allowed to approve"
assert po_over.state == 'to approve'
print("[PASS] Test 3: Purchase Officer cannot approve high-value PO.")

# 4. Purchase Manager approves the order -> succeeds and moves to 'purchase'
print("\n--- Test 4: Purchase Manager approves high-value PO ---")
po_over.with_user(pur_manager).button_approve()
print(f"PO {po_over.name} state after PurManager approve: {po_over.state}")
assert po_over.state == 'purchase', "Order must be confirmed into 'purchase' state"
print("[PASS] Test 4: Purchase Manager successfully approved the order.")

# 5. Purchase Manager creates and confirms high-value PO directly -> succeeds directly
print("\n--- Test 5: Purchase Manager confirms high-value PO directly ---")
po_mgr_direct = env['purchase.order'].with_user(pur_manager).create({
    'partner_id': vendor.id,
    'order_line': [(0, 0, {
        'product_id': laptop_prod.id,
        'product_qty': 15.0,
        'price_unit': 3800.0, # Total: 57,000 SAR >= 50,000 SAR
    })],
})
print(f"PO {po_mgr_direct.name} created by Manager. Total: {po_mgr_direct.amount_total:,.2f} SAR")
po_mgr_direct.with_user(pur_manager).button_confirm()
print(f"PO {po_mgr_direct.name} state after Manager confirm: {po_mgr_direct.state}")
assert po_mgr_direct.state == 'purchase', "Manager must be able to confirm directly"
print("[PASS] Test 5: Purchase Manager confirmed high-value PO directly.")

env.cr.commit()
print("\n" + "="*60)
print("ALL PURCHASE ORDER APPROVAL TESTS PASSED (100% SUCCESS)!")
print("="*60)
