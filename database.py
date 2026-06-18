import pyodbc
import sqlite3
import bcrypt
import json
import configparser
from datetime import datetime, timedelta

# Global variable to store the current connection string or file path
CURRENT_DB_CONFIG = {}

def get_db_profiles():
    """Reads database profiles from config.ini."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    profiles = {}
    for section in config.sections():
        if section.startswith('DB_'):
            profile_name = section[3:] # Remove 'DB_' prefix
            profiles[profile_name] = dict(config[section])
    return profiles

def set_db_profile(profile_name):
    """Sets the current database configuration based on the profile name."""
    global CURRENT_DB_CONFIG
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    section = f'DB_{profile_name}'
    if config.has_section(section):
        CURRENT_DB_CONFIG = dict(config[section])
        
        # Update last used profile
        if not config.has_section('General'):
            config.add_section('General')
        config['General']['last_profile'] = profile_name
        with open('config.ini', 'w') as f:
            config.write(f)
        return True
    return False

def add_db_profile(name, db_type, server=None, database=None, username=None, password=None, filename=None):
    """Adds a new database profile to config.ini."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    section = f'DB_{name}'
    if not config.has_section(section):
        config.add_section(section)
    
    config[section]['type'] = db_type
    if db_type == 'mssql':
        config[section]['server'] = server
        config[section]['database'] = database
        if username:
            config[section]['username'] = username
        if password:
            config[section]['password'] = password
    elif db_type == 'sqlite':
        config[section]['filename'] = filename
        
    with open('config.ini', 'w') as f:
        config.write(f)

def get_server_databases(server, username=None, password=None):
    """Retrieves a list of databases from the specified SQL Server."""
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
    if username and password:
        conn_str += f"UID={username};PWD={password};"
    else:
        conn_str += "Trusted_Connection=yes;"
        
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
        databases = [row[0] for row in cursor.fetchall()]
        conn.close()
        return databases
    except pyodbc.Error as ex:
        print(f"Failed to list databases: {ex}")
        return []

def connect_db():
    """Establishes a connection to the database based on CURRENT_DB_CONFIG."""
    global CURRENT_DB_CONFIG
    
    # If no config is set, try to load the last used profile
    if not CURRENT_DB_CONFIG:
        config = configparser.ConfigParser()
        config.read('config.ini')
        last_profile = config.get('General', 'last_profile', fallback='SQLite')
        set_db_profile(last_profile)

    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')

    if db_type == 'mssql':
        server = CURRENT_DB_CONFIG.get('server')
        database = CURRENT_DB_CONFIG.get('database')
        username = CURRENT_DB_CONFIG.get('username')
        password = CURRENT_DB_CONFIG.get('password')
        
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};"
        
        if username and password:
            conn_str += f"UID={username};PWD={password};"
        else:
            conn_str += "Trusted_Connection=yes;"

        try:
            conn = pyodbc.connect(conn_str)
            return conn
        except pyodbc.Error as ex:
            print(f"SQL Server connection failed: {ex}")
            raise ex
            
    elif db_type == 'sqlite':
        filename = CURRENT_DB_CONFIG.get('filename', 'intercounting.db')
        try:
            conn = sqlite3.connect(filename)
            return conn
        except sqlite3.Error as ex:
            print(f"SQLite connection failed: {ex}")
            raise ex
            
    else:
        raise ValueError(f"Unknown database type: {db_type}")

