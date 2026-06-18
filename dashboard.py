import tkinter as tk
from tkinter import ttk
from database import get_dashboard_metrics, get_sales_data_for_chart, get_recent_invoices, get_top_products, get_low_stock_products
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Dashboard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="20")
        self.pack(fill=tk.BOTH, expand=True)

        # --- Title ---
        title_label = ttk.Label(self, text="Dashboard Overview", font=("Segoe UI", 24, "bold"))
        title_label.pack(pady=(0, 20), anchor='w')

        # --- Metrics Frame ---
        metrics_frame = ttk.Frame(self)
        metrics_frame.pack(fill=tk.X, pady=(0, 20))
        metrics_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.total_sales_var = tk.StringVar(value="R0.00")
        self.create_metric_card(metrics_frame, "💰 Total Sales", self.total_sales_var, 0)
        
        self.total_expenses_var = tk.StringVar(value="R0.00")
        self.create_metric_card(metrics_frame, "💸 Total Expenses", self.total_expenses_var, 1)
        
        self.net_profit_var = tk.StringVar(value="R0.00")
        self.create_metric_card(metrics_frame, "📈 Net Profit", self.net_profit_var, 2)

        self.invoice_count_var = tk.StringVar(value="0")
        self.create_metric_card(metrics_frame, "📄 Invoices", self.invoice_count_var, 3)
        
        self.total_customers_var = tk.StringVar(value="0")
        self.create_metric_card(metrics_frame, "👥 Customers", self.total_customers_var, 4)
        
        self.total_products_var = tk.StringVar(value="0")
        self.create_metric_card(metrics_frame, "📦 Products", self.total_products_var, 5)

        # --- Middle Section: Chart and Lists ---
        middle_frame = ttk.Frame(self)
        middle_frame.pack(fill=tk.BOTH, expand=True)
        middle_frame.columnconfigure(0, weight=2) # Chart takes more space
        middle_frame.columnconfigure(1, weight=1) # Lists take less space

        # --- Chart Frame ---
        chart_frame = ttk.Frame(middle_frame, style='Card.TFrame', padding=10)
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        ttk.Label(chart_frame, text="Sales Performance (Last 7 Days)", font=("Segoe UI", 12, "bold")).pack(anchor='w', pady=(0, 10))

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.fig.patch.set_facecolor('#F8F9FA') # Match card background
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#F8F9FA')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Lists Frame ---
        lists_frame = ttk.Frame(middle_frame)
        lists_frame.grid(row=0, column=1, sticky="nsew")
        lists_frame.rowconfigure(0, weight=1)
        lists_frame.rowconfigure(1, weight=1)
        lists_frame.rowconfigure(2, weight=1)

        # Recent Invoices
        self.create_list_section(lists_frame, "Recent Invoices", 0)
        self.recent_invoices_tree = ttk.Treeview(self.list_frames[0], columns=("ID", "Customer", "Total"), show="headings", height=3)
        self.setup_tree(self.recent_invoices_tree, ["#", "Customer", "Total"], [40, 120, 80])

        # Top Products
        self.create_list_section(lists_frame, "Top Products", 1)
        self.top_products_tree = ttk.Treeview(self.list_frames[1], columns=("Product", "Sold"), show="headings", height=3)
        self.setup_tree(self.top_products_tree, ["Product", "Sold"], [150, 50])

        # Low Stock Alerts
        self.create_list_section(lists_frame, "⚠️ Low Stock Alerts", 2)
        self.low_stock_tree = ttk.Treeview(self.list_frames[2], columns=("Product", "Qty"), show="headings", height=3)
        self.setup_tree(self.low_stock_tree, ["Product", "Qty"], [150, 50])

        # --- Refresh Button ---
        refresh_button = ttk.Button(self, text="🔄 Refresh Data", command=self.refresh_all)
        refresh_button.pack(pady=20, anchor='e')

        self.refresh_all()

    def create_metric_card(self, parent, title, data_var, column):
        frame = ttk.Frame(parent, style='Card.TFrame', padding=15)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky="ew")
        
        ttk.Label(frame, text=title, font=("Segoe UI", 10), foreground='#7F8C8D').pack(anchor='w')
        ttk.Label(frame, textvariable=data_var, font=("Segoe UI", 18, "bold"), foreground='#2C3E50').pack(anchor='w', pady=(5, 0))

    def create_list_section(self, parent, title, row):
        if not hasattr(self, 'list_frames'):
            self.list_frames = {}
        
        frame = ttk.Frame(parent, style='Card.TFrame', padding=10)
        frame.grid(row=row, column=0, sticky="nsew", pady=(0, 10))
        ttk.Label(frame, text=title, font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=(0, 5))
        self.list_frames[row] = frame

    def setup_tree(self, tree, headers, widths):
        for col, width in zip(tree['columns'], widths):
            tree.heading(col, text=headers[tree['columns'].index(col)])
            tree.column(col, width=width)
            if col == "Total" or col == "Sold" or col == "Qty":
                tree.column(col, anchor='e')
        tree.pack(fill=tk.BOTH, expand=True)

    def refresh_all(self):
        """Refreshes all dashboard components."""
        self.refresh_metrics()
        self.refresh_chart()
        self.refresh_lists()

    def refresh_metrics(self):
        try:
            metrics = get_dashboard_metrics()
            self.total_sales_var.set(f"R{metrics.get('total_sales', 0):,.2f}")
            self.total_expenses_var.set(f"R{metrics.get('total_expenses', 0):,.2f}")
            self.net_profit_var.set(f"R{metrics.get('net_profit', 0):,.2f}")
            self.invoice_count_var.set(str(metrics.get('invoice_count', 0)))
            self.total_customers_var.set(str(metrics.get('total_customers', 0)))
            self.total_products_var.set(str(metrics.get('total_products', 0)))
        except Exception as e:
            print(f"Error refreshing metrics: {e}")

    def refresh_chart(self):
        try:
            sales_data = get_sales_data_for_chart(days=7)
            dates = [d.split('-')[-1] for d in sales_data.keys()]
            sales = sales_data.values()

            self.ax.clear()
            # Remove chart border
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            
            self.ax.bar(dates, sales, color='#3498DB', alpha=0.7)
            self.ax.set_ylabel('Sales (R)')
            self.ax.set_xlabel('Date')
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error refreshing chart: {e}")

    def refresh_lists(self):
        # Refresh Recent Invoices
        for item in self.recent_invoices_tree.get_children():
            self.recent_invoices_tree.delete(item)
        try:
            invoices = get_recent_invoices()
            for inv in invoices:
                self.recent_invoices_tree.insert("", tk.END, values=(inv['id'], inv['customer_name'], f"R{inv['total_amount']:.2f}"))
        except Exception as e:
            print(f"Error refreshing recent invoices: {e}")

        # Refresh Top Products
        for item in self.top_products_tree.get_children():
            self.top_products_tree.delete(item)
        try:
            products = get_top_products()
            for prod in products:
                self.top_products_tree.insert("", tk.END, values=(prod['name'], prod['total_sold']))
        except Exception as e:
            print(f"Error refreshing top products: {e}")

        # Refresh Low Stock
        for item in self.low_stock_tree.get_children():
            self.low_stock_tree.delete(item)
        try:
            products = get_low_stock_products()
            for prod in products:
                self.low_stock_tree.insert("", tk.END, values=(prod['name'], prod['quantity']))
        except Exception as e:
            print(f"Error refreshing low stock: {e}")


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Dashboard Test")
    root.geometry("1000x700")
    dashboard_frame = Dashboard(root)
    root.mainloop()
