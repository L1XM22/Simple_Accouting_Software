import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import (
    get_all_quotations, get_all_sales_orders, get_all_invoices_with_customer_name,
    convert_quotation_to_sales_order, convert_sales_order_to_invoice,
    get_quotation_details, get_sales_order_details, get_invoice_details
)
from quotation_creation import QuotationCreationWindow
from sales_order_creation import SalesOrderCreationWindow
from invoice_creation import InvoiceCreationWindow
from invoice_details_window import InvoiceDetailsWindow
from pdf_service import generate_quotation_pdf, generate_sales_order_pdf, generate_invoice_pdf
from email_service import send_quotation_email, send_invoice_email

class DocumentListingWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sales Documents")
        self.geometry("900x600")

        # --- Notebook (Tabs) ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Tab 1: Quotations ---
        quotation_tab = ttk.Frame(notebook)
        notebook.add(quotation_tab, text="Quotations")
        self.create_quotation_tab(quotation_tab)

        # --- Tab 2: Sales Orders ---
        sales_order_tab = ttk.Frame(notebook)
        notebook.add(sales_order_tab, text="Sales Orders")
        self.create_sales_order_tab(sales_order_tab)

        # --- Tab 3: Invoices ---
        invoice_tab = ttk.Frame(notebook)
        notebook.add(invoice_tab, text="Invoices")
        self.create_invoice_tab(invoice_tab)

    def create_quotation_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview
        self.quotation_tree = ttk.Treeview(frame, columns=("ID", "Customer", "Date", "Total", "Status"), show="headings")
        self.quotation_tree.heading("ID", text="ID")
        self.quotation_tree.heading("Customer", text="Customer")
        self.quotation_tree.heading("Date", text="Date")
        self.quotation_tree.heading("Total", text="Total")
        self.quotation_tree.heading("Status", text="Status")
        
        self.quotation_tree.column("ID", width=50)
        self.quotation_tree.column("Customer", width=200)
        self.quotation_tree.column("Date", width=100)
        self.quotation_tree.column("Total", width=100, anchor=tk.E)
        self.quotation_tree.column("Status", width=100)
        
        self.quotation_tree.pack(fill=tk.BOTH, expand=True)

        # Actions
        btn_frame = ttk.Frame(frame, padding=(0, 10, 0, 0))
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Create Quotation", command=self.create_quotation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Convert to Sales Order", command=self.convert_quotation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Export to PDF", command=self.export_quotation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Email Quotation", command=self.email_quotation).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Refresh", command=self.load_quotations).pack(side=tk.RIGHT)

        self.load_quotations()

    def create_sales_order_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview
        self.sales_order_tree = ttk.Treeview(frame, columns=("ID", "Customer", "Date", "Total", "Status"), show="headings")
        self.sales_order_tree.heading("ID", text="ID")
        self.sales_order_tree.heading("Customer", text="Customer")
        self.sales_order_tree.heading("Date", text="Date")
        self.sales_order_tree.heading("Total", text="Total")
        self.sales_order_tree.heading("Status", text="Status")
        
        self.sales_order_tree.column("ID", width=50)
        self.sales_order_tree.column("Customer", width=200)
        self.sales_order_tree.column("Date", width=100)
        self.sales_order_tree.column("Total", width=100, anchor=tk.E)
        self.sales_order_tree.column("Status", width=100)
        
        self.sales_order_tree.pack(fill=tk.BOTH, expand=True)

        # Actions
        btn_frame = ttk.Frame(frame, padding=(0, 10, 0, 0))
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Create Sales Order", command=self.create_sales_order).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Convert to Invoice", command=self.convert_sales_order).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Export to PDF", command=self.export_sales_order).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Refresh", command=self.load_sales_orders).pack(side=tk.RIGHT)

        self.load_sales_orders()

    def create_invoice_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview
        self.invoice_tree = ttk.Treeview(frame, columns=("ID", "Customer", "Date", "Total", "Status"), show="headings")
        self.invoice_tree.heading("ID", text="ID")
        self.invoice_tree.heading("Customer", text="Customer")
        self.invoice_tree.heading("Date", text="Date")
        self.invoice_tree.heading("Total", text="Total")
        self.invoice_tree.heading("Status", text="Status")
        
        self.invoice_tree.column("ID", width=50)
        self.invoice_tree.column("Customer", width=200)
        self.invoice_tree.column("Date", width=100)
        self.invoice_tree.column("Total", width=100, anchor=tk.E)
        self.invoice_tree.column("Status", width=100)
        
        self.invoice_tree.pack(fill=tk.BOTH, expand=True)
        self.invoice_tree.bind("<Double-1>", self.on_invoice_double_click)

        # Actions
        btn_frame = ttk.Frame(frame, padding=(0, 10, 0, 0))
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Create Invoice", command=self.create_invoice).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Export to PDF", command=self.export_invoice).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Email Invoice", command=self.email_invoice).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Refresh", command=self.load_invoices).pack(side=tk.RIGHT)

        self.load_invoices()

    def load_quotations(self):
        for item in self.quotation_tree.get_children():
            self.quotation_tree.delete(item)
        
        quotations = get_all_quotations()
        for q in quotations:
            self.quotation_tree.insert("", tk.END, values=(
                q['id'], q['customer_name'], q['date'], f"R{q['total']:.2f}", q['status']
            ))

    def load_sales_orders(self):
        for item in self.sales_order_tree.get_children():
            self.sales_order_tree.delete(item)
        
        orders = get_all_sales_orders()
        for o in orders:
            self.sales_order_tree.insert("", tk.END, values=(
                o['id'], o['customer_name'], o['date'], f"R{o['total']:.2f}", o['status']
            ))

    def load_invoices(self):
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)
        
        invoices = get_all_invoices_with_customer_name()
        for i in invoices:
            self.invoice_tree.insert("", tk.END, values=(
                i['id'], i['customer_name'], i['invoice_date'], f"R{i['total_amount']:.2f}", i['status']
            ))

    def create_quotation(self):
        QuotationCreationWindow(self)

    def create_sales_order(self):
        SalesOrderCreationWindow(self)

    def create_invoice(self):
        InvoiceCreationWindow(self)

    def on_invoice_double_click(self, event):
        item_id = self.invoice_tree.focus()
        if not item_id: return
        invoice_id = self.invoice_tree.item(item_id)['values'][0]
        InvoiceDetailsWindow(self, invoice_id)

    def convert_quotation(self):
        selected = self.quotation_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a quotation to convert.")
            return
        
        item = self.quotation_tree.item(selected[0])
        quotation_id = item['values'][0]
        status = item['values'][4]
        
        if status == 'Converted':
            messagebox.showinfo("Info", "This quotation has already been converted.")
            return

        if messagebox.askyesno("Confirm", f"Convert Quotation #{quotation_id} to Sales Order?"):
            try:
                order_id = convert_quotation_to_sales_order(quotation_id)
                messagebox.showinfo("Success", f"Sales Order #{order_id} created successfully.")
                self.load_quotations()
                self.load_sales_orders()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to convert quotation: {e}")

    def convert_sales_order(self):
        selected = self.sales_order_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a sales order to convert.")
            return
        
        item = self.sales_order_tree.item(selected[0])
        order_id = item['values'][0]
        status = item['values'][4]
        
        if status == 'Invoiced':
            messagebox.showinfo("Info", "This sales order has already been invoiced.")
            return

        if messagebox.askyesno("Confirm", f"Convert Sales Order #{order_id} to Invoice?"):
            try:
                invoice_id = convert_sales_order_to_invoice(order_id)
                messagebox.showinfo("Success", f"Invoice #{invoice_id} created successfully.")
                self.load_sales_orders()
                self.load_invoices()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to convert sales order: {e}")

    def export_quotation(self):
        selected = self.quotation_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a quotation to export.")
            return
        
        item = self.quotation_tree.item(selected[0])
        quotation_id = item['values'][0]
        customer_name = item['values'][1]
        
        try:
            details = get_quotation_details(quotation_id)
            if not details:
                messagebox.showerror("Error", "Could not load quotation details.")
                return
                
            suggested_filename = f"Quotation_{quotation_id}_{customer_name}.pdf"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
                initialfile=suggested_filename
            )
            if not file_path:
                return
                
            if generate_quotation_pdf(file_path, details):
                messagebox.showinfo("Success", f"Quotation exported to:\n{file_path}")
            else:
                messagebox.showerror("Error", "Failed to generate PDF.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def export_sales_order(self):
        selected = self.sales_order_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a sales order to export.")
            return
        
        item = self.sales_order_tree.item(selected[0])
        order_id = item['values'][0]
        customer_name = item['values'][1]
        
        try:
            details = get_sales_order_details(order_id)
            if not details:
                messagebox.showerror("Error", "Could not load sales order details.")
                return
                
            suggested_filename = f"SalesOrder_{order_id}_{customer_name}.pdf"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
                initialfile=suggested_filename
            )
            if not file_path:
                return
                
            if generate_sales_order_pdf(file_path, details):
                messagebox.showinfo("Success", f"Sales Order exported to:\n{file_path}")
            else:
                messagebox.showerror("Error", "Failed to generate PDF.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def export_invoice(self):
        selected = self.invoice_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an invoice to export.")
            return
        
        item = self.invoice_tree.item(selected[0])
        invoice_id = item['values'][0]
        customer_name = item['values'][1]
        
        try:
            details = get_invoice_details(invoice_id)
            if not details:
                messagebox.showerror("Error", "Could not load invoice details.")
                return
                
            suggested_filename = f"Invoice_{invoice_id}_{customer_name}.pdf"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
                initialfile=suggested_filename
            )
            if not file_path:
                return
                
            if generate_invoice_pdf(file_path, details):
                messagebox.showinfo("Success", f"Invoice exported to:\n{file_path}")
            else:
                messagebox.showerror("Error", "Failed to generate PDF.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def email_quotation(self):
        selected = self.quotation_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a quotation to email.")
            return
        
        item = self.quotation_tree.item(selected[0])
        quotation_id = item['values'][0]
        
        try:
            details = get_quotation_details(quotation_id)
            if not details:
                messagebox.showerror("Error", "Could not load quotation details.")
                return
            
            if not details.get('customer_email'):
                messagebox.showerror("Error", "This customer does not have an email address.")
                return

            if messagebox.askyesno("Confirm", f"Email Quotation #{quotation_id} to {details['customer_email']}?"):
                if send_quotation_email(details):
                    messagebox.showinfo("Success", "Quotation emailed successfully.")
                else:
                    messagebox.showerror("Error", "Failed to send email. Check console for details.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def email_invoice(self):
        selected = self.invoice_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an invoice to email.")
            return
        
        item = self.invoice_tree.item(selected[0])
        invoice_id = item['values'][0]
        
        try:
            details = get_invoice_details(invoice_id)
            if not details:
                messagebox.showerror("Error", "Could not load invoice details.")
                return
            
            if not details.get('customer_email'):
                messagebox.showerror("Error", "This customer does not have an email address.")
                return

            if messagebox.askyesno("Confirm", f"Email Invoice #{invoice_id} to {details['customer_email']}?"):
                if send_invoice_email(details):
                    messagebox.showinfo("Success", "Invoice emailed successfully.")
                else:
                    messagebox.showerror("Error", "Failed to send email. Check console for details.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = DocumentListingWindow(root)
    root.withdraw()
    app.mainloop()
