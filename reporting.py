import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from database import get_all_invoices_with_customer_name, get_invoice_details
from email_service import send_invoice_email
from invoice_details_window import InvoiceDetailsWindow

class ReportingWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Invoice Reports")
        self.geometry("900x600")

        # --- Top Frame for buttons ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X)

        send_email_button = ttk.Button(top_frame, text="Send Email", command=self.send_selected_invoice)
        send_email_button.pack(side=tk.LEFT, padx=(0, 5))
        
        export_csv_button = ttk.Button(top_frame, text="Export to CSV", command=self.export_to_csv)
        export_csv_button.pack(side=tk.LEFT, padx=(0, 5))
        
        tax_report_button = ttk.Button(top_frame, text="Tax Report", command=self.generate_tax_report)
        tax_report_button.pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text="Double-click an invoice to see details").pack(side=tk.RIGHT, padx=10)

        # --- Treeview to display invoices ---
        tree_frame = ttk.Frame(self, padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Customer", "Date", "Due Date", "Total", "Status"),
            show="headings"
        )
        self.tree.heading("ID", text="Invoice ID")
        self.tree.heading("Customer", text="Customer")
        self.tree.heading("Date", text="Invoice Date")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Total", text="Total Amount")
        self.tree.heading("Status", text="Status")

        self.tree.column("ID", width=80)
        self.tree.column("Customer", width=200)
        self.tree.column("Date", width=120)
        self.tree.column("Due Date", width=120)
        self.tree.column("Total", width=120, anchor=tk.E)
        self.tree.column("Status", width=100)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

        self.load_invoices()

    def load_invoices(self):
        self.invoices = get_all_invoices_with_customer_name()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for inv in self.invoices:
            self.tree.insert("", tk.END, values=(
                inv['id'], inv['customer_name'], inv['invoice_date'],
                inv['due_date'], f"R{inv['total_amount']:.2f}", inv['status']
            ))

    def on_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        invoice_id = self.tree.item(item_id)['values'][0]
        InvoiceDetailsWindow(self, invoice_id)

    def send_selected_invoice(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an invoice to send.")
            return
        invoice_id = self.tree.item(selected_item)['values'][0]
        try:
            invoice_details = get_invoice_details(invoice_id)
            if not invoice_details:
                messagebox.showerror("Error", f"Could not find details for invoice ID {invoice_id}.")
                return
            confirm = messagebox.askyesno("Confirm Email", f"Send invoice #{invoice_id} to {invoice_details.get('customer_email')}?")
            if not confirm: return
            success = send_invoice_email(invoice_details)
            if success:
                messagebox.showinfo("Email Sent", "The invoice was sent successfully.")
            else:
                messagebox.showerror("Email Failed", "Failed to send the invoice email. Check the console for errors.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def export_to_csv(self):
        """Exports the current list of invoices to a CSV file."""
        if not self.invoices:
            messagebox.showinfo("Export", "There are no invoices to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="invoices.csv"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.invoices[0].keys())
                writer.writeheader()
                writer.writerows(self.invoices)
            messagebox.showinfo("Success", f"Invoice data exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred: {e}")

    def generate_tax_report(self):
        """Generates a CSV report of tax collected."""
        # For simplicity, we'll just export all invoices with their tax amounts
        # In a real app, you'd want date filtering here.
        
        # We need to fetch full details to get tax amounts, as the list view doesn't have it
        # This might be slow for many invoices, but okay for now.
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="tax_report.csv"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Invoice ID', 'Date', 'Customer', 'Total Amount', 'Tax Amount'])
                
                for inv in self.invoices:
                    details = get_invoice_details(inv['id'])
                    if details:
                        writer.writerow([
                            details['id'],
                            details['invoice_date'],
                            details['customer_name'],
                            details['total_amount'],
                            details.get('tax_amount', 0)
                        ])
            messagebox.showinfo("Success", f"Tax report generated successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ReportingWindow(root)
    root.withdraw()
    app.mainloop()
