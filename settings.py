import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import configparser
import os

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("700x650")

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        # --- Notebook (Tabs) ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Tab 1: SMTP Settings ---
        smtp_tab = ttk.Frame(notebook)
        notebook.add(smtp_tab, text="SMTP Settings")
        self.create_smtp_tab(smtp_tab)

        # --- Tab 2: Email Templates ---
        template_tab = ttk.Frame(notebook)
        notebook.add(template_tab, text="Email Templates")
        self.create_template_tab(template_tab)

        # --- Tab 3: Invoice Template ---
        invoice_tab = ttk.Frame(notebook)
        notebook.add(invoice_tab, text="Invoice Template")
        self.create_invoice_tab(invoice_tab)

        # --- Tab 4: Tax Settings ---
        tax_tab = ttk.Frame(notebook)
        notebook.add(tax_tab, text="Tax Settings")
        self.create_tax_tab(tax_tab)

        # --- Save Button ---
        save_button = ttk.Button(self, text="Save Settings", command=self.save_settings)
        save_button.pack(pady=10)

    def create_smtp_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Server:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.server_var = tk.StringVar(value=self.config.get('SMTP', 'server', fallback=''))
        ttk.Entry(frame, textvariable=self.server_var, width=40).grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(frame, text="Port:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_var = tk.StringVar(value=self.config.get('SMTP', 'port', fallback=''))
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(frame, text="Username:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar(value=self.config.get('SMTP', 'username', fallback=''))
        ttk.Entry(frame, textvariable=self.username_var, width=40).grid(row=2, column=1, sticky=tk.EW)

        ttk.Label(frame, text="Password:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.password_var = tk.StringVar(value=self.config.get('SMTP', 'password', fallback=''))
        ttk.Entry(frame, textvariable=self.password_var, show="*", width=40).grid(row=3, column=1, sticky=tk.EW)

    def create_template_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Invoice Email
        ttk.Label(frame, text="Invoice Email Template", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text="Subject:").pack(anchor=tk.W)
        self.subject_var = tk.StringVar(value=self.config.get('EmailTemplates', 'subject', fallback=''))
        ttk.Entry(frame, textvariable=self.subject_var, width=60).pack(fill=tk.X, pady=(0, 5))
        ttk.Label(frame, text="Body:").pack(anchor=tk.W)
        self.body_text = tk.Text(frame, height=5, width=60)
        self.body_text.pack(fill=tk.X, pady=(0, 10))
        self.body_text.insert('1.0', self.config.get('EmailTemplates', 'body', fallback=''))

        # Quotation Email
        ttk.Label(frame, text="Quotation Email Template", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text="Subject:").pack(anchor=tk.W)
        self.quote_subject_var = tk.StringVar(value=self.config.get('QuotationEmailTemplates', 'subject', fallback=''))
        ttk.Entry(frame, textvariable=self.quote_subject_var, width=60).pack(fill=tk.X, pady=(0, 5))
        ttk.Label(frame, text="Body:").pack(anchor=tk.W)
        self.quote_body_text = tk.Text(frame, height=5, width=60)
        self.quote_body_text.pack(fill=tk.X, pady=(0, 10))
        self.quote_body_text.insert('1.0', self.config.get('QuotationEmailTemplates', 'body', fallback=''))

    def create_invoice_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Logo
        ttk.Label(frame, text="Logo / Watermark Image:").pack(anchor=tk.W, pady=(0, 5))
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X)
        self.logo_path_var = tk.StringVar(value=self.config.get('InvoiceTemplate', 'logo_path', fallback=''))
        ttk.Entry(file_frame, textvariable=self.logo_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(file_frame, text="Browse...", command=self.browse_logo).pack(side=tk.RIGHT)
        
        # Logo Position
        ttk.Label(frame, text="Logo Position:").pack(anchor=tk.W, pady=(10, 5))
        self.logo_pos_var = tk.StringVar(value=self.config.get('InvoiceTemplate', 'logo_position', fallback='Right'))
        ttk.Combobox(frame, textvariable=self.logo_pos_var, values=['Left', 'Center', 'Right'], state="readonly").pack(anchor=tk.W)

        # Logo Width
        ttk.Label(frame, text="Logo Width (inches):").pack(anchor=tk.W, pady=(10, 5))
        width_frame = ttk.Frame(frame)
        width_frame.pack(fill=tk.X)
        self.logo_width_var = tk.DoubleVar(value=float(self.config.get('InvoiceTemplate', 'logo_width', fallback='2.0')))
        scale = ttk.Scale(width_frame, from_=0.5, to=5.0, variable=self.logo_width_var, orient='horizontal')
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        width_label = ttk.Label(width_frame, text=f"{self.logo_width_var.get():.1f}")
        width_label.pack(side=tk.LEFT)
        scale.configure(command=lambda val: width_label.config(text=f"{float(val):.1f}"))

        # Header Title
        ttk.Label(frame, text="Header Title:").pack(anchor=tk.W, pady=(10, 5))
        self.header_title_var = tk.StringVar(value=self.config.get('InvoiceTemplate', 'header_title', fallback='INVOICE'))
        ttk.Entry(frame, textvariable=self.header_title_var).pack(fill=tk.X)

        # Company Info
        ttk.Label(frame, text="Company Information (HTML allowed):").pack(anchor=tk.W, pady=(10, 5))
        self.company_info_text = tk.Text(frame, height=5, width=60)
        self.company_info_text.pack(fill=tk.X)
        default_company_info = """<b>Inter-counting Inc.</b><br/>
123 Accounting Lane<br/>
Your City, State, 12345<br/>
(123) 456-7890"""
        self.company_info_text.insert('1.0', self.config.get('InvoiceTemplate', 'company_info', fallback=default_company_info))

        # Footer Text
        ttk.Label(frame, text="Footer Text:").pack(anchor=tk.W, pady=(10, 5))
        self.footer_text_var = tk.StringVar(value=self.config.get('InvoiceTemplate', 'footer_text', fallback='Thank you for your business!'))
        ttk.Entry(frame, textvariable=self.footer_text_var).pack(fill=tk.X)

    def create_tax_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Tax Name (e.g., VAT, GST):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.tax_name_var = tk.StringVar(value=self.config.get('Tax', 'name', fallback='VAT'))
        ttk.Entry(frame, textvariable=self.tax_name_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frame, text="Tax Rate (%):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.tax_rate_var = tk.DoubleVar(value=float(self.config.get('Tax', 'rate', fallback='15.0')))
        ttk.Entry(frame, textvariable=self.tax_rate_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

    def browse_logo(self):
        filename = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )
        if filename:
            self.logo_path_var.set(filename)

    def save_settings(self):
        # Update SMTP settings
        if not self.config.has_section('SMTP'):
            self.config.add_section('SMTP')
        self.config['SMTP']['server'] = self.server_var.get()
        self.config['SMTP']['port'] = self.port_var.get()
        self.config['SMTP']['username'] = self.username_var.get()
        self.config['SMTP']['password'] = self.password_var.get()

        # Update Email Templates
        if not self.config.has_section('EmailTemplates'):
            self.config.add_section('EmailTemplates')
        self.config['EmailTemplates']['subject'] = self.subject_var.get()
        self.config['EmailTemplates']['body'] = self.body_text.get('1.0', tk.END).strip()
        
        if not self.config.has_section('QuotationEmailTemplates'):
            self.config.add_section('QuotationEmailTemplates')
        self.config['QuotationEmailTemplates']['subject'] = self.quote_subject_var.get()
        self.config['QuotationEmailTemplates']['body'] = self.quote_body_text.get('1.0', tk.END).strip()

        # Update Invoice Template
        if not self.config.has_section('InvoiceTemplate'):
            self.config.add_section('InvoiceTemplate')
        self.config['InvoiceTemplate']['logo_path'] = self.logo_path_var.get()
        self.config['InvoiceTemplate']['logo_position'] = self.logo_pos_var.get()
        self.config['InvoiceTemplate']['logo_width'] = str(self.logo_width_var.get())
        self.config['InvoiceTemplate']['header_title'] = self.header_title_var.get()
        self.config['InvoiceTemplate']['company_info'] = self.company_info_text.get('1.0', tk.END).strip()
        self.config['InvoiceTemplate']['footer_text'] = self.footer_text_var.get()

        # Update Tax Settings
        if not self.config.has_section('Tax'):
            self.config.add_section('Tax')
        self.config['Tax']['name'] = self.tax_name_var.get()
        self.config['Tax']['rate'] = str(self.tax_rate_var.get())

        # Write to file
        try:
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    app = SettingsWindow(root)
    root.withdraw()
    app.mainloop()
