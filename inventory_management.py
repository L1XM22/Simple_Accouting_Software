import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import (
    add_supplier, get_all_suppliers, get_all_products_from_db, 
    create_purchase_order, receive_purchase_order, adjust_stock, log_action
)
from theme import apply_theme

class InventoryManagementWindow(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Inventory Management")
        self.geometry("900x600")
        self.current_user = current_user
        
        apply_theme(self, accent_color='#D35400') # Orange accent for inventory

        # --- Notebook (Tabs) ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Tab 1: Suppliers ---
        supplier_tab = ttk.Frame(notebook)
        notebook.add(supplier_tab, text="Suppliers")
        self.create_supplier_tab(supplier_tab)

        # --- Tab 2: Purchase Orders ---
        po_tab = ttk.Frame(notebook)
        notebook.add(po_tab, text="Purchase Orders")
        self.create_po_tab(po_tab)

        # --- Tab 3: Stock Adjustments ---
        adj_tab = ttk.Frame(notebook)
        notebook.add(adj_tab, text="Stock Adjustments")
        self.create_adjustment_tab(adj_tab)
        
        # Load data after all tabs are created
        self.load_suppliers()

    def create_supplier_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Add Supplier Frame
        add_frame = ttk.LabelFrame(frame, text="Add Supplier", padding="10")
        add_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(add_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
        self.sup_name_entry = ttk.Entry(add_frame)
        self.sup_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="Email:").grid(row=0, column=2, padx=5, pady=5)
        self.sup_email_entry = ttk.Entry(add_frame)
        self.sup_email_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(add_frame, text="Phone:").grid(row=0, column=4, padx=5, pady=5)
        self.sup_phone_entry = ttk.Entry(add_frame)
        self.sup_phone_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(add_frame, text="Address:").grid(row=1, column=0, padx=5, pady=5)
        self.sup_address_entry = ttk.Entry(add_frame, width=50)
        self.sup_address_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ttk.Button(add_frame, text="Add Supplier", command=self.add_supplier).grid(row=1, column=5, padx=5, pady=5)

        # Supplier List
        list_frame = ttk.LabelFrame(frame, text="Suppliers", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.supplier_tree = ttk.Treeview(list_frame, columns=("Name", "Email", "Phone", "Address"), show="headings")
        self.supplier_tree.heading("Name", text="Name")
        self.supplier_tree.heading("Email", text="Email")
        self.supplier_tree.heading("Phone", text="Phone")
        self.supplier_tree.heading("Address", text="Address")
        self.supplier_tree.pack(fill=tk.BOTH, expand=True)

    def create_po_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Create PO Frame
        create_frame = ttk.LabelFrame(frame, text="Create Purchase Order", padding="10")
        create_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(create_frame, text="Supplier:").grid(row=0, column=0, padx=5, pady=5)
        self.po_supplier_var = tk.StringVar()
        self.po_supplier_menu = ttk.Combobox(create_frame, textvariable=self.po_supplier_var, width=30)
        self.po_supplier_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(create_frame, text="Product:").grid(row=0, column=2, padx=5, pady=5)
        self.po_product_var = tk.StringVar()
        self.po_product_menu = ttk.Combobox(create_frame, textvariable=self.po_product_var, width=30)
        self.po_product_menu.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(create_frame, text="Qty:").grid(row=1, column=0, padx=5, pady=5)
        self.po_qty_entry = ttk.Entry(create_frame, width=10)
        self.po_qty_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(create_frame, text="Cost:").grid(row=1, column=2, padx=5, pady=5)
        self.po_cost_entry = ttk.Entry(create_frame, width=10)
        self.po_cost_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        ttk.Button(create_frame, text="Add Item", command=self.add_po_item).grid(row=1, column=4, padx=5, pady=5)
        
        # PO Items List (Temporary)
        self.po_items_tree = ttk.Treeview(create_frame, columns=("Product", "Qty", "Cost"), show="headings", height=5)
        self.po_items_tree.heading("Product", text="Product")
        self.po_items_tree.heading("Qty", text="Qty")
        self.po_items_tree.heading("Cost", text="Cost")
        self.po_items_tree.grid(row=2, column=0, columnspan=5, sticky="ew", padx=5, pady=5)
        
        ttk.Button(create_frame, text="Create Order", command=self.save_po).grid(row=2, column=5, padx=5, pady=5, sticky="n")

        self.po_items = []

        # Receive PO Frame (Placeholder for now, ideally this would be a list of active POs)
        receive_frame = ttk.LabelFrame(frame, text="Receive Order", padding="10")
        receive_frame.pack(fill=tk.X)
        
        ttk.Label(receive_frame, text="Enter PO ID to Receive:").pack(side=tk.LEFT, padx=5)
        self.receive_po_id = ttk.Entry(receive_frame, width=10)
        self.receive_po_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(receive_frame, text="Receive Stock", command=self.receive_po).pack(side=tk.LEFT, padx=5)

    def create_adjustment_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        adj_frame = ttk.LabelFrame(frame, text="Adjust Stock Level", padding="10")
        adj_frame.pack(fill=tk.X)

        ttk.Label(adj_frame, text="Product:").grid(row=0, column=0, padx=5, pady=5)
        self.adj_product_var = tk.StringVar()
        self.adj_product_menu = ttk.Combobox(adj_frame, textvariable=self.adj_product_var, width=30)
        self.adj_product_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(adj_frame, text="Change (+/-):").grid(row=0, column=2, padx=5, pady=5)
        self.adj_qty_entry = ttk.Entry(adj_frame, width=10)
        self.adj_qty_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(adj_frame, text="Reason:").grid(row=1, column=0, padx=5, pady=5)
        self.adj_reason_entry = ttk.Entry(adj_frame, width=50)
        self.adj_reason_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        ttk.Button(adj_frame, text="Adjust Stock", command=self.adjust_stock).grid(row=1, column=4, padx=5, pady=5)

    def load_suppliers(self):
        self.suppliers = get_all_suppliers()
        self.supplier_tree.delete(*self.supplier_tree.get_children())
        supplier_names = []
        for s in self.suppliers:
            self.supplier_tree.insert("", tk.END, values=(s['name'], s['email'], s['phone'], s['address']))
            supplier_names.append(s['name'])
        
        if hasattr(self, 'po_supplier_menu'):
            self.po_supplier_menu['values'] = supplier_names
        
        # Load products for dropdowns
        self.products = get_all_products_from_db()
        product_names = [p['name'] for p in self.products]
        
        if hasattr(self, 'po_product_menu'):
            self.po_product_menu['values'] = product_names
        if hasattr(self, 'adj_product_menu'):
            self.adj_product_menu['values'] = product_names

    def add_supplier(self):
        name = self.sup_name_entry.get()
        if not name:
            messagebox.showerror("Error", "Name is required.")
            return
        
        add_supplier(name, self.sup_email_entry.get(), self.sup_phone_entry.get(), self.sup_address_entry.get())
        messagebox.showinfo("Success", "Supplier added.")
        self.load_suppliers()
        
        # Clear entries
        self.sup_name_entry.delete(0, tk.END)
        self.sup_email_entry.delete(0, tk.END)
        self.sup_phone_entry.delete(0, tk.END)
        self.sup_address_entry.delete(0, tk.END)

    def add_po_item(self):
        product_name = self.po_product_var.get()
        try:
            qty = int(self.po_qty_entry.get())
            cost = float(self.po_cost_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or cost.")
            return
            
        product = next((p for p in self.products if p['name'] == product_name), None)
        if not product:
            return
            
        self.po_items.append({
            'product_id': product['id'],
            'name': product_name,
            'quantity': qty,
            'cost': cost
        })
        
        self.po_items_tree.insert("", tk.END, values=(product_name, qty, f"R{cost:.2f}"))
        
        self.po_product_var.set('')
        self.po_qty_entry.delete(0, tk.END)
        self.po_cost_entry.delete(0, tk.END)

    def save_po(self):
        supplier_name = self.po_supplier_var.get()
        if not supplier_name or not self.po_items:
            messagebox.showerror("Error", "Select a supplier and add items.")
            return
            
        supplier = next((s for s in self.suppliers if s['name'] == supplier_name), None)
        if not supplier:
            return
            
        try:
            order_id = create_purchase_order(supplier['id'], self.po_items)
            messagebox.showinfo("Success", f"Purchase Order #{order_id} created.")
            self.po_items = []
            self.po_items_tree.delete(*self.po_items_tree.get_children())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create PO: {e}")

    def receive_po(self):
        try:
            order_id = int(self.receive_po_id.get())
            if receive_purchase_order(order_id, self.current_user['id']):
                messagebox.showinfo("Success", f"Stock received for PO #{order_id}.")
                self.receive_po_id.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to receive PO: {e}")

    def adjust_stock(self):
        product_name = self.adj_product_var.get()
        try:
            change = int(self.adj_qty_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity.")
            return
            
        reason = self.adj_reason_entry.get()
        if not reason:
            messagebox.showerror("Error", "Reason is required.")
            return
            
        product = next((p for p in self.products if p['name'] == product_name), None)
        if not product:
            return
            
        try:
            adjust_stock(product['id'], change, reason, self.current_user['id'])
            messagebox.showinfo("Success", "Stock adjusted.")
            self.adj_product_var.set('')
            self.adj_qty_entry.delete(0, tk.END)
            self.adj_reason_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust stock: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    dummy_user = {'id': 0, 'username': 'test_admin'}
    app = InventoryManagementWindow(root, dummy_user)
    root.withdraw()
    app.mainloop()
