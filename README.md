# Inter-counting Desktop ERP & Accounting Application

A modern white and charcoal-themed ERP and accounting system built with Python, Tkinter (using the `clam` theme), and SQLite/MS SQL Server. Designed for managing customers, inventory, sales workflows (Quotations, Sales Orders, Invoices), expenses, email communication, and user roles with fine-grained permissions.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: Make sure Python 3.8+ is installed.
- **System Requirements**: Tkinter support (included in standard Python installations on Windows).

### 2. Setup Virtual Environment & Dependencies
Initialize and activate the virtual environment, then install the packages listed in [requirements.txt](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/requirements.txt):
```powershell
# Create venv if not already created
python -m venv .venv

# Activate venv
.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Run the Application
Execute the app using the virtual environment's Python interpreter:
```powershell
.venv\Scripts\python.exe main.py
```

### 4. Default Login Credentials
Upon the first initialization, the database is auto-seeded with a default admin user:
- **Username**: `admin`
- **Password**: `admin`

---

## 🛠 Features

### 📈 Visual Dashboard
- Renders summary tiles for Total Revenue, Total Paid/Unpaid Invoices, Expenses, and Net Profit.
- Interactive Matplotlib charts for sales trends and expense breakdown.
- Automatically highlights inventory warning alerts for low-stock products.
- View in [dashboard.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/dashboard.py).

### 🗄 Multi-Database Profiles
- Support for both **SQLite** and **Microsoft SQL Server (pyodbc)** database connections.
- Set database profiles dynamically inside the app UI or manually edit [config.ini](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/config.ini).
- Schema auto-initialization (tables like `customers`, `products`, `invoices`, etc.).
- View connection handling in [database.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/database.py).

### 👥 Customer & Product Management
- Complete CRUD operations for customers and products.
- CSV Import/Export feature for bulk customer and inventory updates.
- View implementations in [customer_management.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/customer_management.py) and [product_management.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/product_management.py).

### 📑 Sales Lifecycle
- **Quotations**: Create and print quotes, send to customers via email, track expiry dates. View in [quotation_creation.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/quotation_creation.py).
- **Sales Orders**: Draft and approve sales orders before fulfillment. View in [sales_order_creation.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/sales_order_creation.py).
- **Invoices**: Generate high-quality PDFs containing VAT calculations (defined in settings), and register payments (Paid, Unpaid, Partial status). View in [invoice_creation.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/invoice_creation.py).
- **Listing & PDF Utilities**: Use ReportLab to generate official PDFs. View in [document_listing.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/document_listing.py) and [pdf_service.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/pdf_service.py).

### 📦 Inventory & Stock Management
- Track quantity-in-stock, process supplier purchase orders, and record manual stock adjustments.
- View in [inventory_management.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/inventory_management.py).

### ✉️ Communication & Email Templates
- Integration with an SMTP server (Office 365 default setup in `config.ini`).
- Templates for invoice and quotation distribution.
- Set custom HTML email signatures with images.
- View in [email_service.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/email_service.py) and [communication_window.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/communication_window.py).

### ⚙️ Automation Settings
- Define automation rules (e.g. email customers automatically when invoices are generated).
- View in [automation_service.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/automation_service.py) and [automation_window.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/automation_window.py).

### 🔒 Security, Audit & Admin Utilities
- **Password Protection**: Hashed passwords using bcrypt.
- **Audit Logging**: Tracks all user activities (logins, invoice generation, customer modifications). View in [audit_trail_window.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/audit_trail_window.py).
- **User Permissions**: Fine-grained access control (e.g. `create_invoices`, `manage_expenses`, `view_reports`). View in [user_management.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/user_management.py).
- **Backup & Restore**: Easily backup SQLite databases. View in [backup_restore_window.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/backup_restore_window.py).

---

## 📂 Project Architecture

Key files inside the workspace:
* **[main.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/main.py)**: The central application window and sidebar routing logic.
* **[login.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/login.py)**: Setup database profile selection and authenticate user.
* **[database.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/database.py)**: Database connections and schema definition.
* **[config.ini](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/config.ini)**: Application configurations, SMTP settings, PDF headers, and tax/VAT values.
* **[theme.py](file:///c:/Users/Liam/IdeaProjects/new%20sage%20app/theme.py)**: Clam theme config overrides for high-contrast white and charcoal colors.