def create_tables():
    """Creates necessary tables in the database if they don't exist."""
    conn = connect_db()
    cursor = conn.cursor()
    
    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
    
    # SQL syntax differences
    if db_type == 'sqlite':
        auto_inc = "INTEGER PRIMARY KEY AUTOINCREMENT"
    else:
        auto_inc = "INT PRIMARY KEY IDENTITY(1,1)"

    # Helper to execute SQL safely
    def execute_sql(sql):
        try:
            cursor.execute(sql)
        except Exception as e:
            # Ignore errors if table/column already exists
            pass

    # Customers
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS customers (
                id {auto_inc},
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                customer_code TEXT
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='customers' and xtype='U')
            CREATE TABLE customers (
                id {auto_inc},
                name NVARCHAR(255) NOT NULL,
                email NVARCHAR(255),
                phone NVARCHAR(50),
                address NVARCHAR(MAX),
                customer_code NVARCHAR(50)
            )
        ''')
    
    try:
        if db_type == 'sqlite':
            cursor.execute("ALTER TABLE customers ADD COLUMN customer_code TEXT")
        else:
            cursor.execute("ALTER TABLE customers ADD customer_code NVARCHAR(50)")
    except Exception:
        pass

    # Products
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS products (
                id {auto_inc},
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                quantity_in_stock INTEGER DEFAULT 0,
                item_code TEXT
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='products' and xtype='U')
            CREATE TABLE products (
                id {auto_inc},
                name NVARCHAR(255) NOT NULL,
                description NVARCHAR(MAX),
                price DECIMAL(18, 2) NOT NULL,
                quantity_in_stock INT DEFAULT 0,
                item_code NVARCHAR(50)
            )
        ''')
        
    try:
        if db_type == 'sqlite':
            cursor.execute("ALTER TABLE products ADD COLUMN item_code TEXT")
        else:
            cursor.execute("ALTER TABLE products ADD item_code NVARCHAR(50)")
    except Exception:
        pass
        
    try:
        if db_type == 'sqlite':
            cursor.execute("ALTER TABLE products ADD COLUMN quantity_in_stock INTEGER DEFAULT 0")
        else:
            cursor.execute("ALTER TABLE products ADD quantity_in_stock INT DEFAULT 0")
    except Exception:
        pass

    # Invoices
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS invoices (
                id {auto_inc},
                customer_id INTEGER NOT NULL,
                invoice_date TEXT NOT NULL,
                due_date TEXT,
                total_amount REAL NOT NULL,
                amount_paid REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                status TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoices' and xtype='U')
            CREATE TABLE invoices (
                id {auto_inc},
                customer_id INT NOT NULL,
                invoice_date DATE NOT NULL,
                due_date DATE,
                total_amount DECIMAL(18, 2) NOT NULL,
                amount_paid DECIMAL(18, 2) DEFAULT 0,
                tax_amount DECIMAL(18, 2) DEFAULT 0,
                status NVARCHAR(50) NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
    try:
        if db_type == 'sqlite':
            cursor.execute("ALTER TABLE invoices ADD COLUMN amount_paid REAL DEFAULT 0")
            cursor.execute("ALTER TABLE invoices ADD COLUMN tax_amount REAL DEFAULT 0")
        else:
            cursor.execute("ALTER TABLE invoices ADD amount_paid DECIMAL(18, 2) DEFAULT 0")
            cursor.execute("ALTER TABLE invoices ADD tax_amount DECIMAL(18, 2) DEFAULT 0")
    except Exception:
        pass

    # Invoice Items
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id {auto_inc},
                invoice_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoice_items' and xtype='U')
            CREATE TABLE invoice_items (
                id {auto_inc},
                invoice_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(18, 2) NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

    # Users
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS users (
                id {auto_inc},
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                permissions TEXT
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' and xtype='U')
            CREATE TABLE users (
                id {auto_inc},
                username NVARCHAR(255) NOT NULL UNIQUE,
                password_hash NVARCHAR(255) NOT NULL,
                role NVARCHAR(50) NOT NULL,
                permissions NVARCHAR(MAX)
            )
        ''')

    # Audit Log
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS audit_log (
                id {auto_inc},
                timestamp TEXT NOT NULL,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='audit_log' and xtype='U')
            CREATE TABLE audit_log (
                id {auto_inc},
                timestamp DATETIME NOT NULL,
                user_id INT,
                username NVARCHAR(255),
                action NVARCHAR(MAX) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')

    # Payments
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS payments (
                id {auto_inc},
                invoice_id INTEGER NOT NULL,
                payment_date TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='payments' and xtype='U')
            CREATE TABLE payments (
                id {auto_inc},
                invoice_id INT NOT NULL,
                payment_date DATE NOT NULL,
                amount DECIMAL(18, 2) NOT NULL,
                payment_method NVARCHAR(50),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')

    # Expense Categories
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS expense_categories (
                id {auto_inc},
                name TEXT NOT NULL UNIQUE
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='expense_categories' and xtype='U')
            CREATE TABLE expense_categories (
                id {auto_inc},
                name NVARCHAR(255) NOT NULL UNIQUE
            )
        ''')

    # Expenses
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS expenses (
                id {auto_inc},
                expense_date TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                user_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES expense_categories(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='expenses' and xtype='U')
            CREATE TABLE expenses (
                id {auto_inc},
                expense_date DATE NOT NULL,
                category_id INT NOT NULL,
                amount DECIMAL(18, 2) NOT NULL,
                description NVARCHAR(MAX),
                user_id INT,
                FOREIGN KEY (category_id) REFERENCES expense_categories(id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')

    # Automation Rules
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS automation_rules (
                id {auto_inc},
                name TEXT NOT NULL,
                trigger_event TEXT NOT NULL,
                action_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='automation_rules' and xtype='U')
            CREATE TABLE automation_rules (
                id {auto_inc},
                name NVARCHAR(255) NOT NULL,
                trigger_event NVARCHAR(255) NOT NULL,
                action_type NVARCHAR(255) NOT NULL,
                is_active BIT DEFAULT 1
            )
        ''')

    # Email Signatures
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS email_signatures (
                id {auto_inc},
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                image_path TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='email_signatures' and xtype='U')
            CREATE TABLE email_signatures (
                id {auto_inc},
                name NVARCHAR(255) NOT NULL,
                content NVARCHAR(MAX) NOT NULL,
                image_path NVARCHAR(MAX),
                user_id INT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
        
    try:
        if db_type == 'sqlite':
            cursor.execute("ALTER TABLE email_signatures ADD COLUMN image_path TEXT")
        else:
            cursor.execute("ALTER TABLE email_signatures ADD image_path NVARCHAR(MAX)")
    except Exception:
        pass

    # Quotations
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS quotations (
                id {auto_inc},
                customer_id INTEGER NOT NULL,
                quotation_date TEXT NOT NULL,
                expiry_date TEXT,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS quotation_items (
                id {auto_inc},
                quotation_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (quotation_id) REFERENCES quotations(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='quotations' and xtype='U')
            CREATE TABLE quotations (
                id {auto_inc},
                customer_id INT NOT NULL,
                quotation_date DATE NOT NULL,
                expiry_date DATE,
                total_amount DECIMAL(18, 2) NOT NULL,
                status NVARCHAR(50) NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='quotation_items' and xtype='U')
            CREATE TABLE quotation_items (
                id {auto_inc},
                quotation_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(18, 2) NOT NULL,
                FOREIGN KEY (quotation_id) REFERENCES quotations(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

    # Sales Orders
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS sales_orders (
                id {auto_inc},
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                delivery_date TEXT,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS sales_order_items (
                id {auto_inc},
                sales_order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sales_orders' and xtype='U')
            CREATE TABLE sales_orders (
                id {auto_inc},
                customer_id INT NOT NULL,
                order_date DATE NOT NULL,
                delivery_date DATE,
                total_amount DECIMAL(18, 2) NOT NULL,
                status NVARCHAR(50) NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sales_order_items' and xtype='U')
            CREATE TABLE sales_order_items (
                id {auto_inc},
                sales_order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(18, 2) NOT NULL,
                FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

    # Suppliers
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS suppliers (
                id {auto_inc},
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='suppliers' and xtype='U')
            CREATE TABLE suppliers (
                id {auto_inc},
                name NVARCHAR(255) NOT NULL,
                email NVARCHAR(255),
                phone NVARCHAR(50),
                address NVARCHAR(MAX)
            )
        ''')

    # Purchase Orders
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id {auto_inc},
                supplier_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                expected_date TEXT,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id {auto_inc},
                purchase_order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='purchase_orders' and xtype='U')
            CREATE TABLE purchase_orders (
                id {auto_inc},
                supplier_id INT NOT NULL,
                order_date DATE NOT NULL,
                expected_date DATE,
                total_amount DECIMAL(18, 2) NOT NULL,
                status NVARCHAR(50) NOT NULL,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='purchase_order_items' and xtype='U')
            CREATE TABLE purchase_order_items (
                id {auto_inc},
                purchase_order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_cost DECIMAL(18, 2) NOT NULL,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

    # Stock Adjustments
    if db_type == 'sqlite':
        execute_sql(f'''
            CREATE TABLE IF NOT EXISTS stock_adjustments (
                id {auto_inc},
                product_id INTEGER NOT NULL,
                adjustment_date TEXT NOT NULL,
                quantity_change INTEGER NOT NULL,
                reason TEXT,
                user_id INTEGER,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    else:
        execute_sql(f'''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='stock_adjustments' and xtype='U')
            CREATE TABLE stock_adjustments (
                id {auto_inc},
                product_id INT NOT NULL,
                adjustment_date DATE NOT NULL,
                quantity_change INT NOT NULL,
                reason NVARCHAR(MAX),
                user_id INT,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')

    conn.commit()

    # --- Create Default Admin User ---
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        all_permissions = "manage_customers,manage_products,create_invoices,view_reports,manage_expenses,manage_automation,manage_communication,manage_sales,manage_inventory"
        create_user('admin', 'admin', 'admin', permissions=all_permissions)
        log_action(None, 'admin', 'Application initialized and default admin created.')

    # --- Seed Default Expense Categories ---
    cursor.execute("SELECT COUNT(*) FROM expense_categories")
    if cursor.fetchone()[0] == 0:
        default_categories = ['Rent', 'Utilities', 'Salaries', 'Supplies', 'Marketing', 'Insurance', 'Other']
        for cat in default_categories:
            cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (cat,))
        conn.commit()

    conn.close()

def log_action(user_id, username, action):
    """Records an action in the audit log."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_log (timestamp, user_id, username, action) VALUES (?, ?, ?, ?)",
        (datetime.now(), user_id, username, action)
    )
    conn.commit()
    conn.close()

def get_audit_logs():
    """Retrieves all audit logs, most recent first."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, username, action FROM audit_log ORDER BY timestamp DESC")
    logs = []
    for row in cursor.fetchall():
        logs.append({
            'timestamp': row[0],
            'username': row[1],
            'action': row[2]
        })
    conn.close()
    return logs

def hash_password(password):
    """Hashes a password for storing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(stored_password_hash, provided_password):
    """Verifies a provided password against a stored hash."""
    # SQLite stores strings, so we might need to encode
    if isinstance(stored_password_hash, str):
        stored_password_hash = stored_password_hash.encode('utf-8')
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password_hash)

def create_user(username, password, role, permissions=''):
    """Creates a new user with a hashed password."""
    conn = connect_db()
    cursor = conn.cursor()
    password_hash = hash_password(password).decode('utf-8')
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, permissions) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, permissions)
        )
        conn.commit()
    except Exception: # Catch both pyodbc and sqlite3 errors
        return False
    finally:
        conn.close()
    return True

def authenticate_user(username, password):
    """Authenticates a user and returns their details if successful."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role, permissions FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data and verify_password(user_data[2], password):
        permissions_str = user_data[4] or ''
        user_details = {
            'id': user_data[0],
            'username': user_data[1],
            'role': user_data[3],
            'permissions': permissions_str.split(',') if permissions_str else []
        }
        log_action(user_details['id'], user_details['username'], f"User '{username}' logged in.")
        return user_details
    else:
        log_action(None, username, f"Failed login attempt for user '{username}'.")
        return None

def get_all_users():
    """Retrieves all users from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, permissions FROM users")
    users = []
    for row in cursor.fetchall():
        permissions_str = row[3] or ''
        users.append({
            'id': row[0],
            'username': row[1],
            'role': row[2],
            'permissions': permissions_str.split(',') if permissions_str else []
        })
    conn.close()
    return users

def update_user_permissions(user_id, permissions):
    """Updates the permissions for a specific user."""
    conn = connect_db()
    cursor = conn.cursor()
    permissions_str = ','.join(permissions)
    cursor.execute("UPDATE users SET permissions = ? WHERE id = ?", (permissions_str, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    """Deletes a user from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


# ... (rest of the database functions) ...
def add_customer_to_db(name, email, phone, address, customer_code=''):
    """Adds a new customer to the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (name, email, phone, address, customer_code) VALUES (?, ?, ?, ?, ?)",
                   (name, email, phone, address, customer_code))
    conn.commit()
    conn.close()

def get_all_customers_from_db():
    """Retrieves all customers from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, address, customer_code FROM customers")
    customers = []
    for row in cursor.fetchall():
        customers.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'address': row[4],
            'customer_code': row[5] or ''
        })
    conn.close()
    return customers

def update_customer_in_db(customer_id, name, email, phone, address, customer_code=''):
    """Updates an existing customer in the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET name=?, email=?, phone=?, address=?, customer_code=? WHERE id=?",
                   (name, email, phone, address, customer_code, customer_id))
    conn.commit()
    conn.close()

def delete_customer_from_db(customer_id):
    """Deletes a customer from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.commit()
    conn.close()

def add_product_to_db(name, description, price, quantity_in_stock=0, item_code=''):
    """Adds a new product to the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, description, price, quantity_in_stock, item_code) VALUES (?, ?, ?, ?, ?)",
                   (name, description, price, quantity_in_stock, item_code))
    conn.commit()
    conn.close()

def get_all_products_from_db():
    """Retrieves all products from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price, quantity_in_stock, item_code FROM products")
    products = []
    for row in cursor.fetchall():
        products.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': float(row[3]),
            'quantity_in_stock': row[4],
            'item_code': row[5] or ''
        })
    conn.close()
    return products

