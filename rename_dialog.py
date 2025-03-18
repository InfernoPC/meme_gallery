import tkinter as tk
from tkinter import ttk  # Import ttk for themed widgets

class RenameDialog:
    def __init__(self, root, current_name):
        self.root = root
        self.current_name = current_name
        self.new_name = None

    def show(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("🗨 重命名圖片")
        dialog.geometry(f"400x150+{self.root.winfo_x() + self.root.winfo_width() // 2 - 200}+{self.root.winfo_y() + self.root.winfo_height() // 2 - 50}")

        ttk.Label(dialog, text="輸入新的圖片名稱：").pack(pady=10)
        new_name_var = tk.StringVar(value=self.current_name)
        entry = ttk.Entry(dialog, textvariable=new_name_var, width=50)
        entry.pack(pady=5)
        entry.focus_set()
        entry.select_range(0, tk.END)

        def on_ok(event=None):
            self.new_name = new_name_var.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        entry.bind("<Return>", on_ok)
        ttk.Button(dialog, text="確定", command=on_ok).pack(side="left", padx=10, pady=10)
        ttk.Button(dialog, text="取消", command=on_cancel).pack(side="right", padx=10, pady=10)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return self.new_name
