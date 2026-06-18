from database import get_automation_rules, get_invoice_details
from email_service import send_invoice_email

def trigger_automation(event_type, **kwargs):
    """Checks for active automation rules for the given event and executes them."""
    rules = get_automation_rules()
    
    for rule in rules:
        if rule['is_active'] and rule['trigger_event'] == event_type:
            execute_action(rule['action_type'], **kwargs)

def execute_action(action_type, **kwargs):
    """Executes a specific action based on the rule."""
    if action_type == 'Email Invoice':
        invoice_id = kwargs.get('invoice_id')
        if invoice_id:
            invoice_details = get_invoice_details(invoice_id)
            if invoice_details:
                print(f"Automation: Sending email for invoice #{invoice_id}")
                send_invoice_email(invoice_details)
    
    # Add more actions here as needed (e.g., 'Log Event', 'Notify Admin')