def update_product_in_db(product_id, name, description, price, quantity_in_stock, item_code=''):
    """Updates an existing product in the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name=?, description=?, price=?, quantity_in_stock=?, item_code=? WHERE id=?",
                   (name, description, price, quantity_in_stock, item_code, product_id))
    conn.commit()
    conn.close()

def delete_product_from_db(product_id):
    """Deletes a product from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def create_invoice(customer_id, items, status='draft'):
    """Creates a new invoice and its items in the database, deducting stock."""
    conn = connect_db()
    cursor = conn.cursor()
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    tax_rate = float(config.get('Tax', 'rate', fallback='0.0')) / 100

    try:
        # Check stock availability first
        for item in items:
            cursor.execute("SELECT quantity_in_stock, name FROM products WHERE id = ?", (item['product_id'],))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Product ID {item['product_id']} not found.")
            
            current_stock, product_name = result
            if current_stock < item['quantity']:
                raise ValueError(f"Insufficient stock for '{product_name}'. Available: {current_stock}, Requested: {item['quantity']}")

        subtotal = sum(item['quantity'] * item['price'] for item in items)
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        invoice_date = datetime.now().date()
        due_date = invoice_date + timedelta(days=30)

        # Create the invoice record
        db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
        if db_type == 'sqlite':
            cursor.execute(
                "INSERT INTO invoices (customer_id, invoice_date, due_date, total_amount, tax_amount, status) VALUES (?, ?, ?, ?, ?, ?)",
                (customer_id, invoice_date, due_date, total_amount, tax_amount, status)
            )
            invoice_id = cursor.lastrowid
        else:
            cursor.execute(
                "INSERT INTO invoices (customer_id, invoice_date, due_date, total_amount, tax_amount, status) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?)",
                (customer_id, invoice_date, due_date, total_amount, tax_amount, status)
            )
            invoice_id = cursor.fetchone()[0]

        # Create invoice items and deduct stock
        for item in items:
            cursor.execute(
                "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (invoice_id, item['product_id'], item['quantity'], item['price'])
            )
            cursor.execute(
                "UPDATE products SET quantity_in_stock = quantity_in_stock - ? WHERE id = ?",
                (item['quantity'], item['product_id'])
            )

        conn.commit()
        return invoice_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_invoices_with_customer_name():
    """Retrieves all invoices with customer names."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, c.name, i.invoice_date, i.due_date, i.total_amount, i.status
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        ORDER BY i.invoice_date DESC
    """)
    invoices = []
    for row in cursor.fetchall():
        invoices.append({
            'id': row[0],
            'customer_name': row[1],
            'invoice_date': row[2],
            'due_date': row[3],
            'total_amount': float(row[4]),
            'status': row[5]
        })
    conn.close()
    return invoices

