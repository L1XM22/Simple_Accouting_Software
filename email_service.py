import smtplib
import configparser
import os
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pdf_service import generate_invoice_pdf, generate_quotation_pdf

def send_invoice_email(invoice_details):
    """Sends an invoice email to the customer with the invoice attached as a PDF."""
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        smtp_server = config.get('SMTP', 'server')
        smtp_port = config.getint('SMTP', 'port')
        smtp_username = config.get('SMTP', 'username')
        smtp_password = config.get('SMTP', 'password')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Configuration error: {e}. Please configure SMTP settings.")
        return False

    if not all([smtp_server, smtp_port, smtp_username]):
        print("SMTP settings are incomplete. Please update them in the Settings menu.")
        return False

    if not invoice_details or not invoice_details.get('customer_email'):
        print("Could not send email: Customer email is missing.")
        return False

    # Get templates
    subject_template = config.get('EmailTemplates', 'subject', fallback="Invoice #{invoice_id} from Inter-counting")
    body_template = config.get('EmailTemplates', 'body', fallback="Hi {customer_name},\n\nPlease find attached invoice #{invoice_id}.")

    # Format templates
    format_data = {
        'customer_name': invoice_details['customer_name'],
        'invoice_id': invoice_details['id'],
        'invoice_date': invoice_details['invoice_date'],
        'due_date': invoice_details['due_date'],
        'total_amount': f"R{invoice_details['total_amount']:.2f}"
    }
    
    subject = subject_template.format(**format_data)
    body_text = body_template.format(**format_data)

    sender_email = smtp_username
    receiver_email = invoice_details['customer_email']

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    # Attach body
    message.attach(MIMEText(body_text, "plain"))

    # Generate and attach PDF
    temp_pdf_path = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        temp_pdf_path = temp_file.name
        
        if generate_invoice_pdf(temp_pdf_path, invoice_details):
            with open(temp_pdf_path, "rb") as attachment:
                part = MIMEBase("application", "pdf")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            filename = f"Invoice_{invoice_details['id']}.pdf"
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            message.attach(part)
        else:
            print("Failed to generate PDF for attachment.")
            return False

    except Exception as e:
        print(f"Error preparing attachment: {e}")
        return False

    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        print(f"Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        # Clean up temp file
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except Exception:
                pass

def send_quotation_email(quotation_details):
    """Sends a quotation email to the customer with the quotation attached as a PDF."""
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        smtp_server = config.get('SMTP', 'server')
        smtp_port = config.getint('SMTP', 'port')
        smtp_username = config.get('SMTP', 'username')
        smtp_password = config.get('SMTP', 'password')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Configuration error: {e}. Please configure SMTP settings.")
        return False

    if not all([smtp_server, smtp_port, smtp_username]):
        print("SMTP settings are incomplete. Please update them in the Settings menu.")
        return False

    if not quotation_details or not quotation_details.get('customer_email'):
        print("Could not send email: Customer email is missing.")
        return False

    # Get templates
    subject_template = config.get('QuotationEmailTemplates', 'subject', fallback="Quotation #{quotation_id} from Inter-counting")
    body_template = config.get('QuotationEmailTemplates', 'body', fallback="Hi {customer_name},\n\nPlease find attached quotation #{quotation_id}.")

    # Format templates
    format_data = {
        'customer_name': quotation_details['customer_name'],
        'quotation_id': quotation_details['id'],
        'date': quotation_details['date'],
        'total_amount': f"R{quotation_details['total_amount']:.2f}"
    }
    
    subject = subject_template.format(**format_data)
    body_text = body_template.format(**format_data)

    sender_email = smtp_username
    receiver_email = quotation_details['customer_email']

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    # Attach body
    message.attach(MIMEText(body_text, "plain"))

    # Generate and attach PDF
    temp_pdf_path = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        temp_pdf_path = temp_file.name
        
        if generate_quotation_pdf(temp_pdf_path, quotation_details):
            with open(temp_pdf_path, "rb") as attachment:
                part = MIMEBase("application", "pdf")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            filename = f"Quotation_{quotation_details['id']}.pdf"
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            message.attach(part)
        else:
            print("Failed to generate PDF for attachment.")
            return False

    except Exception as e:
        print(f"Error preparing attachment: {e}")
        return False

    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        print(f"Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        # Clean up temp file
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except Exception:
                pass

def send_custom_email(to_addr, subject, body, attachments=None):
    """Sends a custom email with optional attachments."""
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        smtp_server = config.get('SMTP', 'server')
        smtp_port = config.getint('SMTP', 'port')
        smtp_username = config.get('SMTP', 'username')
        smtp_password = config.get('SMTP', 'password')
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_addr
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachments:
        for filename in attachments:
            if not os.path.isfile(filename):
                continue
            
            try:
                with open(filename, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(filename)}",
                )
                msg.attach(part)
            except Exception as e:
                print(f"Failed to attach file {filename}: {e}")

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def _create_email_body(invoice, custom_body_text):
    pass

if __name__ == '__main__':
    pass
