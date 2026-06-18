import tkinter as tk
from tkinter import ttk
import sys
from customer_management import CustomerManagementWindow
from product_management import ProductManagementWindow
from invoice_creation import InvoiceCreationWindow
from reporting import ReportingWindow
from settings import SettingsWindow
from dashboard import Dashboard
from user_management import UserManagementWindow
from login import LoginWindow
from audit_trail_window import AuditTrailWindow
from backup_restore_window import BackupRestoreWindow
from expense_management import ExpenseManagementWindow
from automation_window import AutomationWindow
from communication_window import CommunicationWindow
from document_listing import DocumentListingWindow
from inventory_management import InventoryManagementWindow
from advanced_reporting import AdvancedReportingWindow
from database import create_tables, log_action
from theme import apply_theme

def main():
    """Application entry point."""
    while True:
        # Apply theme to the login window first
        login_app = LoginWindow()
        apply_theme(login_app)
        user = login_app.run()

        if not user:
            # User closed the login window without logging in
            break

        create_tables()
        root = tk.Tk()
        root.title(f"Inter-counting - Logged in as {user['username']} ({user['role']})")
        root.geometry("1100x750")
        
        # Apply theme to the main window
        apply_theme(root)

        # --- Main Layout ---
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Sidebar ---
        # Create a custom style for the sidebar to give it a distinct look
        style = ttk.Style()
        style.configure('Sidebar.TFrame', background='#F5F5F5') # Very light grey for sidebar
        
        sidebar = ttk.Frame(main_frame, width=220, style='Sidebar.TFrame')
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Prevent sidebar from shrinking
        sidebar.pack_propagate(False)

        # App Logo/Title
        title_label = ttk.Label(sidebar, text="Inter-counting", font=("Segoe UI", 20, "bold"), background='#F5F5F5', foreground='#2C3E50')
        title_label.pack(pady=(30, 20), padx=10)

        is_admin = user['role'] == 'admin'
        user_perms = user.get('permissions', [])

        def has_permission(perm_name):
            return is_admin or perm_name in user_perms

        # --- Navigation Buttons ---
        # Custom style for sidebar buttons - Bolder and larger
        style.configure('Sidebar.TButton', 
                        background='#F5F5F5', 
                        foreground='#2C3E50', 
                        font=('Segoe UI', 11, 'bold'), 
                        anchor='w', 
                        padding=(20, 12),
                        borderwidth=0)
        
        style.map('Sidebar.TButton', 
                  background=[('active', '#E0E0E0'), ('pressed', '#D0D0D0')],
                  foreground=[('active', '#000000')])

        def create_nav_btn(text, command):
            btn = ttk.Button(sidebar, text=text, command=command, style='Sidebar.TButton')
            btn.pack(fill=tk.X, pady=2, padx=5)

        create_nav_btn("Dashboard", lambda: show_frame(dashboard_frame))
        
        if has_permission('manage_customers'):
            create_nav_btn("Manage Customers", lambda: CustomerManagementWindow(root))
        
        if has_permission('manage_products'):
            create_nav_btn("Manage Products", lambda: ProductManagementWindow(root))
            
        if has_permission('manage_sales'):
            create_nav_btn("Sales Documents", lambda: DocumentListingWindow(root))
            
        if has_permission('manage_inventory'):
            create_nav_btn("Inventory Management", lambda: InventoryManagementWindow(root, user))
            
        if has_permission('view_reports'):
            create_nav_btn("View Reports", lambda: ReportingWindow(root))
            create_nav_btn("Advanced Reports", lambda: AdvancedReportingWindow(root))
            
        if has_permission('manage_expenses'):
            create_nav_btn("Manage Expenses", lambda: ExpenseManagementWindow(root, user))
            
        if has_permission('manage_automation'):
            create_nav_btn("Automation", lambda: AutomationWindow(root, user))
            
        if has_permission('manage_communication'):
            create_nav_btn("Communication", lambda: CommunicationWindow(root, user))
        
        if is_admin:
            ttk.Separator(sidebar, orient='horizontal').pack(fill='x', pady=15, padx=10)
            create_nav_btn("User Management", lambda: UserManagementWindow(root, user))
            create_nav_btn("Audit Trail", lambda: AuditTrailWindow(root))
            create_nav_btn("Backup & Restore", lambda: BackupRestoreWindow(root, user))
            create_nav_btn("Settings", lambda: SettingsWindow(root))

        # --- Log Out Button ---
        # Push to bottom
        ttk.Frame(sidebar, style='Sidebar.TFrame').pack(fill=tk.Y, expand=True)
        
        def logout():
            log_action(user['id'], user['username'], "User logged out.")
            root.destroy()

        logout_btn = ttk.Button(sidebar, text="Log Out", command=logout, style='Sidebar.TButton')
        logout_btn.pack(fill=tk.X, pady=20, padx=5, side=tk.BOTTOM)

        # --- Content Area ---
        content_area = ttk.Frame(main_frame, padding=20)
        content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- Top Bar with Refresh Button ---
        top_bar = ttk.Frame(content_area)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        def refresh_current_view():
            if isinstance(dashboard_frame, Dashboard):
                dashboard_frame.refresh_all()
                
        refresh_btn = ttk.Button(top_bar, text="🔄 Refresh", command=refresh_current_view, style='Action.TButton')
        refresh_btn.pack(side=tk.RIGHT)

        dashboard_frame = Dashboard(content_area)
        
        def show_frame(frame_to_show):
            frame_to_show.tkraise()
            if isinstance(frame_to_show, Dashboard):
                frame_to_show.refresh_all()

        show_frame(dashboard_frame)
        
        log_action(user['id'], user['username'], "Main application window opened.")

        root.mainloop()

if __name__ == "__main__":
    main()