def get_invoice_details(invoice_id):
    """Retrieves full details for a single invoice."""
    conn = connect_db()
    cursor = conn.cursor()

    # Get invoice and customer details
    cursor.execute("""
        SELECT i.id, i.invoice_date, i.due_date, i.total_amount, i.amount_paid, i.status,
               c.name, c.email, c.address, c.customer_code, i.tax_amount
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id = ?
    """, (invoice_id,))
    invoice_data = cursor.fetchone()

    if not invoice_data:
        return None

    invoice_details = {
        'id': invoice_data[0],
        'invoice_date': invoice_data[1],
        'due_date': invoice_data[2],
        'total_amount': float(invoice_data[3]),
        'amount_paid': float(invoice_data[4] or 0),
        'status': invoice_data[5],
        'customer_name': invoice_data[6],
        'customer_email': invoice_data[7],
        'customer_address': invoice_data[8],
        'customer_code': invoice_data[9] or '',
        'tax_amount': float(invoice_data[10] or 0),
        'items': [],
        'payments': []
    }

    # Get invoice items
    cursor.execute("""
        SELECT p.name, ii.quantity, ii.unit_price, p.item_code
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        WHERE ii.invoice_id = ?
    """, (invoice_id,))
    for row in cursor.fetchall():
        invoice_details['items'].append({
            'product_name': row[0],
            'quantity': row[1],
            'unit_price': float(row[2]),
            'item_code': row[3] or ''
        })

    # Get payments
    cursor.execute("""
        SELECT payment_date, amount, payment_method
        FROM payments
        WHERE invoice_id = ?
        ORDER BY payment_date DESC
    """, (invoice_id,))
    for row in cursor.fetchall():
        invoice_details['payments'].append({
            'date': row[0],
            'amount': float(row[1]),
            'method': row[2]
        })

    conn.close()
    return invoice_details

def record_payment(invoice_id, amount, method):
    """Records a payment for an invoice."""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Insert payment record
        cursor.execute(
            "INSERT INTO payments (invoice_id, payment_date, amount, payment_method) VALUES (?, ?, ?, ?)",
            (invoice_id, datetime.now().date(), amount, method)
        )
        
        # Update invoice amount_paid and status
        cursor.execute("UPDATE invoices SET amount_paid = amount_paid + ? WHERE id = ?", (amount, invoice_id))
        
        # Check if fully paid
        cursor.execute("SELECT total_amount, amount_paid FROM invoices WHERE id = ?", (invoice_id,))
        total, paid = cursor.fetchone()
        
        new_status = 'Paid' if paid >= total else 'Partial'
        cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error recording payment: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --- Expense Functions ---

