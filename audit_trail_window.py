import tkinter as tk
from tkinter import ttk
from database import get_audit_logs

class AuditTrailWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Audit Trail")
        self.geometry("900x600")

        # --- Treeview to display logs ---
        tree_frame = ttk.Frame(self, padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Timestamp", "Username", "Action"),
            show="headings"
        )
        self.tree.heading("Timestamp", text="Timestamp")
        self.tree.heading("Username", text="User")
        self.tree.heading("Action", text="Action")

        self.tree.column("Timestamp", width=180)
        self.tree.column("Username", width=120)
        self.tree.column("Action", width=550)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.load_logs()

    def load_logs(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        logs = get_audit_logs()
        for log in logs:
            # Format timestamp for better readability
            ts = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            self.tree.insert("", tk.END, values=(ts, log['username'], log['action']))

if __name__ == '__main__':
    root = tk.Tk()
    app = AuditTrailWindow(root)
    root.withdraw()
    app.mainloop()
