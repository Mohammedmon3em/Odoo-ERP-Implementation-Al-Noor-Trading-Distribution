import logging
from odoo.exceptions import UserError

_logger = logging.getLogger('alnoor.test')

print("="*60)
print("AL NOOR TRADING & DISTRIBUTION - ACCEPTANCE TEST SUITE")
print("="*60)

test_results = {}

# Setup test prerequisites
admin_user = env.ref('base.user_admin')
sal_user = env['res.users'].search([('login', '=', 'salUser')], limit=1)
sal_manager = env['res.users'].search([('login', '=', 'SalManager')], limit=1)
pur_user = env['res.users'].search([('login', '=', 'PurUser')], limit=1)
wh_user = env['res.users'].search([('login', '=', 'WHUser')], limit=1)
acc_user = env['res.users'].search([('login', '=', 'AccUser')], limit=1)

laptop_prod = env['product.product'].search([('name', 'ilike', 'Dell Latitude')], limit=1)
router_prod = env['product.product'].search([('name', 'ilike', 'TP-Link')], limit=1)
vendor = env['res.partner'].search([('name', 'ilike', 'Al-Hamami')], limit=1)

# -------------------------------------------------------------
# TC-001: Create Customer
# -------------------------------------------------------------
try:
    cust1 = env['res.partner'].create({
        'name': 'TC001 Retail Customer',
        'customer_code': 'CUST-TC001',
        'customer_type': 'retail',
        'credit_limit': 25000.0,
        'use_partner_credit_limit': True,
        'email': 'tc001@example.com',
        'phone': '+966550000001',
    })
    assert cust1.id and cust1.customer_code == 'CUST-TC001' and cust1.customer_type == 'retail'
    test_results['TC-001: Customer Creation'] = 'PASS'
    print("[PASS] TC-001: Customer created successfully.")
except Exception as e:
    test_results['TC-001: Customer Creation'] = f'FAIL: {e}'
    print(f"[FAIL] TC-001: {e}")

# -------------------------------------------------------------
# TC-002: Quotation Under Credit Limit Confirmation
# -------------------------------------------------------------
try:
    so_under = env['sale.order'].create({
        'partner_id': cust1.id,
        'user_id': sal_user.id if sal_user else admin_user.id,
        'order_line': [(0, 0, {
            'product_id': laptop_prod.id,
            'product_uom_qty': 2.0, # 2 * 4500 = 9000 SAR <= 25000 Limit
            'price_unit': 4500.0,
        })],
    })
    assert not so_under.is_credit_limit_exceeded
    so_under.action_confirm()
    assert so_under.state == 'sale'
    test_results['TC-002: Order Under Credit Limit'] = 'PASS'
    print("[PASS] TC-002: Quotation under credit limit confirmed directly.")
except Exception as e:
    test_results['TC-002: Order Under Credit Limit'] = f'FAIL: {e}'
    print(f"[FAIL] TC-002: {e}")

# -------------------------------------------------------------
# TC-003: Order Exceeding Credit Limit Blocks Confirmation
# -------------------------------------------------------------
try:
    so_over = env['sale.order'].create({
        'partner_id': cust1.id,
        'user_id': sal_user.id if sal_user else admin_user.id,
        'order_line': [(0, 0, {
            'product_id': laptop_prod.id,
            'product_uom_qty': 10.0, # 10 * 4500 = 45000 SAR > 25000 Limit
            'price_unit': 4500.0,
        })],
    })
    assert so_over.is_credit_limit_exceeded
    blocked = False
    try:
        so_over.action_confirm()
    except UserError as ue:
        blocked = True
    assert blocked and so_over.approval_status == 'pending'
    test_results['TC-003: Over Credit Limit Blocked & Set Pending'] = 'PASS'
    print("[PASS] TC-003: Over credit limit order blocked from confirmation and set to Pending.")
except Exception as e:
    test_results['TC-003: Over Credit Limit Blocked & Set Pending'] = f'FAIL: {e}'
    print(f"[FAIL] TC-003: {e}")

# -------------------------------------------------------------
# TC-004: Salesperson cannot approve order (BR-102 & BR-103)
# -------------------------------------------------------------
try:
    denied = False
    try:
        so_over.with_user(sal_user).action_approve_credit_limit()
    except UserError:
        denied = True
    assert denied
    test_results['TC-004: Salesperson Cannot Approve (Access Denied)'] = 'PASS'
    print("[PASS] TC-004: Salesperson attempting to approve order correctly raises Access Denied.")
except Exception as e:
    test_results['TC-004: Salesperson Cannot Approve (Access Denied)'] = f'FAIL: {e}'
    print(f"[FAIL] TC-004: {e}")

# -------------------------------------------------------------
# TC-005: Sales Manager Approves Order
# -------------------------------------------------------------
try:
    so_over.with_user(sal_manager).action_approve_credit_limit()
    assert so_over.approval_status == 'approved'
    assert so_over.approved_by_id.id == sal_manager.id
    assert so_over.approval_date
    # Now order can be confirmed!
    so_over.action_confirm()
    assert so_over.state == 'sale'
    test_results['TC-005: Sales Manager Approval & Confirmation'] = 'PASS'
    print("[PASS] TC-005: Sales Manager approved order and order confirmed successfully.")
except Exception as e:
    test_results['TC-005: Sales Manager Approval & Confirmation'] = f'FAIL: {e}'
    print(f"[FAIL] TC-005: {e}")