def get_expense_categories():
    """Retrieves all expense categories."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM expense_categories")
    categories = []
    for row in cursor.fetchall():
        categories.append({'id': row[0], 'name': row[1]})
    conn.close()
    return categories

def add_expense(date, category_id, amount, description, user_id):
    """Adds a new expense."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (expense_date, category_id, amount, description, user_id) VALUES (?, ?, ?, ?, ?)",
        (date, category_id, amount, description, user_id)
    )
    conn.commit()
    conn.close()

def get_all_expenses():
    """Retrieves all expenses with category names."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.expense_date, c.name, e.amount, e.description, u.username
        FROM expenses e
        JOIN expense_categories c ON e.category_id = c.id
        LEFT JOIN users u ON e.user_id = u.id
        ORDER BY e.expense_date DESC
    """)
    expenses = []
    for row in cursor.fetchall():
        expenses.append({
            'id': row[0],
            'date': row[1],
            'category': row[2],
            'amount': float(row[3]),
            'description': row[4],
            'user': row[5]
        })
    conn.close()
    return expenses

def get_dashboard_metrics():
    """Retrieves key metrics for the dashboard."""
    conn = connect_db()
    cursor = conn.cursor()

    # Total customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    # Total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # Total sales (sum of all invoices)
    cursor.execute("SELECT SUM(total_amount) FROM invoices")
    total_sales = cursor.fetchone()[0] or 0.0

    # Total expenses
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0.0

    # Number of invoices
    cursor.execute("SELECT COUNT(*) FROM invoices")
    invoice_count = cursor.fetchone()[0]

    conn.close()

    net_profit = float(total_sales) - float(total_expenses)

    return {
        'total_customers': total_customers,
        'total_products': total_products,
        'total_sales': float(total_sales),
        'total_expenses': float(total_expenses),
        'net_profit': net_profit,
        'invoice_count': invoice_count
    }

def get_sales_data_for_chart(days=7):
    """Retrieves total sales for each of the last N days."""
    conn = connect_db()
    cursor = conn.cursor()
    
    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
    
    if db_type == 'sqlite':
        query = """
            SELECT
                DATE(invoice_date) as sale_date,
                SUM(total_amount) as daily_sales
            FROM invoices
            WHERE invoice_date >= ?
            GROUP BY DATE(invoice_date)
            ORDER BY sale_date ASC
        """
    else:
        query = """
            SELECT
                CAST(invoice_date AS DATE) as sale_date,
                SUM(total_amount) as daily_sales
            FROM invoices
            WHERE invoice_date >= ?
            GROUP BY CAST(invoice_date AS DATE)
            ORDER BY sale_date ASC
        """
    
    start_date = datetime.now().date() - timedelta(days=days-1)
    cursor.execute(query, (start_date,))
    
    sales_data = { (start_date + timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(days) }

    for row in cursor.fetchall():
        # Handle different date formats/objects from drivers
        if isinstance(row[0], str):
            date_str = row[0]
        else:
            date_str = row[0].strftime('%Y-%m-%d')
            
        sales_data[date_str] = float(row[1])
        
    conn.close()
    return sales_data

def get_recent_invoices(limit=5):
    """Retrieves the most recent invoices."""
    conn = connect_db()
    cursor = conn.cursor()
    
    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
    if db_type == 'sqlite':
        cursor.execute("""
            SELECT i.id, c.name, i.total_amount, i.status
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            ORDER BY i.invoice_date DESC, i.id DESC
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT TOP (?) i.id, c.name, i.total_amount, i.status
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            ORDER BY i.invoice_date DESC, i.id DESC
        """, (limit,))
        
    invoices = []
    for row in cursor.fetchall():
        invoices.append({
            'id': row[0],
            'customer_name': row[1],
            'total_amount': float(row[2]),
            'status': row[3]
        })
    conn.close()
    return invoices

def get_top_products(limit=5):
    """Retrieves the top selling products by quantity."""
    conn = connect_db()
    cursor = conn.cursor()
    
    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
    if db_type == 'sqlite':
        cursor.execute("""
            SELECT p.name, SUM(ii.quantity) as total_sold
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            GROUP BY p.name
            ORDER BY total_sold DESC
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT TOP (?) p.name, SUM(ii.quantity) as total_sold
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            GROUP BY p.name
            ORDER BY total_sold DESC
        """, (limit,))
        
    products = []
    for row in cursor.fetchall():
        products.append({
            'name': row[0],
            'total_sold': row[1]
        })
    conn.close()
    return products

def get_low_stock_products(threshold=10):
    """Retrieves products with stock below the threshold."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, quantity_in_stock FROM products WHERE quantity_in_stock < ?", (threshold,))
    products = []
    for row in cursor.fetchall():
        products.append({
            'name': row[0],
            'quantity': row[1]
        })
    conn.close()
    return products

# --- Automation Functions ---

def get_automation_rules():
    """Retrieves all automation rules."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, trigger_event, action_type, is_active FROM automation_rules")
    rules = []
    for row in cursor.fetchall():
        rules.append({
            'id': row[0],
            'name': row[1],
            'trigger_event': row[2],
            'action_type': row[3],
            'is_active': bool(row[4])
        })
    conn.close()
    return rules

def add_automation_rule(name, trigger_event, action_type):
    """Adds a new automation rule."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO automation_rules (name, trigger_event, action_type, is_active) VALUES (?, ?, ?, 1)",
        (name, trigger_event, action_type)
    )
    conn.commit()
    conn.close()

def delete_automation_rule(rule_id):
    """Deletes an automation rule."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM automation_rules WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()

