import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from database import get_expense_categories, add_expense, get_all_expenses, log_action

class ExpenseManagementWindow(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Expense Management")
        self.geometry("800x600")
        self.current_user = current_user

        # --- Top Frame: Add Expense ---
        add_frame = ttk.LabelFrame(self, text="Add New Expense", padding="10")
        add_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(add_frame, text="Date:").grid(row=0, column=0, padx=5, pady=5)
        self.date_entry = DateEntry(add_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
        self.categories = get_expense_categories()
        category_names = [c['name'] for c in self.categories]
        self.category_var = tk.StringVar()
        self.category_menu = ttk.Combobox(add_frame, textvariable=self.category_var, values=category_names)
        self.category_menu.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(add_frame, text="Amount:").grid(row=0, column=4, padx=5, pady=5)
        self.amount_var = tk.DoubleVar()
        self.amount_entry = ttk.Entry(add_frame, textvariable=self.amount_var, width=10)
        self.amount_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(add_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5)
        self.desc_entry = ttk.Entry(add_frame, width=50)
        self.desc_entry.grid(row=1, column=1, columnspan=4, padx=5, pady=5, sticky="ew")

        add_button = ttk.Button(add_frame, text="Add Expense", command=self.add_expense)
        add_button.grid(row=1, column=5, padx=5, pady=5)

        # --- Bottom Frame: Expense List ---
        list_frame = ttk.LabelFrame(self, text="Expense History", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(list_frame, columns=("Date", "Category", "Amount", "Description", "User"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Description", text="Description")
        self.tree.heading("User", text="Added By")

        self.tree.column("Date", width=100)
        self.tree.column("Category", width=150)
        self.tree.column("Amount", width=100, anchor=tk.E)
        self.tree.column("Description", width=300)
        self.tree.column("User", width=100)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_expenses()

    def add_expense(self):
        date = self.date_entry.get_date()
        category_name = self.category_var.get()
        amount = self.amount_var.get()
        description = self.desc_entry.get()

        if not category_name or amount <= 0:
            messagebox.showerror("Error", "Please select a category and enter a valid amount.")
            return

        category_id = next((c['id'] for c in self.categories if c['name'] == category_name), None)
        
        try:
            add_expense(date, category_id, amount, description, self.current_user['id'])
            log_action(self.current_user['id'], self.current_user['username'], f"Added expense: R{amount} for {category_name}")
            messagebox.showinfo("Success", "Expense added successfully.")
            self.load_expenses()
            self.clear_entries()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add expense: {e}")

    def load_expenses(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        expenses = get_all_expenses()
        for exp in expenses:
            self.tree.insert("", tk.END, values=(
                exp['date'], exp['category'], f"R{exp['amount']:.2f}", exp['description'], exp['user']
            ))

    def clear_entries(self):
        self.category_var.set('')
        self.amount_var.set(0.0)
        self.desc_entry.delete(0, tk.END)

if __name__ == '__main__':
    root = tk.Tk()
    # Dummy user for testing
    dummy_user = {'id': 0, 'username': 'test_admin'}
    app = ExpenseManagementWindow(root, dummy_user)
    root.withdraw()
    app.mainloop()
