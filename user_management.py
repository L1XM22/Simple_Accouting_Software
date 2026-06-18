import tkinter as tk
from tkinter import ttk, messagebox
from database import get_all_users, create_user, update_user_permissions, delete_user, log_action

class UserManagementWindow(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("User Management")
        self.geometry("900x600")
        self.current_user = current_user

        self.all_permissions = [
            'manage_customers', 'manage_products', 'create_invoices', 'view_reports', 'manage_expenses', 'manage_automation', 'manage_communication', 'manage_sales', 'manage_inventory'
        ]

        # --- Main Layout ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Left Column: User List & Create User ---
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left_frame.rowconfigure(0, weight=1)

        # User List
        user_list_frame = ttk.LabelFrame(left_frame, text="Users", padding="10")
        user_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.user_listbox = tk.Listbox(user_list_frame)
        self.user_listbox.pack(fill=tk.BOTH, expand=True)
        self.user_listbox.bind('<<ListboxSelect>>', self.on_user_select)

        # Create User Frame
        create_user_frame = ttk.LabelFrame(left_frame, text="Create New User", padding="10")
        create_user_frame.pack(fill=tk.X)

        ttk.Label(create_user_frame, text="Username:").pack(anchor=tk.W)
        self.new_username_var = tk.StringVar()
        ttk.Entry(create_user_frame, textvariable=self.new_username_var).pack(fill=tk.X, pady=(0, 5))

        ttk.Label(create_user_frame, text="Password:").pack(anchor=tk.W)
        self.new_password_var = tk.StringVar()
        ttk.Entry(create_user_frame, textvariable=self.new_password_var, show="*").pack(fill=tk.X, pady=(0, 5))

        ttk.Label(create_user_frame, text="Role:").pack(anchor=tk.W)
        self.new_role_var = tk.StringVar(value="standard")
        ttk.Combobox(create_user_frame, textvariable=self.new_role_var, values=["standard", "admin"], state="readonly").pack(fill=tk.X, pady=(0, 10))

        ttk.Button(create_user_frame, text="Create User", command=self.create_new_user).pack(fill=tk.X)

        # --- Right Column: User Details & Permissions ---
        details_frame = ttk.LabelFrame(main_frame, text="Details & Permissions", padding="10")
        details_frame.grid(row=0, column=1, sticky="nsew")

        self.username_label = ttk.Label(details_frame, text="Username: ")
        self.username_label.pack(anchor=tk.W, pady=(0, 5))
        self.role_label = ttk.Label(details_frame, text="Role: ")
        self.role_label.pack(anchor=tk.W, pady=(0, 20))

        self.perm_vars = {}
        for perm in self.all_permissions:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(details_frame, text=perm.replace('_', ' ').title(), variable=var)
            cb.pack(anchor=tk.W)
            self.perm_vars[perm] = var

        # --- Action Buttons ---
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(pady=20, anchor=tk.E)
        
        self.save_button = ttk.Button(button_frame, text="Save Permissions", command=self.save_permissions, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(button_frame, text="Delete User", command=self.delete_selected_user, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT)

        self.load_users()

    def load_users(self):
        self.user_listbox.delete(0, tk.END)
        self.users = get_all_users()
        for user in self.users:
            self.user_listbox.insert(tk.END, f"{user['username']} ({user['role']})")

    def on_user_select(self, event):
        selection = event.widget.curselection()
        if not selection:
            return

        index = selection[0]
        self.selected_user = self.users[index]

        self.username_label.config(text=f"Username: {self.selected_user['username']}")
        self.role_label.config(text=f"Role: {self.selected_user['role']}")

        is_admin = self.selected_user['role'] == 'admin'
        for perm, var in self.perm_vars.items():
            var.set(is_admin or perm in self.selected_user['permissions'])
            cb = var.get_tk_widget()
            cb.config(state=tk.DISABLED if is_admin else tk.NORMAL)

        self.save_button.config(state=tk.NORMAL if not is_admin else tk.DISABLED)
        
        # Enable delete button only if not deleting 'admin' or self
        can_delete = (self.selected_user['username'] != 'admin' and 
                      self.selected_user['id'] != self.current_user['id'])
        self.delete_button.config(state=tk.NORMAL if can_delete else tk.DISABLED)

    def create_new_user(self):
        username = self.new_username_var.get()
        password = self.new_password_var.get()
        role = self.new_role_var.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            return

        if create_user(username, password, role):
            log_action(self.current_user['id'], self.current_user['username'], f"Created new user '{username}' with role '{role}'.")
            messagebox.showinfo("Success", f"User '{username}' created successfully.")
            self.new_username_var.set("")
            self.new_password_var.set("")
            self.load_users()
        else:
            messagebox.showerror("Error", f"User '{username}' already exists or an error occurred.")

    def save_permissions(self):
        if not hasattr(self, 'selected_user'):
            return

        new_permissions = [perm for perm, var in self.perm_vars.items() if var.get()]
        
        try:
            update_user_permissions(self.selected_user['id'], new_permissions)
            log_action(
                self.current_user['id'], self.current_user['username'],
                f"Updated permissions for user '{self.selected_user['username']}' to: {', '.join(new_permissions)}"
            )
            messagebox.showinfo("Success", "User permissions updated successfully.")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update permissions: {e}")

    def delete_selected_user(self):
        if not hasattr(self, 'selected_user'):
            return
            
        if self.selected_user['username'] == 'admin':
            messagebox.showerror("Error", "Cannot delete the default admin user.")
            return
            
        if self.selected_user['id'] == self.current_user['id']:
            messagebox.showerror("Error", "You cannot delete your own account.")
            return

        confirm = messagebox.askyesno(
            "Delete User",
            f"Are you sure you want to delete the user '{self.selected_user['username']}'?"
        )
        if not confirm:
            return

        try:
            deleted_username = self.selected_user['username']
            if delete_user(self.selected_user['id']):
                log_action(
                    self.current_user['id'], self.current_user['username'],
                    f"Deleted user '{deleted_username}'."
                )
                messagebox.showinfo("Success", "User deleted successfully.")
                self.load_users()
                self.clear_details()
            else:
                messagebox.showerror("Error", "Failed to delete user. Check database constraints.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {e}")

    def clear_details(self):
        self.username_label.config(text="Username: ")
        self.role_label.config(text="Role: ")
        for var in self.perm_vars.values():
            var.set(False)
        self.save_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        if hasattr(self, 'selected_user'):
            del self.selected_user

if __name__ == '__main__':
    # Dummy user for testing
    dummy_user = {'id': 0, 'username': 'test_admin', 'role': 'admin'}
    root = tk.Tk()
    app = UserManagementWindow(root, dummy_user)
    root.withdraw()
    app.mainloop()