def toggle_automation_rule(rule_id, is_active):
    """Toggles the active status of an automation rule."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE automation_rules SET is_active = ? WHERE id = ?", (1 if is_active else 0, rule_id))
    conn.commit()
    conn.close()

# --- Email Signature Functions ---

def get_email_signatures(user_id):
    """Retrieves email signatures for a user."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, content, image_path FROM email_signatures WHERE user_id = ?", (user_id,))
    signatures = []
    for row in cursor.fetchall():
        signatures.append({
            'id': row[0],
            'name': row[1],
            'content': row[2],
            'image_path': row[3]
        })
    conn.close()
    return signatures

def add_email_signature(name, content, user_id, image_path=None):
    """Adds a new email signature."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO email_signatures (name, content, user_id, image_path) VALUES (?, ?, ?, ?)",
        (name, content, user_id, image_path)
    )
    conn.commit()
    conn.close()

def delete_email_signature(signature_id):
    """Deletes an email signature."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM email_signatures WHERE id = ?", (signature_id,))
    conn.commit()
    conn.close()

# --- Quotation Functions ---

def create_quotation(customer_id, items):
    """Creates a new quotation."""
    conn = connect_db()
    cursor = conn.cursor()

    total_amount = sum(item['quantity'] * item['price'] for item in items)
    quotation_date = datetime.now().date()
    expiry_date = quotation_date + timedelta(days=14) # Default 14 days expiry

    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
    if db_type == 'sqlite':
        cursor.execute(
            "INSERT INTO quotations (customer_id, quotation_date, expiry_date, total_amount, status) VALUES (?, ?, ?, ?, 'Draft')",
            (customer_id, quotation_date, expiry_date, total_amount)
        )
        quotation_id = cursor.lastrowid
    else:
        cursor.execute(
            "INSERT INTO quotations (customer_id, quotation_date, expiry_date, total_amount, status) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, 'Draft')",
            (customer_id, quotation_date, expiry_date, total_amount)
        )
        quotation_id = cursor.fetchone()[0]

    for item in items:
        cursor.execute(
            "INSERT INTO quotation_items (quotation_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (quotation_id, item['product_id'], item['quantity'], item['price'])
        )

    conn.commit()
    conn.close()
    return quotation_id

def get_all_quotations():
    """Retrieves all quotations."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT q.id, c.name, q.quotation_date, q.total_amount, q.status
        FROM quotations q
        JOIN customers c ON q.customer_id = c.id
        ORDER BY q.quotation_date DESC
    """)
    quotations = []
    for row in cursor.fetchall():
        quotations.append({
            'id': row[0],
            'customer_name': row[1],
            'date': row[2],
            'total': float(row[3]),
            'status': row[4]
        })
    conn.close()
    return quotations

def convert_quotation_to_sales_order(quotation_id):
    """Converts a quotation to a sales order."""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Get quotation details
        cursor.execute("SELECT customer_id, total_amount FROM quotations WHERE id = ?", (quotation_id,))
        quotation = cursor.fetchone()
        if not quotation:
            raise ValueError("Quotation not found")
            
        customer_id, total_amount = quotation
        
        # Create Sales Order
        order_date = datetime.now().date()
        db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            cursor.execute(
                "INSERT INTO sales_orders (customer_id, order_date, total_amount, status) VALUES (?, ?, ?, 'Pending')",
                (customer_id, order_date, total_amount)
            )
            order_id = cursor.lastrowid
        else:
            cursor.execute(
                "INSERT INTO sales_orders (customer_id, order_date, total_amount, status) OUTPUT INSERTED.id VALUES (?, ?, ?, 'Pending')",
                (customer_id, order_date, total_amount)
            )
            order_id = cursor.fetchone()[0]
            
        # Copy items
        cursor.execute("SELECT product_id, quantity, unit_price FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        items = cursor.fetchall()
        
        for item in items:
            cursor.execute(
                "INSERT INTO sales_order_items (sales_order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, item[0], item[1], item[2])
            )
            
        # Update quotation status
        cursor.execute("UPDATE quotations SET status = 'Converted' WHERE id = ?", (quotation_id,))
        
        conn.commit()
        return order_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_quotation_details(quotation_id):
    """Retrieves full details for a single quotation."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT q.id, q.quotation_date, q.expiry_date, q.total_amount, q.status,
               c.name, c.email, c.address, c.customer_code
        FROM quotations q
        JOIN customers c ON q.customer_id = c.id
        WHERE q.id = ?
    """, (quotation_id,))
    data = cursor.fetchone()

    if not data:
        return None

    details = {
        'id': data[0],
        'date': data[1],
        'expiry_date': data[2],
        'total_amount': float(data[3]),
        'status': data[4],
        'customer_name': data[5],
        'customer_email': data[6],
        'customer_address': data[7],
        'customer_code': data[8] or '',
        'items': []
    }

    cursor.execute("""
        SELECT p.name, qi.quantity, qi.unit_price, p.item_code
        FROM quotation_items qi
        JOIN products p ON qi.product_id = p.id
        WHERE qi.quotation_id = ?
    """, (quotation_id,))
    for row in cursor.fetchall():
        details['items'].append({
            'product_name': row[0],
            'quantity': row[1],
            'unit_price': float(row[2]),
            'item_code': row[3] or ''
        })

    conn.close()
    return details

# --- Sales Order Functions ---

