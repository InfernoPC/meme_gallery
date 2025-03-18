import os
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk  # Import ttk for themed widgets
from PIL import Image, ImageTk
from watchdog.observers import Observer

from config_manager import ConfigManager
from font_manager import FontManager
from image_manager import ImageManager
from font_dialog import FontDialog  # Import the new FontDialog class
from rename_dialog import RenameDialog  # Import the new RenameDialog class
from directory_monitor import DirectoryMonitor  # Import the new DirectoryMonitor class

class MemeGalleryApp:
    def __init__(self, root):
        self.root = root
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.font_manager = FontManager(self.config)
        self.image_manager = ImageManager(self.config.get('image_dir', 'img/'), self.config.get('image_width', 150))
        self.observer = None

        self.root.title("Meme Gallery")
        self.root.geometry(self.config.get('window_geometry', '800x600'))

        self.create_widgets()
        self.root.update_idletasks()  # Ensure the window is fully rendered before calculating columns
        self.display_images()

        self.is_resizing = False
        self.last_geometry = self.root.geometry().split('+')[0]  # Track the last geometry size
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.monitor_thread = threading.Thread(target=self.start_monitoring, daemon=True)
        self.monitor_thread.start()

    def create_widgets(self):
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(fill="x", pady=5)

        self.settings_button = ttk.Button(self.toolbar, text="⚙", command=self.show_settings_menu)
        self.settings_button.pack(side="left", padx=10)

        self.reload_button = ttk.Button(self.toolbar, text="🔄 重新載入圖片", command=self.display_images)
        self.reload_button.pack(side="left", padx=10)

        self.select_dir_button = ttk.Button(self.toolbar, text="📁 選擇圖片目錄", command=self.select_image_dir)
        self.select_dir_button.pack(side="left", padx=10)

        self.open_dir_button = ttk.Button(self.toolbar, text="📂 開啟圖片目錄", command=self.open_image_dir)
        self.open_dir_button.pack(side="left", padx=10)

        self.save_clipboard_button = ttk.Button(self.toolbar, text="📋 保存剪貼簿圖片", command=self.save_clipboard_image)
        self.save_clipboard_button.pack(side="left", padx=10)

        self.search_frame = ttk.Frame(self.toolbar)
        self.search_frame.pack(side="right", padx=10)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.display_images())
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side="right")

        self.search_label = ttk.Label(self.search_frame, text="🔍")
        self.search_label.pack(side="right")

        self.status_label = ttk.Label(self.toolbar, text="", foreground="green")
        self.status_label.pack(side="left")

        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame = ttk.Frame(self.canvas)
        self.frame_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", self.on_frame_configure)

        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", lambda event: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda event: self.canvas.yview_scroll(1, "units"))

        self.canvas.bind("<Button-3>", self.show_context_menu)

    def show_settings_menu(self):
        self.settings_menu = tk.Menu(self.root, tearoff=0)
        self.settings_menu.add_command(label="🪄 變更字型", command=self.change_font)
        self.settings_menu.post(self.settings_button.winfo_rootx(), self.settings_button.winfo_rooty() + self.settings_button.winfo_height())

    def change_font(self):
        font_dialog = FontDialog(self.root, self.font_manager.font_family, self.font_manager.font_size)
        new_font_family, new_font_size = font_dialog.show()
        if new_font_family and new_font_size:
            self.font_manager.update_font(new_font_family, new_font_size)
            self.config_manager.save_config()
            self.update_fonts()

    def update_fonts(self):
        self.settings_button.config(font=self.font_manager.custom_font)
        self.reload_button.config(font=self.font_manager.custom_font)
        self.select_dir_button.config(font=self.font_manager.custom_font)
        self.open_dir_button.config(font=self.font_manager.custom_font)
        self.search_entry.config(font=self.font_manager.custom_font)
        self.search_label.config(font=self.font_manager.custom_font)
        self.status_label.config(font=self.font_manager.custom_font)
        for widget in self.frame.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.config(font=self.font_manager.custom_font)

    def save_clipboard_image(self):
        image_path = self.image_manager.save_clipboard_image()
        if image_path:
            self.display_images()
            self.status_label.config(text="✅ 剪貼簿圖片已保存", foreground="green")
        else:
            self.status_label.config(text="❌ 剪貼簿中沒有圖片", foreground="red")

    def on_image_click(self, event, image_path):
        success = self.image_manager.copy_image_to_clipboard(image_path)
        if success:
            self.status_label.config(text="✅ 已複製成功", foreground="green")
        else:
            self.status_label.config(text="❌ 失敗", foreground="red")
        self.root.after(2000, lambda: self.status_label.config(text=""))

    def get_max_columns(self):
        window_width = self.root.winfo_width()
        if window_width == 1:  # Handle the initial app start
            window_width = int(self.config.get('window_geometry', '800x600').split('x')[0])
        return max(1, window_width // (self.image_manager.image_width + 6))  # 加上間距

    def display_images(self):
        if not os.path.exists(self.image_manager.img_dir):
            return
        
        for widget in self.frame.winfo_children():
            widget.grid_forget()
        
        search_text = self.search_var.get().lower()
        image_files = self.image_manager.get_image_files(search_text)
        
        if not image_files:
            return
        
        max_columns = self.get_max_columns()
        row, column = 0, 0

        for image_file in image_files:
            image_path = os.path.join(self.image_manager.img_dir, image_file)
            img = Image.open(image_path)
            img.thumbnail((self.image_manager.image_width, self.image_manager.image_width))
            img_tk = ImageTk.PhotoImage(img)

            img_label = ttk.Label(self.frame, image=img_tk, text=image_file, compound="top", cursor="hand2", font=self.font_manager.custom_font, wraplength=self.image_manager.image_width)
            img_label.image = img_tk
            img_label.grid(row=row, column=column, padx=3, pady=3)
            img_label.bind("<Button-1>", lambda event, path=image_path: self.on_image_click(event, path))
            img_label.bind("<Button-3>", self.show_context_menu)

            column += 1
            if column >= max_columns:
                column = 0
                row += 1

        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def show_context_menu(self, event):
        widget = event.widget
        if isinstance(widget, ttk.Label):
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label="💔 刪除圖片", command=lambda: self.delete_image(widget))
            self.context_menu.add_command(label="🗨 重命名圖片", command=lambda: self.rename_image(widget))
            self.context_menu.post(event.x_root, event.y_root)

    def delete_image(self, widget):
        image_path = widget.cget("text")
        if messagebox.askyesno("確認刪除", f"確定要刪除 {image_path} 嗎？"):
            os.remove(os.path.join(self.image_manager.img_dir, image_path))
            self.display_images()

    def rename_image(self, widget):
        image_path = widget.cget("text")
        original_ext = os.path.splitext(image_path)[1]
        rename_dialog = RenameDialog(self.root, os.path.splitext(image_path)[0])
        new_name = rename_dialog.show()
        if new_name:
            if not new_name.endswith(original_ext):
                new_name += original_ext
            new_path = os.path.join(self.image_manager.img_dir, new_name)
            os.rename(os.path.join(self.image_manager.img_dir, image_path), new_path)
            self.display_images()

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 40), "units")

    def on_resize(self, event):
        current_geometry = self.root.geometry().split('+')[0]
        if current_geometry != self.last_geometry:
            self.last_geometry = current_geometry
            if not self.is_resizing:
                self.is_resizing = True
                self.root.after(100, lambda: (self.display_images(), self.reset_resize_flag()))

    def reset_resize_flag(self):
        self.is_resizing = False

    def on_close(self):
        self.config['window_geometry'] = self.root.geometry()
        self.config['image_width'] = self.image_manager.image_width
        self.config_manager.save_config()
        self.stop_monitoring()
        self.root.destroy()

    def select_image_dir(self):
        new_dir = filedialog.askdirectory()
        if new_dir:
            self.image_manager.img_dir = new_dir
            self.config['image_dir'] = new_dir
            self.config_manager.save_config()
            self.display_images()

    def open_image_dir(self):
        abs_img_dir = os.path.abspath(self.image_manager.img_dir)
        if os.path.exists(abs_img_dir):
            subprocess.Popen(['explorer', abs_img_dir])

    def start_monitoring(self):
        if self.observer is None or not self.observer.is_alive():
            self.observer = Observer()
            self.observer.schedule(DirectoryMonitor(self), path=self.image_manager.img_dir, recursive=False)
            self.observer.start()

    def stop_monitoring(self):
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            self.observer = None
