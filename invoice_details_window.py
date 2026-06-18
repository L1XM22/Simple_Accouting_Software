import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from database import get_invoice_details, record_payment
from pdf_service import generate_invoice_pdf, print_invoice

class InvoiceDetailsWindow(tk.Toplevel):
    def __init__(self, parent, invoice_id):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.title(f"Invoice Details #{self.invoice_id}")
        self.geometry("800x600")

        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.load_details()

    def load_details(self):
        # Clear existing widgets before loading
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        try:
            self.invoice = get_invoice_details(self.invoice_id)
            if not self.invoice:
                messagebox.showerror("Error", f"Could not load details for invoice ID {self.invoice_id}.")
                self.destroy()
                return
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.destroy()
            return

        # --- Top section with two columns ---
        top_section = ttk.Frame(self.main_frame)
        top_section.pack(fill=tk.X, pady=(0, 20))
        top_section.columnconfigure(0, weight=1)
        top_section.columnconfigure(1, weight=1)

        # --- Customer & Invoice Info ---
        info_frame = ttk.Frame(top_section)
        info_frame.grid(row=0, column=0, sticky="ew")
        info_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(3, weight=1)

        ttk.Label(info_frame, text="Customer:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.invoice['customer_name']).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(info_frame, text="Invoice Date:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Label(info_frame, text=self.invoice['invoice_date']).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(info_frame, text="Address:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.invoice['customer_address']).grid(row=1, column=1, sticky=tk.W)
        ttk.Label(info_frame, text="Due Date:", font=("Helvetica", 10, "bold")).grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Label(info_frame, text=self.invoice['due_date']).grid(row=1, column=3, sticky=tk.W)
        
        # --- Payment Summary ---
        payment_summary_frame = ttk.Frame(top_section)
        payment_summary_frame.grid(row=0, column=1, sticky="ew", padx=(20, 0))
        
        balance_due = self.invoice['total_amount'] - self.invoice['amount_paid']
        tax_amount = self.invoice.get('tax_amount', 0)
        subtotal = self.invoice['total_amount'] - tax_amount
        
        ttk.Label(payment_summary_frame, text="Subtotal:", font=("Helvetica", 10)).pack(anchor=tk.E)
        ttk.Label(payment_summary_frame, text=f"R{subtotal:.2f}", font=("Helvetica", 10, "bold")).pack(anchor=tk.E)
        
        if tax_amount > 0:
            ttk.Label(payment_summary_frame, text="Tax:", font=("Helvetica", 10)).pack(anchor=tk.E)
            ttk.Label(payment_summary_frame, text=f"R{tax_amount:.2f}", font=("Helvetica", 10, "bold")).pack(anchor=tk.E)
        
        ttk.Label(payment_summary_frame, text="Total:", font=("Helvetica", 10)).pack(anchor=tk.E)
        ttk.Label(payment_summary_frame, text=f"R{self.invoice['total_amount']:.2f}", font=("Helvetica", 10, "bold")).pack(anchor=tk.E)
        
        ttk.Label(payment_summary_frame, text="Paid:", font=("Helvetica", 10)).pack(anchor=tk.E)
        ttk.Label(payment_summary_frame, text=f"R{self.invoice['amount_paid']:.2f}", font=("Helvetica", 10, "bold")).pack(anchor=tk.E)

        ttk.Label(payment_summary_frame, text="Balance Due:", font=("Helvetica", 10)).pack(anchor=tk.E)
        ttk.Label(payment_summary_frame, text=f"R{balance_due:.2f}", font=("Helvetica", 12, "bold")).pack(anchor=tk.E)

        # --- Middle section with two columns ---
        middle_section = ttk.Frame(self.main_frame)
        middle_section.pack(fill=tk.BOTH, expand=True)
        middle_section.columnconfigure(0, weight=2)
        middle_section.columnconfigure(1, weight=1)

        # --- Items Treeview ---
        items_frame = ttk.LabelFrame(middle_section, text="Invoice Items", padding="10")
        items_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tree = ttk.Treeview(items_frame, columns=("Product", "Quantity", "Price", "Total"), show="headings")
        tree.heading("Product", text="Product")
        tree.heading("Quantity", text="Quantity")
        tree.heading("Price", text="Unit Price")
        tree.heading("Total", text="Line Total")
        tree.column("Quantity", width=80, anchor=tk.CENTER)
        tree.column("Price", width=100, anchor=tk.E)
        tree.column("Total", width=100, anchor=tk.E)
        tree.pack(fill=tk.BOTH, expand=True)

        for item in self.invoice['items']:
            line_total = item['quantity'] * item['unit_price']
            tree.insert("", tk.END, values=(
                item['product_name'], item['quantity'],
                f"R{item['unit_price']:.2f}", f"R{line_total:.2f}"
            ))

        # --- Payments Treeview ---
        payments_frame = ttk.LabelFrame(middle_section, text="Payment History", padding="10")
        payments_frame.grid(row=0, column=1, sticky="nsew")

        payments_tree = ttk.Treeview(payments_frame, columns=("Date", "Amount", "Method"), show="headings")
        payments_tree.heading("Date", text="Date")
        payments_tree.heading("Amount", text="Amount")
        payments_tree.heading("Method", text="Method")
        payments_tree.column("Date", width=80)
        payments_tree.column("Amount", width=80, anchor=tk.E)
        payments_tree.column("Method", width=100)
        payments_tree.pack(fill=tk.BOTH, expand=True)

        for pmt in self.invoice['payments']:
            payments_tree.insert("", tk.END, values=(
                pmt['date'], f"R{pmt['amount']:.2f}", pmt['method']
            ))

        # --- Bottom Frame for Buttons ---
        bottom_frame = ttk.Frame(self.main_frame, padding="10")
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="Print", command=self.print_invoice).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom_frame, text="Export to PDF", command=self.export_pdf).pack(side=tk.LEFT)
        
        if balance_due > 0:
            ttk.Button(bottom_frame, text="Record Payment", command=self.record_payment_dialog).pack(side=tk.LEFT, padx=10)

    def record_payment_dialog(self):
        amount = simpledialog.askfloat("Record Payment", "Enter payment amount:", parent=self)
        if amount is None or amount <= 0:
            return
            
        method = simpledialog.askstring("Record Payment", "Enter payment method (e.g., 'Credit Card', 'Cash'):", parent=self)
        if not method:
            return

        if record_payment(self.invoice_id, amount, method):
            messagebox.showinfo("Success", "Payment recorded successfully.")
            self.load_details() # Refresh the window
        else:
            messagebox.showerror("Error", "Failed to record payment.")

    def export_pdf(self):
        suggested_filename = f"Invoice_{self.invoice['id']}_{self.invoice['customer_name']}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            initialfile=suggested_filename
        )
        if not file_path:
            return
        if generate_invoice_pdf(file_path, self.invoice):
            messagebox.showinfo("Success", f"Invoice exported to:\n{file_path}")
        else:
            messagebox.showerror("Error", "Failed to generate PDF.")

    def print_invoice(self):
        if print_invoice(self.invoice):
            messagebox.showinfo("Success", "Invoice sent to printer.")
        else:
            messagebox.showerror("Error", "Failed to print invoice.")

if __name__ == '__main__':
    TEST_INVOICE_ID = 1 
    root = tk.Tk()
    root.withdraw()
    app = InvoiceDetailsWindow(parent=root, invoice_id=TEST_INVOICE_ID)
    app.mainloop()