# -------------------------------------------------------------
# TC-006: Manager Rejection Requires Reason (BR-104 & BR-107)
# -------------------------------------------------------------
try:
    so_reject = env['sale.order'].create({
        'partner_id': cust1.id,
        'user_id': sal_user.id if sal_user else admin_user.id,
        'order_line': [(0, 0, {
            'product_id': laptop_prod.id,
            'product_uom_qty': 15.0, # 15 * 4500 = 67500 SAR
            'price_unit': 4500.0,
        })],
    })
    so_reject.action_request_approval()
    assert so_reject.approval_status == 'pending'

    # Try reject without reason -> should fail
    wizard_empty = env['sale.order.reject.wizard'].with_user(sal_manager).create({
        'order_id': so_reject.id,
        'rejection_reason': '   ',
    })
    no_reason_blocked = False
    try:
        wizard_empty.action_confirm_rejection()
    except UserError:
        no_reason_blocked = True
    assert no_reason_blocked

    # Reject with valid reason
    wizard = env['sale.order.reject.wizard'].with_user(sal_manager).create({
        'order_id': so_reject.id,
        'rejection_reason': 'Customer credit score too low for 67,500 SAR order.',
    })
    wizard.action_confirm_rejection()
    assert so_reject.approval_status == 'rejected'
    assert so_reject.rejected_by_id.id == sal_manager.id
    assert 'credit score' in so_reject.rejection_reason

    # Trying to confirm rejected order must fail (BR-104)
    confirm_rejected_blocked = False
    try:
        so_reject.action_confirm()
    except UserError:
        confirm_rejected_blocked = True
    assert confirm_rejected_blocked

    test_results['TC-006: Rejection Mandatory Reason & Lock'] = 'PASS'
    print("[PASS] TC-006: Order rejection requires reason and permanently blocks confirmation until resubmitted.")
except Exception as e:
    test_results['TC-006: Rejection Mandatory Reason & Lock'] = f'FAIL: {e}'
    print(f"[FAIL] TC-006: {e}")

# -------------------------------------------------------------
# TC-007: Purchase Order & Receipt Generation
# -------------------------------------------------------------
try:
    po = env['purchase.order'].create({
        'partner_id': vendor.id,
        'user_id': pur_user.id if pur_user else admin_user.id,
        'order_line': [(0, 0, {
            'product_id': router_prod.id,
            'product_qty': 25.0,
            'price_unit': 240.0,
        })],
    })
    po.button_confirm()
    assert po.state == 'purchase'
    assert len(po.picking_ids) >= 1
    test_results['TC-007: Purchase Order & Receipt Creation'] = 'PASS'
    print("[PASS] TC-007: Purchase Order confirmed and Receipt operation created.")
except Exception as e:
    test_results['TC-007: Purchase Order & Receipt Creation'] = f'FAIL: {e}'
    print(f"[FAIL] TC-007: {e}")

# -------------------------------------------------------------
# TC-008: Receive Products (Stock In)
# -------------------------------------------------------------
try:
    initial_stock = router_prod.qty_available
    receipt = po.picking_ids[0]
    # Set quantities done
    for move in receipt.move_ids:
        move.quantity = move.product_uom_qty
    receipt.button_validate()
    assert receipt.state == 'done'
    router_prod.invalidate_recordset(['qty_available'])
    assert router_prod.qty_available == initial_stock + 25.0
    test_results['TC-008: Stock Receipt Validation'] = 'PASS'
    print(f"[PASS] TC-008: Receipt validated. Stock increased from {initial_stock} to {router_prod.qty_available}.")
except Exception as e:
    test_results['TC-008: Stock Receipt Validation'] = f'FAIL: {e}'
    print(f"[FAIL] TC-008: {e}")

# -------------------------------------------------------------
# TC-009: Deliver Products (Stock Out)
# -------------------------------------------------------------
try:
    # Use router_prod which has 25 units received in TC-008
    router_initial = router_prod.qty_available
    so_deliver = env['sale.order'].create({
        'partner_id': cust1.id,
        'order_line': [(0, 0, {
            'product_id': router_prod.id,
            'product_uom_qty': 5.0, # 5 * 350 = 1750 <= 25000 Limit
            'price_unit': 350.0,
        })],
    })
    so_deliver.action_confirm()
    delivery = so_deliver.picking_ids[0]
    for move in delivery.move_ids:
        move.quantity = 5.0
    delivery.with_context(skip_sms=True).button_validate()
    assert delivery.state == 'done'
    router_prod.invalidate_recordset(['qty_available'])
    assert router_prod.qty_available == router_initial - 5.0
    test_results['TC-009: Delivery Order Validation'] = 'PASS'
    print(f"[PASS] TC-009: Delivery validated. Stock decreased from {router_initial} to {router_prod.qty_available}.")
except Exception as e:
    test_results['TC-009: Delivery Order Validation'] = f'FAIL: {e}'
    print(f"[FAIL] TC-009: {e}")

# -------------------------------------------------------------
# TC-010: Customer Invoice Linked to Sales Order
# -------------------------------------------------------------
try:
    inv = so_under._create_invoices()
    assert inv and inv.move_type == 'out_invoice'
    assert inv.id in so_under.invoice_ids.ids
    assert inv.amount_total > 0
    test_results['TC-010: Customer Invoice Generation'] = 'PASS'
    print(f"[PASS] TC-010: Invoice {inv.name or inv.id} generated and linked to Sales Order {so_under.name}.")
except Exception as e:
    test_results['TC-010: Customer Invoice Generation'] = f'FAIL: {e}'
    print(f"[FAIL] TC-010: {e}")

env.cr.commit()

print("\n" + "="*60)
print("TEST SUMMARY REPORT:")
print("="*60)
all_passed = True
for tc, res in test_results.items():
    print(f"{tc:.<50} {res}")
    if res != 'PASS':
        all_passed = False

if all_passed:
    print("\nALL 10 TEST CASES PASSED WITH 100% SUCCESS!")
else:
    print("\nSOME TESTS FAILED - SEE DETAILS ABOVE.")
print("="*60)
