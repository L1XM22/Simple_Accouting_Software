import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import get_all_customers_from_db, get_all_invoices_with_customer_name, get_email_signatures, add_email_signature, delete_email_signature, get_invoice_details
from email_service import send_custom_email
from pdf_service import generate_invoice_pdf
import tempfile
import os

class CommunicationWindow(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Communication Center")
        self.geometry("900x700")
        self.current_user = current_user
        self.attachments = []

        # --- Notebook (Tabs) ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Tab 1: Compose Email ---
        compose_tab = ttk.Frame(notebook)
        notebook.add(compose_tab, text="Compose Email")
        self.create_compose_tab(compose_tab)

        # --- Tab 2: Signatures ---
        signature_tab = ttk.Frame(notebook)
        notebook.add(signature_tab, text="Signatures")
        self.create_signature_tab(signature_tab)

    def create_compose_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # To
        ttk.Label(frame, text="To:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.customers = get_all_customers_from_db()
        customer_emails = [f"{c['name']} <{c['email']}>" for c in self.customers if c['email']]
        self.to_var = tk.StringVar()
        self.to_menu = ttk.Combobox(frame, textvariable=self.to_var, values=customer_emails, width=50)
        self.to_menu.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Subject
        ttk.Label(frame, text="Subject:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.subject_entry = ttk.Entry(frame, width=80)
        self.subject_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Attach Invoice
        ttk.Label(frame, text="Attach Invoice:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.invoices = get_all_invoices_with_customer_name()
        invoice_list = [f"#{inv['id']} - {inv['customer_name']} (R{inv['total_amount']:.2f})" for inv in self.invoices]
        self.invoice_var = tk.StringVar()
        self.invoice_menu = ttk.Combobox(frame, textvariable=self.invoice_var, values=invoice_list, width=50)
        self.invoice_menu.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Other Attachments
        ttk.Label(frame, text="Attachments:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.attachment_label = ttk.Label(frame, text="None")
        self.attachment_label.grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Button(frame, text="Add File", command=self.add_attachment).grid(row=3, column=2, padx=5)
        ttk.Button(frame, text="Clear", command=self.clear_attachments).grid(row=3, column=3, padx=5)

        # Signature Selection
        ttk.Label(frame, text="Signature:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.signatures = get_email_signatures(self.current_user['id'])
        sig_names = [s['name'] for s in self.signatures]
        self.sig_var = tk.StringVar()
        self.sig_menu = ttk.Combobox(frame, textvariable=self.sig_var, values=sig_names, state="readonly")
        self.sig_menu.grid(row=4, column=1, sticky=tk.W, pady=5)
        self.sig_menu.bind("<<ComboboxSelected>>", self.insert_signature)

        # Body
        ttk.Label(frame, text="Message:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.body_text = tk.Text(frame, height=15, width=80)
        self.body_text.grid(row=5, column=1, columnspan=3, sticky=tk.W, pady=5)

        # Send Button
        ttk.Button(frame, text="Send Email", command=self.send_email).grid(row=6, column=1, sticky=tk.E, pady=10)

    def create_signature_tab(self, parent):
        frame = ttk.Frame(parent, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # List
        list_frame = ttk.LabelFrame(frame, text="Your Signatures", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.sig_listbox = tk.Listbox(list_frame, width=30)
        self.sig_listbox.pack(fill=tk.Y, expand=True)
        self.sig_listbox.bind('<<ListboxSelect>>', self.on_sig_select)
        
        ttk.Button(list_frame, text="Delete", command=self.delete_signature).pack(pady=5)

        # Edit
        edit_frame = ttk.LabelFrame(frame, text="Edit Signature", padding="10")
        edit_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(edit_frame, text="Name:").pack(anchor=tk.W)
        self.sig_name_entry = ttk.Entry(edit_frame)
        self.sig_name_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(edit_frame, text="Content:").pack(anchor=tk.W)
        self.sig_content_text = tk.Text(edit_frame, height=10)
        self.sig_content_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        ttk.Button(edit_frame, text="Save Signature", command=self.save_signature).pack(anchor=tk.E)
        
        self.load_signatures()

    def add_attachment(self):
        filenames = filedialog.askopenfilenames()
        if filenames:
            self.attachments.extend(filenames)
            self.update_attachment_label()

    def clear_attachments(self):
        self.attachments = []
        self.update_attachment_label()

    def update_attachment_label(self):
        if not self.attachments:
            self.attachment_label.config(text="None")
        else:
            names = [os.path.basename(f) for f in self.attachments]
            self.attachment_label.config(text=", ".join(names))

    def load_signatures(self):
        self.signatures = get_email_signatures(self.current_user['id'])
        self.sig_listbox.delete(0, tk.END)
        for sig in self.signatures:
            self.sig_listbox.insert(tk.END, sig['name'])
        
        # Update combo in compose tab
        sig_names = [s['name'] for s in self.signatures]
        self.sig_menu['values'] = sig_names

    def on_sig_select(self, event):
        selection = self.sig_listbox.curselection()
        if selection:
            index = selection[0]
            sig = self.signatures[index]
            self.sig_name_entry.delete(0, tk.END)
            self.sig_name_entry.insert(0, sig['name'])
            self.sig_content_text.delete('1.0', tk.END)
            self.sig_content_text.insert('1.0', sig['content'])

    def save_signature(self):
        name = self.sig_name_entry.get()
        content = self.sig_content_text.get('1.0', tk.END).strip()
        
        if not name or not content:
            messagebox.showerror("Error", "Name and content are required.")
            return
            
        add_email_signature(name, content, self.current_user['id'])
        messagebox.showinfo("Success", "Signature saved.")
        self.load_signatures()
        self.sig_name_entry.delete(0, tk.END)
        self.sig_content_text.delete('1.0', tk.END)

    def delete_signature(self):
        selection = self.sig_listbox.curselection()
        if selection:
            index = selection[0]
            sig = self.signatures[index]
            if messagebox.askyesno("Confirm", f"Delete signature '{sig['name']}'?"):
                delete_email_signature(sig['id'])
                self.load_signatures()
                self.sig_name_entry.delete(0, tk.END)
                self.sig_content_text.delete('1.0', tk.END)

    def insert_signature(self, event):
        name = self.sig_var.get()
        sig = next((s for s in self.signatures if s['name'] == name), None)
        if sig:
            self.body_text.insert(tk.END, "\n\n" + sig['content'])

    def send_email(self):
        to_addr_raw = self.to_var.get()
        # Extract email from "Name <email>" format if needed
        if '<' in to_addr_raw:
            to_addr = to_addr_raw.split('<')[1].strip('>')
        else:
            to_addr = to_addr_raw
            
        subject = self.subject_entry.get()
        body = self.body_text.get('1.0', tk.END).strip()
        
        if not to_addr or not subject or not body:
            messagebox.showerror("Error", "To, Subject, and Message are required.")
            return

        files_to_send = list(self.attachments)
        
        # Handle Invoice Attachment
        invoice_selection = self.invoice_var.get()
        temp_invoice_path = None
        if invoice_selection:
            try:
                invoice_id = int(invoice_selection.split(' ')[0].strip('#'))
                invoice_details = get_invoice_details(invoice_id)
                if invoice_details:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_file.close()
                    if generate_invoice_pdf(temp_file.name, invoice_details):
                        temp_invoice_path = temp_file.name
                        files_to_send.append(temp_invoice_path)
            except Exception as e:
                print(f"Error attaching invoice: {e}")

        if send_custom_email(to_addr, subject, body, files_to_send):
            messagebox.showinfo("Success", "Email sent successfully.")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to send email.")
            
        # Cleanup temp invoice
        if temp_invoice_path and os.path.exists(temp_invoice_path):
            os.remove(temp_invoice_path)

if __name__ == '__main__':
    root = tk.Tk()
    dummy_user = {'id': 0, 'username': 'test_admin'}
    app = CommunicationWindow(root, dummy_user)
    root.withdraw()
    app.mainloop()