def create_sales_order(customer_id, items):
    """Creates a new sales order."""
    conn = connect_db()
    cursor = conn.cursor()

    total_amount = sum(item['quantity'] * item['price'] for item in items)
    order_date = datetime.now().date()

    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
    if db_type == 'sqlite':
        cursor.execute(
            "INSERT INTO sales_orders (customer_id, order_date, total_amount, status) VALUES (?, ?, ?, 'Pending')",
            (customer_id, order_date, total_amount)
        )
        order_id = cursor.lastrowid
    else:
        cursor.execute(
            "INSERT INTO sales_orders (customer_id, order_date, total_amount, status) OUTPUT INSERTED.id VALUES (?, ?, ?, 'Pending')",
            (customer_id, order_date, total_amount)
        )
        order_id = cursor.fetchone()[0]

    for item in items:
        cursor.execute(
            "INSERT INTO sales_order_items (sales_order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (order_id, item['product_id'], item['quantity'], item['price'])
        )

    conn.commit()
    conn.close()
    return order_id

def get_all_sales_orders():
    """Retrieves all sales orders."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT so.id, c.name, so.order_date, so.total_amount, so.status
        FROM sales_orders so
        JOIN customers c ON so.customer_id = c.id
        ORDER BY so.order_date DESC
    """)
    orders = []
    for row in cursor.fetchall():
        orders.append({
            'id': row[0],
            'customer_name': row[1],
            'date': row[2],
            'total': float(row[3]),
            'status': row[4]
        })
    conn.close()
    return orders

def convert_sales_order_to_invoice(order_id):
    """Converts a sales order to an invoice."""
    conn = connect_db()
    cursor = conn.cursor()
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    tax_rate = float(config.get('Tax', 'rate', fallback='0.0')) / 100
    
    try:
        # Get order details
        cursor.execute("SELECT customer_id, total_amount FROM sales_orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError("Sales Order not found")
            
        customer_id, total_amount = order
        
        # Get items to check stock
        cursor.execute("SELECT product_id, quantity, unit_price FROM sales_order_items WHERE sales_order_id = ?", (order_id,))
        items = cursor.fetchall()
        
        # Check stock
        for item in items:
            cursor.execute("SELECT quantity_in_stock, name FROM products WHERE id = ?", (item[0],))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Product ID {item[0]} not found.")
            
            current_stock, product_name = result
            if current_stock < item[1]:
                raise ValueError(f"Insufficient stock for '{product_name}'. Available: {current_stock}, Requested: {item[1]}")

        # Calculate tax
        subtotal = sum(item[1] * item[2] for item in items)
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount

        # Create Invoice
        invoice_date = datetime.now().date()
        due_date = invoice_date + timedelta(days=30)
        db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
        
        if db_type == 'sqlite':
            cursor.execute(
                "INSERT INTO invoices (customer_id, invoice_date, due_date, total_amount, tax_amount, status) VALUES (?, ?, ?, ?, ?, 'Unpaid')",
                (customer_id, invoice_date, due_date, total_amount, tax_amount)
            )
            invoice_id = cursor.lastrowid
        else:
            cursor.execute(
                "INSERT INTO invoices (customer_id, invoice_date, due_date, total_amount, tax_amount, status) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, 'Unpaid')",
                (customer_id, invoice_date, due_date, total_amount, tax_amount)
            )
            invoice_id = cursor.fetchone()[0]
            
        # Copy items and deduct stock
        for item in items:
            cursor.execute(
                "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (invoice_id, item[0], item[1], item[2])
            )
            cursor.execute(
                "UPDATE products SET quantity_in_stock = quantity_in_stock - ? WHERE id = ?",
                (item[1], item[0])
            )
            
        # Update order status
        cursor.execute("UPDATE sales_orders SET status = 'Invoiced' WHERE id = ?", (order_id,))
        
        conn.commit()
        return invoice_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_sales_order_details(order_id):
    """Retrieves full details for a single sales order."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT so.id, so.order_date, so.total_amount, so.status,
               c.name, c.email, c.address, c.customer_code
        FROM sales_orders so
        JOIN customers c ON so.customer_id = c.id
        WHERE so.id = ?
    """, (order_id,))
    data = cursor.fetchone()

    if not data:
        return None

    details = {
        'id': data[0],
        'date': data[1],
        'total_amount': float(data[2]),
        'status': data[3],
        'customer_name': data[4],
        'customer_email': data[5],
        'customer_address': data[6],
        'customer_code': data[7] or '',
        'items': []
    }

    cursor.execute("""
        SELECT p.name, soi.quantity, soi.unit_price, p.item_code
        FROM sales_order_items soi
        JOIN products p ON soi.product_id = p.id
        WHERE soi.sales_order_id = ?
    """, (order_id,))
    for row in cursor.fetchall():
        details['items'].append({
            'product_name': row[0],
            'quantity': row[1],
            'unit_price': float(row[2]),
            'item_code': row[3] or ''
        })

    conn.close()
    return details

# --- Supplier Functions ---

def add_supplier(name, email, phone, address):
    """Adds a new supplier."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO suppliers (name, email, phone, address) VALUES (?, ?, ?, ?)",
        (name, email, phone, address)
    )
    conn.commit()
    conn.close()

def get_all_suppliers():
    """Retrieves all suppliers."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, address FROM suppliers")
    suppliers = []
    for row in cursor.fetchall():
        suppliers.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'address': row[4]
        })
    conn.close()
    return suppliers

# --- Purchase Order Functions ---

def create_purchase_order(supplier_id, items):
    """Creates a new purchase order."""
    conn = connect_db()
    cursor = conn.cursor()

    total_amount = sum(item['quantity'] * item['cost'] for item in items)
    order_date = datetime.now().date()

    db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
    if db_type == 'sqlite':
        cursor.execute(
            "INSERT INTO purchase_orders (supplier_id, order_date, total_amount, status) VALUES (?, ?, ?, 'Pending')",
            (supplier_id, order_date, total_amount)
        )
        order_id = cursor.lastrowid
    else:
        cursor.execute(
            "INSERT INTO purchase_orders (supplier_id, order_date, total_amount, status) OUTPUT INSERTED.id VALUES (?, ?, ?, 'Pending')",
            (supplier_id, order_date, total_amount)
        )
        order_id = cursor.fetchone()[0]

    for item in items:
        cursor.execute(
            "INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, unit_cost) VALUES (?, ?, ?, ?)",
            (order_id, item['product_id'], item['quantity'], item['cost'])
        )

    conn.commit()
    conn.close()
    return order_id

