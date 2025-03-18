import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk  # Import ttk for themed widgets

class FontDialog:
    def __init__(self, root, current_font_family, current_font_size):
        self.root = root
        self.current_font_family = current_font_family
        self.current_font_size = current_font_size
        self.new_font_family = None
        self.new_font_size = None

    def show(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("🪄 變更字型")
        dialog.geometry(f"400x250+{self.root.winfo_x() + self.root.winfo_width() // 2 - 200}+{self.root.winfo_y() + self.root.winfo_height() // 2 - 100}")

        ttk.Label(dialog, text="字型：", font=(self.current_font_family, self.current_font_size)).pack(pady=10)
        font_family_var = tk.StringVar(value=self.current_font_family)
        font_family_dropdown = ttk.OptionMenu(dialog, font_family_var, *tkfont.families())
        font_family_dropdown.pack(pady=5)

        ttk.Label(dialog, text="字體大小：", font=(self.current_font_family, self.current_font_size)).pack(pady=10)
        font_size_var = tk.IntVar(value=self.current_font_size)
        font_size_entry = ttk.Entry(dialog, textvariable=font_size_var, width=10, font=(self.current_font_family, self.current_font_size))
        font_size_entry.pack(pady=5)

        def on_ok():
            self.new_font_family = font_family_var.get()
            self.new_font_size = font_size_var.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ttk.Button(dialog, text="確定", command=on_ok).pack(side="left", padx=10, pady=10)
        ttk.Button(dialog, text="取消", command=on_cancel).pack(side="right", padx=10, pady=10)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return self.new_font_family, self.new_font_size
