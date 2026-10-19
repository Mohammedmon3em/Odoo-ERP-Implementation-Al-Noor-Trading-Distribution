# Al Noor Trading & Distribution — Odoo 19 ERP Implementation

Comprehensive enterprise ERP implementation for **Al Noor Trading & Distribution** built on **Odoo 19.0 Community/Enterprise**, featuring custom business logic for sales credit limits, high-value procurement approvals, warehouse logistics, and role-based access control.

---

## 1. Company Profile & Business Scope

- **Company Name**: Al Noor Trading & Distribution (*شركة النور للتجارة والتوزيع*)
- **Industry**: Wholesale and retail distribution of consumer electronics, enterprise IT equipment, and mobile accessories.
- **Product Lines**:
  - Laptops 
  - Smartphones 
  - Monitors
  - Computer Accessories 
  - Networking Equipment 
- **Currency**: Saudi Riyal (`SAR`)
- **Active Database**: `odoo19_ver_1`
- **Default Port**: `8070` ([http://localhost:8070](http://localhost:8070))

---

## 2. Directory Structure

```text
odoo_project/
│
├── custom_addons/
│   └── alnoor_custom/                 # Custom Odoo 19 Module for Al Noor Trading
│       ├── data/
│       │   └── payment_term_data.xml  # Payment terms (Immediate, Net 15, Net 30, Net 60)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── res_partner.py         # Customer Code, Customer Type, Credit Limits
│       │   ├── sale_order.py          # Sales Credit Limit & Approval Workflow (BR-101..108)
│       │   └── purchase_order.py      # PO Approval for orders >= 50,000 SAR
│       ├── security/
│       │   ├── security.xml           # Credit Limit Approver Group definition
│       │   └── ir.model.access.csv    # Access rights for wizards and models
│       ├── views/
│       │   ├── res_partner_views.xml  # Customer classification and filtering views
│       │   ├── sale_order_views.xml   # Approval alerts, buttons, audit trail tab, filters
│       │   └── purchase_order_views.xml # High-value alerts, badges, and filters
│       ├── wizard/
│       │   ├── __init__.py
│       │   ├── sale_order_reject_wizard.py       # Mandatory rejection reason wizard
│       │   └── sale_order_reject_wizard_views.xml # Wizard form dialog
│       ├── __init__.py
│       └── __manifest__.py            # Module manifest and dependencies
│
├── sample_import_data/                # Sample CSV templates for data migration
│   ├── customers.csv                  # Customer master data with types and credit limits
│   ├── products.csv                   # Catalog with internal refs, barcodes, prices, weights
│   ├── vendors.csv                    # Approved vendor master data
│   └── opening_stock.csv              # Initial inventory counts and locations
│
├── screenshots/                       # Application UI screenshots and visual proof
│   ├── 01_login_screen.png            # Odoo 19 Login Screen
│   ├── 02_quotations_list.png         # Sales Quotations & Credit Limit Approval Badges
│   ├── 03_sales_order_form.png        # Sales Order Form & Credit Limit Warning / Approval
│   ├── 04_purchase_orders_list.png    # Purchase Orders & RFQ List View
│   ├── 05_purchase_order_form.png     # High-Value Purchase Order Approval Workflow
│   ├── 06_contacts_list.png           # Classified Customers & Contacts
│   ├── 07_customer_form.png           # Customer Code, Type & Credit Limit Form
│   └── 08_inventory_overview.png      # Al Noor Warehouse Operations Dashboard
│
├── odoo/                              # Odoo 19 Core Engine Source Code
├── venv/                              # Python 3.12 Virtual Environment
├── odoo.conf                          # Server configuration file
├── run_alnoor_test_cases.py           # Acceptance test runner (TC-001 to TC-010)
├── test_po_approval.py                # Purchase Order >= 50,000 SAR test runner
└── README.md                          # Project documentation
```

---

## 3. Key Custom Workflows & Business Rules

### 3.1 Sales Credit Limit Approval Workflow (`alnoor_custom`)
Implements strict credit controls on all sales quotations to prevent unauthorized financial exposure:

1. **Credit Exposure Check**:
   $$\text{Total Exposure} = \text{Current Customer Receivable} + \text{Order Total}$$
   If $\text{Total Exposure} > \text{Customer Credit Limit}$ (and limit $> 0$):
   - The system flags the order as **Credit Limit Exceeded**.
   - Salesperson **cannot** confirm the order directly.
2. **Approval Statuses**:
   - `Not Required`: Order is within credit limit.
   - `Waiting for Approval`: Order exceeds credit limit and is awaiting manager action.
   - `Approved`: Approved by Sales Manager or General Manager.
   - `Rejected`: Rejected with mandatory reason; cannot be confirmed until re-submitted.
3. **Business Rules**:
   - **BR-101**: Order cannot be confirmed without manager approval if credit limit is exceeded.
   - **BR-102**: Salesperson cannot approve their own order.
   - **BR-103**: Only members of *Credit Limit Approver* group (`SalManager` or `GenManager`) can approve or reject.
   - **BR-104**: Rejected orders cannot be confirmed until re-submitted.
   - **BR-105 & BR-106**: Approving user and timestamp are permanently recorded in the audit trail.
   - **BR-107**: Rejection requires a mandatory reason captured via modal wizard and logged to chatter.
   - **BR-108**: Deliveries are only created for confirmed sales orders.

### 3.2 High-Value Purchase Order Approval ($\ge 50,000\text{ SAR}$)
Implements dual-tier procurement validation:
- **Orders $< 50,000\text{ SAR}$**: Purchase Officer (`PurUser`) can confirm directly into a Purchase Order.
- **Orders $\ge 50,000\text{ SAR}$**:
  - Purchase Officer confirming the order causes the order to enter the `to approve` (*Waiting for Approval*) state.
  - An alert banner is displayed on the purchase order form.
  - **Only** the **Purchase Manager** (`PurManager`) or General Manager (`GenManager`) can approve and confirm the order.
  - Non-managers attempting to approve receive an immediate `Access Denied` error.

---

## 4. Product Catalog & Variant Structure

- **Category Hierarchy**:
  ```text
  All
  └── Electronics
      ├── Laptops
      ├── SmartPhones
      ├── Monitors
      ├── Accessories
      └── Networking
  ```
- **Demo Products**:
  | Product Name | Category | Sales Price | Variants / Attributes |
  | :--- | :--- | :--- | :--- |
  | **Dell Latitude 5550** | Laptops | 4,500 SAR | Color: Black, Silver (2 variants) |
  | **HP ProBook 450** | Laptops | 3,800 SAR | Color: Black, Silver (2 variants) |
  | **Samsung Galaxy S26** | SmartPhones | 3,200 SAR | Color: Black, Silver (2 variants) |
  | **LG 27" Monitor** | Monitors | 1,250 SAR | Size (55, 60, 65) × Screen (LED, OLED, AMOLED) (9 variants) |
  | **Logitech Keyboard** | Accessories | 180 SAR | Connection: Wired, Wireless (2 variants) |
  | **TP-Link Router** | Networking | 350 SAR | Standard (1 variant) |

---

## 5. Warehouse & Logistics Architecture

- **Main Warehouse**: `Al Noor Main Warehouse` (Code: `WH`)
- **Key Locations**:
  - `WH/Input`: Inbound receipt staging area.
  - `WH/Stock`: Primary storage location.
  - `WH/Output`: Outbound packing and delivery staging area.
  - `WH/Returns`: Customer and vendor returns location.
- **Picking Types**: Receipts (`IN`), Deliveries (`OUT`), Internal Transfers (`INT`), Pick (`PICK`), Pack (`PACK`), Quality Control (`QC`), Store (`STOR`), Cross-Dock (`XD`).
- **Automated Replenishment**: Reordering rule configured on Samsung Galaxy S26 (`Min: 10`, `Max: 50` units).

---

## 6. User Roles & RBAC (Role-Based Access Control)

| Login | User Name | Department / Role | System Permissions |
| :--- | :--- | :--- | :--- |
| `salUser` | Salesperson | Sales | CRM & Sales User. Own documents only. Cannot approve credit limit exceptions. |
| `SalManager` | Sales Manager | Sales | Sales Administrator & Credit Limit Approver. Full sales pipeline access. |
| `PurUser` | Purchase Officer | Procurement | Purchase User. Can create RFQs and confirm POs $< 50,000\text{ SAR}$. |
| `PurManager` | Purchase Manager | Procurement | Purchase Administrator. Can approve high-value POs $\ge 50,000\text{ SAR}$. |
| `WHUser` | Warehouse User | Inventory | Inventory User. Validates receipts, deliveries, and internal transfers. |
| `AccUser` | Accountant | Finance | Invoicing User. Manages customer invoices and vendor bills. |
| `AccManger` | Accountant Manager | Finance | Accounting Administrator. Full access to chart of accounts and taxes. |
| `GenManager` | General Manager | Executive | Cross-departmental manager with credit approval and reporting rights. |
| `admin` | Administrator | IT / System | Full superuser access to technical settings and configuration. |

---

## 7. Automated Acceptance Test Suites

### 7.1 General Business Flow Tests (`run_alnoor_test_cases.py`)
Run with:
```powershell
Get-Content "run_alnoor_test_cases.py" | & "C:\Odoo\venv\Scripts\python.exe" "odoo\odoo-bin" shell -c "odoo.conf" -d odoo19_ver_1 --no-http
```
Results:
- **TC-001**: Customer Creation with Code & Credit Limit $\rightarrow$ **PASS**
- **TC-002**: Quotation Under Credit Limit Direct Confirmation $\rightarrow$ **PASS**
- **TC-003**: Over Credit Limit Order Blocked & Set to Pending $\rightarrow$ **PASS**
- **TC-004**: Salesperson Cannot Approve (Access Denied) $\rightarrow$ **PASS**
- **TC-005**: Sales Manager Approval & Confirmation $\rightarrow$ **PASS**
- **TC-006**: Rejection Requires Reason & Blocks Confirmation $\rightarrow$ **PASS**
- **TC-007**: Purchase Order Confirmation & Receipt Creation $\rightarrow$ **PASS**
- **TC-008**: Warehouse Stock Receipt Invalidation $\rightarrow$ **PASS**
- **TC-009**: Warehouse Delivery Order Validation $\rightarrow$ **PASS**
- **TC-010**: Customer Invoice Creation Linked to Sales Order $\rightarrow$ **PASS**

### 7.2 Purchase High-Value Tests (`test_po_approval.py`)
Run with:
```powershell
Get-Content "test_po_approval.py" | & "C:\Odoo\venv\Scripts\python.exe" "odoo\odoo-bin" shell -c "odoo.conf" -d odoo19_ver_1 --no-http
```
Results:
- **Test 1**: PO $< 50,000\text{ SAR}$ confirmed directly by Purchase Officer $\rightarrow$ **PASS**
- **Test 2**: PO $\ge 50,000\text{ SAR}$ by Purchase Officer blocked and moved to `to approve` $\rightarrow$ **PASS**
- **Test 3**: Purchase Officer cannot approve high-value PO (Access Denied) $\rightarrow$ **PASS**
- **Test 4**: Purchase Manager approves high-value PO $\rightarrow$ **PASS**
- **Test 5**: Purchase Manager confirms high-value PO directly $\rightarrow$ **PASS**

---

## 8. How to Run the Project

### Prerequisites
- Python 3.12 (virtual environment at `C:\Odoo\venv` or `venv\`)
- PostgreSQL 18 running on port `5433` (User: `odoo`, Password: `openpgpwd`)

### Starting the Server
Open PowerShell in the project directory and run:
```powershell
& "C:\Odoo\venv\Scripts\python.exe" "odoo\odoo-bin" -c "odoo.conf"
```
Or start as a background daemon process:
```powershell
Start-Process -FilePath "C:\Odoo\venv\Scripts\python.exe" -ArgumentList '"odoo\odoo-bin"', '-c', '"odoo.conf"' -NoNewWindow
```

### Accessing the System
- **Web URL**: [http://localhost:8070](http://localhost:8070)
- **Database**: `odoo19_ver_1`
- **User Logins**:
  - Administrator: `admin` / `admin`
  - Sales Manager (Approver): `SalManager` / `SalManager` (or `admin`)
  - Salesperson: `salUser` / `salUser`
  - Purchase Manager: `PurManager` / `PurManager`
  - Purchase Officer: `PurUser` / `PurUser`
  - Warehouse Officer: `WHUser` / `WHUser`
  - Accountant: `AccUser` / `AccUser`
  - General Manager: `GenManager` / `GenManager`

### Upgrading the Custom Addon
Whenever you make updates to the `alnoor_custom` module:
```powershell
& "C:\Odoo\venv\Scripts\python.exe" "odoo\odoo-bin" -c "odoo.conf" -d odoo19_ver_1 -u alnoor_custom --stop-after-init
```

---

## 9. Sample Data Migration Templates (`sample_import_data/`)

Pre-formatted CSV templates ready for standard Odoo import wizard:
1. `customers.csv`: Classified customers with customer codes (`CUST-001`..`005`), types (`retail`, `wholesale`, `vip`), and credit limits (SAR 20,000 to 100,000).
2. `products.csv`: Product master list with internal references, barcodes, standard prices, list prices, and weights.
3. `vendors.csv`: Approved suppliers (`Al Safwa Electronics Distribution`).
4. `opening_stock.csv`: Initial inventory opening counts mapped to `WH/Stock`.

---

## 10. Database Backup & Disaster Recovery

A complete clean database dump has been archived:
- **Location**: `odoo19_ver_1_backup_20261019.dump`
- **Restore Command** (PostgreSQL):
  ```powershell
  & "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -h 127.0.0.1 -p 5433 -U odoo -d odoo19_ver_1 -c -v "odoo19_ver_1_backup_20261019.dump"
  ```

---

## 11. Application Screenshots (`screenshots/`)

All key functional screens have been captured directly from the live application and organized in the `screenshots/` directory:

| Screenshot | Description | File Link |
| :--- | :--- | :--- |
| **01. Login Screen** | Odoo 19 clean authentication page for Al Noor Trading & Distribution | [`01_login_screen.png`](screenshots/01_login_screen.png) |
| **02. Sales Quotations List** | Quotations list view displaying the *Credit Limit Approval Status* badge column and filtering | [`02_quotations_list.png`](screenshots/02_quotations_list.png) |
| **03. Sales Order Form View** | Sales order detail form showing *Credit Limit Exceeded* banner, approval action buttons, and audit trail | [`03_sales_order_form.png`](screenshots/03_sales_order_form.png) |
| **04. Purchase Orders List** | Procurement list view with RFQ, Purchase Order, and *To Approve* statuses | [`04_purchase_orders_list.png`](screenshots/04_purchase_orders_list.png) |
| **05. Purchase Order Form View** | High-value purchase order form ($\ge 50,000\text{ SAR}$) showing approval banner and manager workflow | [`05_purchase_order_form.png`](screenshots/05_purchase_order_form.png) |
| **06. Contacts / Customers List** | Customer directory with Retail, Wholesale, and VIP classifications | [`06_contacts_list.png`](screenshots/06_contacts_list.png) |
| **07. Customer Detail Form** | Customer configuration form showing *Customer Code*, *Customer Type*, and *Credit Limit* controls | [`07_customer_form.png`](screenshots/07_customer_form.png) |
| **08. Inventory Overview** | Warehouse operations dashboard showing Receipts, Deliveries, and Internal Transfers for Al Noor Main Warehouse | [`08_inventory_overview.png`](screenshots/08_inventory_overview.png) |