def receive_purchase_order(order_id, user_id):
    """Receives a purchase order and updates stock."""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Get items
        cursor.execute("SELECT product_id, quantity FROM purchase_order_items WHERE purchase_order_id = ?", (order_id,))
        items = cursor.fetchall()
        
        for item in items:
            product_id, quantity = item
            # Update stock
            cursor.execute("UPDATE products SET quantity_in_stock = quantity_in_stock + ? WHERE id = ?", (quantity, product_id))
            
            # Log adjustment
            cursor.execute(
                "INSERT INTO stock_adjustments (product_id, adjustment_date, quantity_change, reason, user_id) VALUES (?, ?, ?, ?, ?)",
                (product_id, datetime.now().date(), quantity, f"Received PO #{order_id}", user_id)
            )
            
        # Update status
        cursor.execute("UPDATE purchase_orders SET status = 'Received' WHERE id = ?", (order_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def adjust_stock(product_id, quantity_change, reason, user_id):
    """Manually adjusts stock level."""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE products SET quantity_in_stock = quantity_in_stock + ? WHERE id = ?", (quantity_change, product_id))
        
        cursor.execute(
            "INSERT INTO stock_adjustments (product_id, adjustment_date, quantity_change, reason, user_id) VALUES (?, ?, ?, ?, ?)",
            (product_id, datetime.now().date(), quantity_change, reason, user_id)
        )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Profit & Loss Functions ---

def get_profit_loss_data(start_date, end_date):
    """Calculates profit and loss data for a given date range."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Total Income (from paid/partial invoices)
    cursor.execute("""
        SELECT SUM(amount) 
        FROM payments 
        WHERE payment_date BETWEEN ? AND ?
    """, (start_date, end_date))
    total_income = cursor.fetchone()[0] or 0.0
    
    # Total Expenses
    cursor.execute("""
        SELECT SUM(amount) 
        FROM expenses 
        WHERE expense_date BETWEEN ? AND ?
    """, (start_date, end_date))
    total_expenses = cursor.fetchone()[0] or 0.0
    
    # Expense Breakdown by Category
    cursor.execute("""
        SELECT c.name, SUM(e.amount)
        FROM expenses e
        JOIN expense_categories c ON e.category_id = c.id
        WHERE e.expense_date BETWEEN ? AND ?
        GROUP BY c.name
    """, (start_date, end_date))
    expense_breakdown = []
    for row in cursor.fetchall():
        expense_breakdown.append({'category': row[0], 'amount': float(row[1])})
        
    conn.close()
    
    net_profit = float(total_income) - float(total_expenses)
    
    return {
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'net_profit': net_profit,
        'expense_breakdown': expense_breakdown
    }

# --- Backup and Restore Functions ---

def backup_database(filepath):
    """Exports all database tables to a JSON file."""
    conn = connect_db()
    cursor = conn.cursor()
    
    data = {}
    
    tables = ['users', 'customers', 'products', 'invoices', 'invoice_items', 'audit_log', 'payments', 'expenses', 'expense_categories', 'automation_rules', 'email_signatures', 'quotations', 'quotation_items', 'sales_orders', 'sales_order_items', 'suppliers', 'purchase_orders', 'purchase_order_items', 'stock_adjustments']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            columns = [column[0] for column in cursor.description]
            rows = []
            for row in cursor.fetchall():
                rows.append(dict(zip(columns, row)))
            data[table] = rows
        except Exception:
            pass
        
    conn.close()
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, default=str, indent=4)
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def restore_database(filepath):
    """Restores the database from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load backup file: {e}")
        return False

    conn = connect_db()
    cursor = conn.cursor()
    
    # Disable constraints or delete in reverse order to avoid FK violations
    # Deleting in reverse dependency order
    tables_reverse = ['stock_adjustments', 'purchase_order_items', 'purchase_orders', 'suppliers', 'sales_order_items', 'sales_orders', 'quotation_items', 'quotations', 'email_signatures', 'expenses', 'expense_categories', 'payments', 'audit_log', 'invoice_items', 'invoices', 'products', 'customers', 'users', 'automation_rules']
    
    try:
        for table in tables_reverse:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except Exception:
                pass
            
        # Insert data in dependency order
        tables_forward = ['users', 'customers', 'products', 'invoices', 'invoice_items', 'audit_log', 'payments', 'expense_categories', 'expenses', 'automation_rules', 'email_signatures', 'quotations', 'quotation_items', 'sales_orders', 'sales_order_items', 'suppliers', 'purchase_orders', 'purchase_order_items', 'stock_adjustments']
        
        db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')

        for table in tables_forward:
            if table not in data: continue
            
            rows = data[table]
            if not rows: continue
            
            columns = list(rows[0].keys())
            col_names = ", ".join(columns)
            placeholders = ", ".join(["?"] * len(columns))
            
            if db_type == 'mssql':
                try:
                    cursor.execute(f"SET IDENTITY_INSERT {table} ON")
                except Exception: pass
            
            for row in rows:
                values = [row[col] for col in columns]
                cursor.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values)
                
            if db_type == 'mssql':
                try:
                    cursor.execute(f"SET IDENTITY_INSERT {table} OFF")
                except Exception: pass
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Restore failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    create_tables()
    print("Database and tables checked/created successfully.")
