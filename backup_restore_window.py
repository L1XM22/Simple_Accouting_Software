import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from database import backup_database, restore_database, log_action

class BackupRestoreWindow(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.title("Backup & Restore")
        self.geometry("500x300")
        self.current_user = current_user

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Backup Section ---
        backup_frame = ttk.LabelFrame(main_frame, text="Backup Database", padding="15")
        backup_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(backup_frame, text="Save your entire database to a JSON file.").pack(anchor=tk.W, pady=(0, 10))
        ttk.Button(backup_frame, text="Create Backup", command=self.create_backup).pack(anchor=tk.E)

        # --- Restore Section ---
        restore_frame = ttk.LabelFrame(main_frame, text="Restore Database", padding="15")
        restore_frame.pack(fill=tk.X)

        ttk.Label(restore_frame, text="Warning: This will overwrite all current data!").pack(anchor=tk.W, pady=(0, 10))
        ttk.Button(restore_frame, text="Restore from Backup", command=self.restore_backup).pack(anchor=tk.E)

    def create_backup(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"backup_intercounting.json"
        )
        if not file_path:
            return

        if backup_database(file_path):
            log_action(self.current_user['id'], self.current_user['username'], "Created a database backup.")
            messagebox.showinfo("Success", "Database backup created successfully.")
        else:
            messagebox.showerror("Error", "Failed to create backup. Check console for details.")

    def restore_backup(self):
        confirm = messagebox.askyesno(
            "Confirm Restore",
            "Are you sure you want to restore the database?\n\nTHIS WILL DELETE ALL CURRENT DATA and replace it with the backup data.\n\nThis action cannot be undone."
        )
        if not confirm:
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return

        if restore_database(file_path):
            log_action(self.current_user['id'], self.current_user['username'], "Restored database from backup.")
            messagebox.showinfo("Success", "Database restored successfully. Please restart the application.")
            self.master.destroy() # Close the main application
        else:
            messagebox.showerror("Error", "Failed to restore database. Check console for details.")

if __name__ == '__main__':
    root = tk.Tk()
    # Dummy user for testing
    dummy_user = {'id': 0, 'username': 'test_admin'}
    app = BackupRestoreWindow(root, dummy_user)
    root.withdraw()
    app.mainloop()
