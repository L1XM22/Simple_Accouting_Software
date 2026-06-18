import tkinter as tk
from tkinter import ttk, messagebox
from database import get_automation_rules, add_automation_rule, delete_automation_rule, toggle_automation_rule, log_action

class AutomationWindow(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Automation Rules")
        self.geometry("700x500")
        self.current_user = current_user

        # --- Top Frame: Add Rule ---
        add_frame = ttk.LabelFrame(self, text="Add New Rule", padding="10")
        add_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(add_frame, text="Rule Name:").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(add_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="Trigger:").grid(row=0, column=2, padx=5, pady=5)
        self.trigger_var = tk.StringVar()
        self.trigger_menu = ttk.Combobox(add_frame, textvariable=self.trigger_var, values=["Invoice Created"], state="readonly")
        self.trigger_menu.grid(row=0, column=3, padx=5, pady=5)
        self.trigger_menu.current(0)

        ttk.Label(add_frame, text="Action:").grid(row=0, column=4, padx=5, pady=5)
        self.action_var = tk.StringVar()
        self.action_menu = ttk.Combobox(add_frame, textvariable=self.action_var, values=["Email Invoice"], state="readonly")
        self.action_menu.grid(row=0, column=5, padx=5, pady=5)
        self.action_menu.current(0)

        add_button = ttk.Button(add_frame, text="Add Rule", command=self.add_rule)
        add_button.grid(row=1, column=5, padx=5, pady=10, sticky="e")

        # --- Bottom Frame: Rules List ---
        list_frame = ttk.LabelFrame(self, text="Active Rules", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Trigger", "Action", "Status"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Trigger", text="Trigger Event")
        self.tree.heading("Action", text="Action")
        self.tree.heading("Status", text="Status")

        self.tree.column("ID", width=50)
        self.tree.column("Name", width=200)
        self.tree.column("Trigger", width=150)
        self.tree.column("Action", width=150)
        self.tree.column("Status", width=80)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Action Buttons ---
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Toggle Active/Inactive", command=self.toggle_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Rule", command=self.delete_rule).pack(side=tk.LEFT, padx=5)

        self.load_rules()

    def add_rule(self):
        name = self.name_entry.get()
        trigger = self.trigger_var.get()
        action = self.action_var.get()

        if not name:
            messagebox.showerror("Error", "Please enter a rule name.")
            return

        try:
            add_automation_rule(name, trigger, action)
            log_action(self.current_user['id'], self.current_user['username'], f"Added automation rule: {name}")
            messagebox.showinfo("Success", "Rule added successfully.")
            self.load_rules()
            self.name_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add rule: {e}")

    def load_rules(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        rules = get_automation_rules()
        for rule in rules:
            status = "Active" if rule['is_active'] else "Inactive"
            self.tree.insert("", tk.END, values=(
                rule['id'], rule['name'], rule['trigger_event'], rule['action_type'], status
            ))

    def toggle_rule(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        rule_id = item['values'][0]
        current_status = item['values'][4]
        new_status = not (current_status == "Active")
        
        try:
            toggle_automation_rule(rule_id, new_status)
            self.load_rules()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update rule: {e}")

    def delete_rule(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        rule_id = item['values'][0]
        
        if messagebox.askyesno("Confirm", "Delete this rule?"):
            try:
                delete_automation_rule(rule_id)
                log_action(self.current_user['id'], self.current_user['username'], f"Deleted automation rule ID: {rule_id}")
                self.load_rules()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete rule: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    dummy_user = {'id': 0, 'username': 'test_admin'}
    app = AutomationWindow(root, dummy_user)
    root.withdraw()
    app.mainloop()
