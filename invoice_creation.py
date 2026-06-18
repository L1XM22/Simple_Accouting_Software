import tkinter as tk
from tkinter import ttk, messagebox
from database import get_all_customers_from_db, get_all_products_from_db, create_invoice
from automation_service import trigger_automation
from theme import apply_theme

class InvoiceCreationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create New Invoice")
        self.geometry("800x600")
        
        # Apply theme with Blue accent
        apply_theme(self, accent_color='#2980B9')

        self.customers = get_all_customers_from_db()
        self.products = get_all_products_from_db()
        self.invoice_items = []

        # --- Top Frame: Customer and Date ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Customer:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.customer_var = tk.StringVar()
        customer_names = [f"{c['name']} ({c['customer_code']})" if c['customer_code'] else c['name'] for c in self.customers]
        self.customer_menu = ttk.Combobox(top_frame, textvariable=self.customer_var, values=customer_names, width=40)
        self.customer_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        # --- Middle Frame: Add Products ---
        middle_frame = ttk.Frame(self, padding="10")
        middle_frame.pack(fill=tk.X)

        ttk.Label(middle_frame, text="Product:").grid(row=0, column=0, padx=5, pady=5)
        self.product_var = tk.StringVar()
        product_names = [f"{p['name']} ({p['item_code']})" if p['item_code'] else p['name'] for p in self.products]
        self.product_menu = ttk.Combobox(middle_frame, textvariable=self.product_var, values=product_names, width=40)
        self.product_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(middle_frame, text="Quantity:").grid(row=0, column=2, padx=5, pady=5)
        self.quantity_var = tk.IntVar(value=1)
        self.quantity_entry = ttk.Entry(middle_frame, textvariable=self.quantity_var, width=10)
        self.quantity_entry.grid(row=0, column=3, padx=5, pady=5)

        add_item_button = ttk.Button(middle_frame, text="Add Item", command=self.add_item)
        add_item_button.grid(row=0, column=4, padx=5, pady=5)

        # --- Items Treeview ---
        items_frame = ttk.Frame(self, padding="10")
        items_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(items_frame, columns=("Code", "Product", "Quantity", "Price", "Total"), show="headings")
        self.tree.heading("Code", text="Code")
        self.tree.heading("Product", text="Product")
        self.tree.heading("Quantity", text="Quantity")
        self.tree.heading("Price", text="Unit Price")
        self.tree.heading("Total", text="Total")
        
        self.tree.column("Code", width=80)
        self.tree.column("Product", width=200)
        self.tree.column("Quantity", width=80, anchor=tk.CENTER)
        self.tree.column("Price", width=100, anchor=tk.E)
        self.tree.column("Total", width=100, anchor=tk.E)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Bottom Frame: Total and Save ---
        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill=tk.X)

        self.total_label = ttk.Label(bottom_frame, text="Total: R0.00")
        self.total_label.pack(side=tk.LEFT, padx=5)

        save_button = ttk.Button(bottom_frame, text="Save Invoice", command=self.save_invoice)
        save_button.pack(side=tk.RIGHT, padx=5)

    def add_item(self):
        product_selection = self.product_var.get()
        quantity = self.quantity_var.get()

        if not product_selection or quantity <= 0:
            return

        # Extract product name (handle cases with/without code)
        if '(' in product_selection and product_selection.endswith(')'):
            product_name = product_selection.rsplit(' (', 1)[0]
        else:
            product_name = product_selection

        product = next((p for p in self.products if p['name'] == product_name), None)
        if not product:
            return

        total_price = product['price'] * quantity
        self.tree.insert("", tk.END, values=(
            product.get('item_code', ''),
            product_name, 
            quantity, 
            f"R{product['price']:.2f}", 
            f"R{total_price:.2f}"
        ))

        self.invoice_items.append({
            'product_id': product['id'],
            'name': product_name,
            'quantity': quantity,
            'price': product['price']
        })
        self.update_total()
        self.product_var.set('')
        self.quantity_var.set(1)


    def update_total(self):
        total = sum(item['quantity'] * item['price'] for item in self.invoice_items)
        self.total_label.config(text=f"Total: R{total:.2f}")


    def save_invoice(self):
        customer_selection = self.customer_var.get()
        if not customer_selection or not self.invoice_items:
            messagebox.showwarning("Warning", "Please select a customer and add items.")
            return

        if '(' in customer_selection and customer_selection.endswith(')'):
            customer_name = customer_selection.rsplit(' (', 1)[0]
        else:
            customer_name = customer_selection

        customer = next((c for c in self.customers if c['name'] == customer_name), None)
        if not customer:
            return

        try:
            invoice_id = create_invoice(customer['id'], self.invoice_items)
            messagebox.showinfo("Success", "Invoice created successfully!")
            
            trigger_automation('Invoice Created', invoice_id=invoice_id)
            
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error creating invoice: {e}")


if __name__ == '__main__':
    root = tk.Tk()
    app = InvoiceCreationWindow(root)
    root.withdraw()
    app.mainloop()
