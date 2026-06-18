import pyodbc
import sqlite3
import configparser
from database import connect_db, CURRENT_DB_CONFIG, set_db_profile

def migrate():
    print("Starting database migration...")
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Set the profile to ensure connect_db works correctly
    last_profile = config.get('General', 'last_profile', fallback='SQLite')
    print(f"Using profile: {last_profile}")
    set_db_profile(last_profile)
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        db_type = CURRENT_DB_CONFIG.get('type', 'sqlite')
        print(f"Database type: {db_type}")

        # 1. Add tax_amount to invoices
        print("Attempting to add 'tax_amount' to 'invoices' table...")
        try:
            if db_type == 'sqlite':
                cursor.execute("ALTER TABLE invoices ADD COLUMN tax_amount REAL DEFAULT 0")
            else:
                cursor.execute("ALTER TABLE invoices ADD tax_amount DECIMAL(18, 2) DEFAULT 0")
            print(" - Success: 'tax_amount' column added.")
        except Exception as e:
            print(f" - Note: Could not add 'tax_amount' (it might already exist). Error: {e}")

        # 2. Add amount_paid to invoices (just in case)
        print("Attempting to add 'amount_paid' to 'invoices' table...")
        try:
            if db_type == 'sqlite':
                cursor.execute("ALTER TABLE invoices ADD COLUMN amount_paid REAL DEFAULT 0")
            else:
                cursor.execute("ALTER TABLE invoices ADD amount_paid DECIMAL(18, 2) DEFAULT 0")
            print(" - Success: 'amount_paid' column added.")
        except Exception as e:
            print(f" - Note: Could not add 'amount_paid' (it might already exist). Error: {e}")

        conn.commit()
        conn.close()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
