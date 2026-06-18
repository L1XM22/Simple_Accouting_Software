from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
import tempfile
import configparser
import win32print
import win32api
import tkinter as tk
from tkinter import ttk, simpledialog

def generate_pdf(file_path, details, document_type="INVOICE"):
    """Generates a PDF document (Invoice, Quotation, Sales Order) from the given details."""
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    story = []
    
    config = configparser.ConfigParser()
    config.read('config.ini')

    # --- Logo ---
    logo_path = config.get('InvoiceTemplate', 'logo_path', fallback='')
    logo_pos = config.get('InvoiceTemplate', 'logo_position', fallback='Right').upper()
    logo_width_inch = float(config.get('InvoiceTemplate', 'logo_width', fallback='2.0'))
    
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path)
            img_width = img.drawWidth
            img_height = img.drawHeight
            
            # Calculate height based on aspect ratio
            aspect_ratio = img_height / img_width
            target_width = logo_width_inch * inch
            target_height = target_width * aspect_ratio
            
            img.drawWidth = target_width
            img.drawHeight = target_height
                
            logo_table = Table([[img]], colWidths=[6 * inch])
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), logo_pos),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            story.append(logo_table)
            story.append(Spacer(1, 0.1 * inch))
        except Exception as e:
            print(f"Failed to load logo: {e}")

    # --- Header ---
    if document_type == "INVOICE":
        header_title = config.get('InvoiceTemplate', 'header_title', fallback='INVOICE')
    else:
        header_title = document_type
        
    header_text = Paragraph(f"<b>{header_title}</b>", styles['h1'])
    story.append(header_text)
    story.append(Spacer(1, 0.25 * inch))

    # --- Company & Customer Info ---
    default_company_info = """
    <b>Inter-counting Inc.</b><br/>
    123 Accounting Lane<br/>
    Your City, State, 12345<br/>
    (123) 456-7890
    """
    company_info = config.get('InvoiceTemplate', 'company_info', fallback=default_company_info)
    
    customer_code_str = f" ({details.get('customer_code', '')})" if details.get('customer_code') else ""
    
    customer_info = f"""
    <b>BILL TO:</b><br/>
    {details['customer_name']}{customer_code_str}<br/>
    {details['customer_address']}<br/>
    {details['customer_email']}
    """
    info_table_data = [
        [Paragraph(company_info, styles['Normal']), Paragraph(customer_info, styles['Normal'])]
    ]
    info_table = Table(info_table_data, colWidths=[3 * inch, 3 * inch])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 0.25 * inch))

    # --- Metadata ---
    if document_type == "INVOICE":
        meta_data = [
            ['Invoice #:', details['id']],
            ['Invoice Date:', details['invoice_date']],
            ['Due Date:', details['due_date']],
        ]
    elif document_type == "QUOTATION":
        meta_data = [
            ['Quotation #:', details['id']],
            ['Date:', details['date']],
            ['Expiry Date:', details['expiry_date']],
        ]
    elif document_type == "SALES ORDER":
        meta_data = [
            ['Order #:', details['id']],
            ['Order Date:', details['date']],
            ['Status:', details['status']],
        ]
        
    meta_table = Table(meta_data, colWidths=[1.5*inch, 2*inch], hAlign='LEFT')
    story.append(meta_table)
    story.append(Spacer(1, 0.25 * inch))

    # --- Items Table ---
    items_header = [
        Paragraph("<b>Code</b>", styles['Normal']),
        Paragraph("<b>Product/Service</b>", styles['Normal']),
        Paragraph("<b>Quantity</b>", styles['Normal']),
        Paragraph("<b>Unit Price</b>", styles['Normal']),
        Paragraph("<b>Total</b>", styles['Normal']),
    ]
    items_data = [items_header]
    
    total_amount = details.get('total_amount', details.get('total', 0))
    tax_amount = details.get('tax_amount', 0)
    subtotal = total_amount - tax_amount
    
    for item in details['items']:
        line_total = item['quantity'] * item['unit_price']
        items_data.append([
            item.get('item_code', ''),
            item['product_name'],
            str(item['quantity']),
            f"R{item['unit_price']:.2f}",
            f"R{line_total:.2f}"
        ])
    
    # --- Totals ---
    # Only show tax breakdown for invoices if tax > 0
    if document_type == "INVOICE" and tax_amount > 0:
        tax_name = config.get('Tax', 'name', fallback='Tax')
        items_data.append(['', '', '', Paragraph("<b>Subtotal:</b>", styles['Normal']), Paragraph(f"<b>R{subtotal:.2f}</b>", styles['Normal'])])
        items_data.append(['', '', '', Paragraph(f"<b>{tax_name}:</b>", styles['Normal']), Paragraph(f"<b>R{tax_amount:.2f}</b>", styles['Normal'])])
        
    items_data.append(['', '', '', Paragraph("<b>Total:</b>", styles['Normal']), Paragraph(f"<b>R{total_amount:.2f}</b>", styles['Normal'])])

    items_table = Table(items_data, colWidths=[1 * inch, 2.5 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'), # Align product names to the left
        ('ALIGN', (-2, 1), (-1, -2), 'RIGHT'), # Align prices to the right
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'), # Align total to the right
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.5 * inch))

    # --- Footer ---
    footer_text_content = config.get('InvoiceTemplate', 'footer_text', fallback="Thank you for your business!")
    footer_text = Paragraph(footer_text_content, styles['Normal'])
    story.append(footer_text)

    # --- Build the PDF ---
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"Failed to generate PDF: {e}")
        return False

def generate_invoice_pdf(file_path, invoice_details):
    return generate_pdf(file_path, invoice_details, "INVOICE")

def generate_quotation_pdf(file_path, quotation_details):
    return generate_pdf(file_path, quotation_details, "QUOTATION")

def generate_sales_order_pdf(file_path, order_details):
    return generate_pdf(file_path, order_details, "SALES ORDER")

def print_invoice(invoice_details):
    """Generates a temporary PDF and allows the user to select a printer."""
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        if generate_invoice_pdf(temp_file.name, invoice_details):
            # Get available printers
            printers = [printer[2] for printer in win32print.EnumPrinters(2)]
            
            # Show selection dialog
            dialog = tk.Toplevel()
            dialog.title("Select Printer")
            dialog.geometry("300x150")
            
            ttk.Label(dialog, text="Choose a printer:").pack(pady=10)
            printer_var = tk.StringVar(value=win32print.GetDefaultPrinter())
            printer_menu = ttk.Combobox(dialog, textvariable=printer_var, values=printers, state="readonly")
            printer_menu.pack(pady=5)
            
            def do_print():
                selected_printer = printer_var.get()
                try:
                    # Set default printer temporarily (or use ShellExecute with specific printer if possible)
                    # ShellExecute "printto" is the standard way
                    win32api.ShellExecute(
                        0,
                        "printto",
                        temp_file.name,
                        f'"{selected_printer}"',
                        ".",
                        0
                    )
                    dialog.destroy()
                except Exception as e:
                    print(f"Print error: {e}")
                    
            ttk.Button(dialog, text="Print", command=do_print).pack(pady=10)
            
            # Wait for dialog to close
            dialog.wait_window()
            return True
        else:
            return False
    except Exception as e:
        print(f"Printing failed: {e}")
        return False

if __name__ == '__main__':
    pass
