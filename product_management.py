import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from database import (
    add_product_to_db,
    get_all_products_from_db,
    update_product_in_db,
    delete_product_from_db,
)
from theme import apply_theme

class ProductManagementWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Product/Service Management")
        self.geometry("700x500")
        
        # Apply theme with Orange accent
        apply_theme(self, accent_color='#D35400')

        # --- Top frame for actions ---
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        top_frame.pack(fill=tk.X)
        
        import_button = ttk.Button(top_frame, text="Import from CSV", command=self.import_from_csv)
        import_button.pack(side=tk.RIGHT)

        # --- Main content frame ---
        content_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for the product list
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.product_listbox = tk.Listbox(left_frame)
        self.product_listbox.pack(fill=tk.BOTH, expand=True)
        self.product_listbox.bind('<<ListboxSelect>>', self.on_product_select)

        # Right frame for the product details
        right_frame = ttk.LabelFrame(content_frame, text="Product Details")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, ipadx=10, ipady=10)

        ttk.Label(right_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(right_frame)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(right_frame, text="Item Code:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.code_entry = ttk.Entry(right_frame)
        self.code_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Label(right_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.description_entry = ttk.Entry(right_frame)
        self.description_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)

        ttk.Label(right_frame, text="Price:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.price_entry = ttk.Entry(right_frame)
        self.price_entry.grid(row=3, column=1, sticky=tk.EW, pady=2)

        ttk.Label(right_frame, text="Quantity:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.quantity_entry = ttk.Entry(right_frame)
        self.quantity_entry.grid(row=4, column=1, sticky=tk.EW, pady=2)

        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Add", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update", command=self.update_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_product).pack(side=tk.LEFT, padx=5)

        self.load_products()

    def load_products(self):
        self.products = get_all_products_from_db()
        self.product_listbox.delete(0, tk.END)
        for product in self.products:
            display_text = product['name']
            if product.get('item_code'):
                display_text += f" ({product['item_code']})"
            self.product_listbox.insert(tk.END, display_text)

    def on_product_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            product = self.products[index]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, product['name'])
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, product.get('item_code', ''))
            self.description_entry.delete(0, tk.END)
            self.description_entry.insert(0, product['description'])
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, str(product['price']))
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, str(product.get('quantity_in_stock', 0)))

    def add_product(self):
        try:
            price = float(self.price_entry.get())
            quantity = int(self.quantity_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Price and Quantity must be numbers.")
            return

        add_product_to_db(
            self.name_entry.get(),
            self.description_entry.get(),
            price,
            quantity,
            self.code_entry.get()
        )
        self.load_products()
        self.clear_entries()

    def update_product(self):
        selection = self.product_listbox.curselection()
        if selection:
            try:
                price = float(self.price_entry.get())
                quantity = int(self.quantity_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Price and Quantity must be numbers.")
                return

            index = selection[0]
            product_id = self.products[index]['id']
            update_product_in_db(
                product_id,
                self.name_entry.get(),
                self.description_entry.get(),
                price,
                quantity,
                self.code_entry.get()
            )
            self.load_products()
            self.clear_entries()

    def delete_product(self):
        selection = self.product_listbox.curselection()
        if selection:
            index = selection[0]
            product_id = self.products[index]['id']
            delete_product_from_db(product_id)
            self.load_products()
            self.clear_entries()

    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.code_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)

    def import_from_csv(self):
        """Imports products from a CSV file."""
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
                    if 'name' in row and 'price' in row:
                        try:
                            price = float(row['price'])
                            quantity = int(row.get('quantity', 0))
                            add_product_to_db(
                                row['name'],
                                row.get('description', ''),
                                price,
                                quantity,
                                row.get('item_code', '')
                            )
                            count += 1
                        except ValueError:
                            continue # Skip invalid rows
            
            messagebox.showinfo("Success", f"Successfully imported {count} products.")
            self.load_products()
        except Exception as e:
            messagebox.showerror("Import Error", f"An error occurred: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ProductManagementWindow(root)
    root.withdraw()
    app.mainloop()
