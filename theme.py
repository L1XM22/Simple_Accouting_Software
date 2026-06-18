import tkinter as tk
from tkinter import ttk

def apply_theme(root, accent_color='#2C3E50'):
    """Applies a modern white and charcoal grey theme with bold, bright fonts."""
    style = ttk.Style(root)
    
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass 

    # Color Palette - High Contrast
    BG_COLOR = '#FFFFFF'              # Pure White
    FG_COLOR = '#000000'              # Pure Black
    ACCENT_COLOR = accent_color       # Customizable Accent
    ACCENT_LIGHT = '#34495E'          # Lighter Charcoal
    TEXT_ON_ACCENT = '#FFFFFF'        # White text on accent
    BORDER_COLOR = '#BDC3C7'          # Distinct Grey for borders
    
    # Status Colors
    STATUS_PAID = '#27AE60'           # Green
    STATUS_UNPAID = '#C0392B'         # Red
    STATUS_PARTIAL = '#F39C12'        # Orange
    STATUS_PENDING = '#7F8C8D'        # Grey

    # --- General Configuration ---
    style.configure('.', 
                    background=BG_COLOR, 
                    foreground=FG_COLOR, 
                    font=('Segoe UI', 11)) 
    
    style.configure('TFrame', background=BG_COLOR)
    style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)
    
    # --- Labelframes ---
    style.configure('TLabelframe', 
                    background=BG_COLOR, 
                    bordercolor=BORDER_COLOR,
                    borderwidth=1)
    style.configure('TLabelframe.Label', 
                    background=BG_COLOR, 
                    foreground=ACCENT_COLOR, 
                    font=('Segoe UI', 12, 'bold'))

    # --- Buttons ---
    style.configure('TButton', 
                    background=ACCENT_COLOR, 
                    foreground=TEXT_ON_ACCENT, 
                    borderwidth=0, 
                    focuscolor='none',
                    font=('Segoe UI', 10, 'bold'),
                    padding=(15, 8))
    
    style.map('TButton', 
              background=[('active', ACCENT_LIGHT), ('pressed', ACCENT_COLOR)],
              foreground=[('active', TEXT_ON_ACCENT)])
              
    # --- Action Buttons (Secondary) ---
    style.configure('Action.TButton',
                    background='#ECF0F1',
                    foreground=ACCENT_COLOR,
                    font=('Segoe UI', 10))
    style.map('Action.TButton',
              background=[('active', '#BDC3C7')],
              foreground=[('active', ACCENT_COLOR)])

    # --- Entries and Comboboxes ---
    style.configure('TEntry', 
                    fieldbackground=BG_COLOR, 
                    foreground=FG_COLOR, 
                    bordercolor=BORDER_COLOR,
                    lightcolor=BORDER_COLOR,
                    darkcolor=BORDER_COLOR,
                    padding=5)
    
    style.configure('TCombobox', 
                    fieldbackground=BG_COLOR, 
                    foreground=FG_COLOR, 
                    arrowcolor=ACCENT_COLOR,
                    padding=5)
    
    # --- Treeview (Lists) ---
    style.configure('Treeview', 
                    background=BG_COLOR, 
                    foreground=FG_COLOR, 
                    fieldbackground=BG_COLOR,
                    rowheight=30,
                    font=('Segoe UI', 10),
                    borderwidth=0)
    
    style.configure('Treeview.Heading', 
                    background='#F8F9FA', 
                    foreground=ACCENT_COLOR, 
                    font=('Segoe UI', 10, 'bold'),
                    relief='flat')
    
    style.map('Treeview', 
              background=[('selected', '#E8F6F3')], # Very light teal for selection
              foreground=[('selected', FG_COLOR)])

    # --- Scrollbars ---
    style.configure('Vertical.TScrollbar', 
                    background=BG_COLOR, 
                    troughcolor='#F0F0F0',
                    arrowcolor=ACCENT_COLOR,
                    relief='flat')
    
    # --- Notebook (Tabs) ---
    style.configure('TNotebook', background=BG_COLOR, borderwidth=0)
    style.configure('TNotebook.Tab', 
                    background='#F0F0F0', 
                    foreground=FG_COLOR, 
                    padding=(15, 8), 
                    font=('Segoe UI', 10))
    style.map('TNotebook.Tab', 
              background=[('selected', ACCENT_COLOR)], 
              foreground=[('selected', TEXT_ON_ACCENT)])
              
    # --- Dashboard Cards ---
    style.configure('Card.TFrame', 
                    background='#F8F9FA', 
                    relief='solid', 
                    borderwidth=1,
                    bordercolor='#E0E0E0')

    # --- Standard Tkinter Widgets ---
    root.option_add('*Background', BG_COLOR)
    root.option_add('*Foreground', FG_COLOR)
    
    root.option_add('*Listbox*Background', BG_COLOR)
    root.option_add('*Listbox*Foreground', FG_COLOR)
    root.option_add('*Listbox*selectBackground', '#E8F6F3')
    root.option_add('*Listbox*selectForeground', FG_COLOR)
    root.option_add('*Listbox*Font', ('Segoe UI', 10))
    root.option_add('*Listbox*Relief', 'flat')
    
    root.option_add('*Text*Background', BG_COLOR)
    root.option_add('*Text*Foreground', FG_COLOR)
    root.option_add('*Text*Font', ('Segoe UI', 10))

    root.configure(bg=BG_COLOR)

    # Configure tags for Treeview rows
    # Note: This needs to be applied to the specific treeview instance, 
    # but we can define the colors here for reference.
    # root.tag_configure('paid', foreground=STATUS_PAID)
    # root.tag_configure('unpaid', foreground=STATUS_UNPAID)
