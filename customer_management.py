import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from database import (
    add_customer_to_db,
    get_all_customers_from_db,
    update_customer_in_db,
    delete_customer_from_db,
)
from theme import apply_theme

class CustomerManagementWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Customer Management")
        self.geometry("700x500")
        
        # Apply theme with Teal accent
        apply_theme(self, accent_color='#16A085')

        # --- Top frame for actions ---
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        top_frame.pack(fill=tk.X)
        
        export_button = ttk.Button(top_frame, text="Export to CSV", command=self.export_to_csv)
        export_button.pack(side=tk.RIGHT, padx=5)
        
        import_button = ttk.Button(top_frame, text="Import from CSV", command=self.import_from_csv)
        import_button.pack(side=tk.RIGHT, padx=5)

        # --- Main content frame ---
        content_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for the customer list
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.customer_listbox = tk.Listbox(left_frame)
        self.customer_listbox.pack(fill=tk.BOTH, expand=True)
        self.customer_listbox.bind('<<ListboxSelect>>', self.on_customer_select)

        # Right frame for the customer details
        right_frame = ttk.LabelFrame(content_frame, text="Customer Details")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, ipadx=10, ipady=10)

        ttk.Label(right_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(right_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)

        ttk.Label(right_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.email_entry = ttk.Entry(right_frame)
        self.email_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Label(right_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.phone_entry = ttk.Entry(right_frame)
        self.phone_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)

        ttk.Label(right_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.address_entry = ttk.Entry(right_frame)
        self.address_entry.grid(row=3, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(right_frame, text="Code:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.code_entry = ttk.Entry(right_frame)
        self.code_entry.grid(row=4, column=1, sticky=tk.EW, pady=2)

        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Add", command=self.add_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update", command=self.update_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_customer).pack(side=tk.LEFT, padx=5)

        self.load_customers()

    def load_customers(self):
        self.customers = get_all_customers_from_db()
        self.customer_listbox.delete(0, tk.END)
        for customer in self.customers:
            display_text = customer['name']
            if customer.get('customer_code'):
                display_text += f" ({customer['customer_code']})"
            self.customer_listbox.insert(tk.END, display_text)

    def on_customer_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            customer = self.customers[index]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, customer['name'])
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, customer['email'])
            self.phone_entry.delete(0, tk.END)
            self.phone_entry.insert(0, customer['phone'])
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, customer['address'])
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, customer.get('customer_code', ''))

    def add_customer(self):
        add_customer_to_db(
            self.name_entry.get(), self.email_entry.get(),
            self.phone_entry.get(), self.address_entry.get(),
            self.code_entry.get()
        )
        self.load_customers()
        self.clear_entries()

    def update_customer(self):
        selection = self.customer_listbox.curselection()
        if selection:
            index = selection[0]
            customer_id = self.customers[index]['id']
            update_customer_in_db(
                customer_id, self.name_entry.get(), self.email_entry.get(),
                self.phone_entry.get(), self.address_entry.get(),
                self.code_entry.get()
            )
            self.load_customers()
            self.clear_entries()

    def delete_customer(self):
        selection = self.customer_listbox.curselection()
        if selection:
            index = selection[0]
            customer_id = self.customers[index]['id']
            delete_customer_from_db(customer_id)
            self.load_customers()
            self.clear_entries()

    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.code_entry.delete(0, tk.END)

    def export_to_csv(self):
        """Exports the current list of customers to a CSV file."""
        if not self.customers:
            messagebox.showinfo("Export", "There are no customers to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="customers.csv"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name', 'email', 'phone', 'address', 'customer_code'])
                writer.writeheader()
                writer.writerows(self.customers)
            messagebox.showinfo("Success", f"Customer data exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred: {e}")

    def import_from_csv(self):
        """Imports customers from a CSV file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # Basic validation
                    if 'name' in row:
                        add_customer_to_db(
                            row['name'],
                            row.get('email', ''),
                            row.get('phone', ''),
                            row.get('address', ''),
                            row.get('customer_code', '')
                        )
                        count += 1
            
            messagebox.showinfo("Success", f"Successfully imported {count} customers.")
            self.load_customers()
        except Exception as e:
            messagebox.showerror("Import Error", f"An error occurred: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = CustomerManagementWindow(root)
    root.withdraw()
    app.mainloop()
