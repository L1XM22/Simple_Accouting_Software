import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import authenticate_user, get_db_profiles, set_db_profile, add_db_profile, create_tables, get_server_databases

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login - Inter-counting")
        self.geometry("450x400")
        self.user = None

        # --- Database Selection Frame ---
        db_frame = ttk.LabelFrame(self, text="Database Connection", padding="10")
        db_frame.pack(fill=tk.X, padx=20, pady=10)

        self.profiles = get_db_profiles()
        self.profile_names = list(self.profiles.keys())
        
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        last_profile = config.get('General', 'last_profile', fallback=self.profile_names[0] if self.profile_names else '')

        self.db_var = tk.StringVar(value=last_profile)
        self.db_menu = ttk.Combobox(db_frame, textvariable=self.db_var, values=self.profile_names, state="readonly")
        self.db_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.db_menu.bind("<<ComboboxSelected>>", self.on_db_change)

        add_db_button = ttk.Button(db_frame, text="+", width=3, command=self.add_new_db)
        add_db_button.pack(side=tk.RIGHT)

        # --- Login Frame ---
        login_frame = ttk.Frame(self, padding="20")
        login_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(login_frame, textvariable=self.username_var).grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(login_frame, textvariable=self.password_var, show="*").grid(row=1, column=1, sticky=tk.EW)

        login_button = ttk.Button(login_frame, text="Login", command=self.attempt_login)
        login_button.grid(row=2, column=0, columnspan=2, pady=20)

        login_frame.columnconfigure(1, weight=1)
        
        # Initialize connection with selected DB
        self.on_db_change()

    def on_db_change(self, event=None):
        selected_profile = self.db_var.get()
        if selected_profile:
            if set_db_profile(selected_profile):
                try:
                    create_tables()
                except Exception as e:
                    messagebox.showerror("Connection Error", f"Failed to connect to '{selected_profile}': {e}")

    def add_new_db(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Database Connection")
        dialog.geometry("400x400")
        
        ttk.Label(dialog, text="Profile Name:").pack(pady=5)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).pack(pady=5)
        
        ttk.Label(dialog, text="Type:").pack(pady=5)
        type_var = tk.StringVar(value="sqlite")
        type_menu = ttk.Combobox(dialog, textvariable=type_var, values=["sqlite", "mssql"], state="readonly")
        type_menu.pack(pady=5)
        
        details_frame = ttk.Frame(dialog)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=20)
        
        server_var = tk.StringVar()
        db_var = tk.StringVar()
        user_var = tk.StringVar()
        pwd_var = tk.StringVar()
        filename_var = tk.StringVar()
        
        def list_databases():
            server = server_var.get()
            user = user_var.get()
            pwd = pwd_var.get()
            
            if not server:
                messagebox.showerror("Error", "Please enter a server name.")
                return
                
            dbs = get_server_databases(server, user, pwd)
            if dbs:
                db_menu['values'] = dbs
                messagebox.showinfo("Success", f"Found {len(dbs)} databases.")
            else:
                messagebox.showerror("Error", "Could not list databases. Check connection details.")

        def update_fields(event=None):
            for widget in details_frame.winfo_children():
                widget.destroy()
                
            if type_var.get() == "mssql":
                ttk.Label(details_frame, text="Server:").grid(row=0, column=0, sticky=tk.W, pady=2)
                ttk.Entry(details_frame, textvariable=server_var).grid(row=0, column=1, sticky=tk.EW, pady=2)
                
                ttk.Label(details_frame, text="Username (Optional):").grid(row=1, column=0, sticky=tk.W, pady=2)
                ttk.Entry(details_frame, textvariable=user_var).grid(row=1, column=1, sticky=tk.EW, pady=2)
                
                ttk.Label(details_frame, text="Password (Optional):").grid(row=2, column=0, sticky=tk.W, pady=2)
                ttk.Entry(details_frame, textvariable=pwd_var, show="*").grid(row=2, column=1, sticky=tk.EW, pady=2)
                
                ttk.Button(details_frame, text="List Databases", command=list_databases).grid(row=3, column=1, sticky=tk.E, pady=5)
                
                ttk.Label(details_frame, text="Database:").grid(row=4, column=0, sticky=tk.W, pady=2)
                global db_menu
                db_menu = ttk.Combobox(details_frame, textvariable=db_var)
                db_menu.grid(row=4, column=1, sticky=tk.EW, pady=2)
                
                details_frame.columnconfigure(1, weight=1)
                
            else:
                ttk.Label(details_frame, text="Filename:").pack()
                ttk.Entry(details_frame, textvariable=filename_var).pack()
        
        type_menu.bind("<<ComboboxSelected>>", update_fields)
        update_fields() 
        
        def save():
            name = name_var.get()
            if not name:
                messagebox.showerror("Error", "Profile name is required.")
                return
            
            if type_var.get() == "mssql":
                add_db_profile(name, "mssql", server=server_var.get(), database=db_var.get(), username=user_var.get(), password=pwd_var.get())
            else:
                add_db_profile(name, "sqlite", filename=filename_var.get())
                
            self.profiles = get_db_profiles()
            self.profile_names = list(self.profiles.keys())
            self.db_menu['values'] = self.profile_names
            self.db_var.set(name)
            self.on_db_change()
            dialog.destroy()
            
        ttk.Button(dialog, text="Save", command=save).pack(pady=10)

    def attempt_login(self):
        username = self.username_var.get()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showerror("Login Failed", "Please enter both username and password.")
            return

        try:
            user = authenticate_user(username, password)
            if user:
                self.user = user
                self.destroy()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")
        except Exception as e:
             messagebox.showerror("Database Error", f"Could not authenticate: {e}")

    def run(self):
        self.mainloop()
        return self.user

if __name__ == '__main__':
    login_app = LoginWindow()
    user = login_app.run()
    if user:
        print(f"Login successful for user: {user['username']} (Role: {user['role']})")
    else:
        print("Login failed or window closed.")
