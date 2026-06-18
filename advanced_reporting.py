import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from database import get_profit_loss_data
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import date, timedelta

class AdvancedReportingWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Advanced Reporting - Profit & Loss")
        self.geometry("800x600")

        # --- Top Frame: Date Selection ---
        top_frame = ttk.LabelFrame(self, text="Select Period", padding="10")
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.start_date_entry = DateEntry(top_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date_entry.set_date(date.today() - timedelta(days=30))
        self.start_date_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
        self.end_date_entry = DateEntry(top_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(top_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=10)

        # --- Report Content ---
        self.report_frame = ttk.Frame(self, padding="20")
        self.report_frame.pack(fill=tk.BOTH, expand=True)

        # Summary Section
        summary_frame = ttk.LabelFrame(self.report_frame, text="Summary", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 20))

        self.income_label = ttk.Label(summary_frame, text="Total Income: R0.00", font=("Segoe UI", 12))
        self.income_label.pack(anchor=tk.W)
        
        self.expenses_label = ttk.Label(summary_frame, text="Total Expenses: R0.00", font=("Segoe UI", 12))
        self.expenses_label.pack(anchor=tk.W)
        
        self.profit_label = ttk.Label(summary_frame, text="Net Profit: R0.00", font=("Segoe UI", 14, "bold"))
        self.profit_label.pack(anchor=tk.W, pady=(10, 0))

        # Expense Breakdown
        breakdown_frame = ttk.LabelFrame(self.report_frame, text="Expense Breakdown", padding="10")
        breakdown_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(breakdown_frame, columns=("Category", "Amount"), show="headings")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount")
        self.tree.column("Category", width=200)
        self.tree.column("Amount", width=100, anchor=tk.E)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Bottom Frame: Export ---
        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="Export to PDF", command=self.export_pdf).pack(side=tk.RIGHT)

        self.current_data = None

    def generate_report(self):
        start_date = self.start_date_entry.get_date()
        end_date = self.end_date_entry.get_date()
        
        try:
            data = get_profit_loss_data(start_date, end_date)
            self.current_data = data
            self.current_data['start_date'] = start_date
            self.current_data['end_date'] = end_date
            
            self.income_label.config(text=f"Total Income: R{data['total_income']:.2f}")
            self.expenses_label.config(text=f"Total Expenses: R{data['total_expenses']:.2f}")
            
            profit_color = 'green' if data['net_profit'] >= 0 else 'red'
            self.profit_label.config(text=f"Net Profit: R{data['net_profit']:.2f}", foreground=profit_color)
            
            # Clear tree
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            for item in data['expense_breakdown']:
                self.tree.insert("", tk.END, values=(item['category'], f"R{item['amount']:.2f}"))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def export_pdf(self):
        if not self.current_data:
            messagebox.showwarning("Warning", "Please generate a report first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            initialfile=f"Profit_Loss_{self.current_data['start_date']}_to_{self.current_data['end_date']}.pdf"
        )
        
        if not file_path:
            return
            
        try:
            doc = SimpleDocTemplate(file_path)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph("<b>Profit & Loss Statement</b>", styles['h1']))
            story.append(Paragraph(f"Period: {self.current_data['start_date']} to {self.current_data['end_date']}", styles['Normal']))
            story.append(Spacer(1, 0.25 * inch))
            
            # Summary Table
            summary_data = [
                ['Total Income', f"R{self.current_data['total_income']:.2f}"],
                ['Total Expenses', f"R{self.current_data['total_expenses']:.2f}"],
                ['Net Profit', f"R{self.current_data['net_profit']:.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'), # Bold Net Profit row
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.25 * inch))
            
            # Expense Breakdown
            story.append(Paragraph("<b>Expense Breakdown</b>", styles['h2']))
            
            expense_data = [['Category', 'Amount']]
            for item in self.current_data['expense_breakdown']:
                expense_data.append([item['category'], f"R{item['amount']:.2f}"])
                
            expense_table = Table(expense_data, colWidths=[3*inch, 2*inch])
            expense_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), # Header
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ]))
            story.append(expense_table)
            
            doc.build(story)
            messagebox.showinfo("Success", f"Report exported to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = AdvancedReportingWindow(root)
    root.withdraw()
    app.mainloop()
