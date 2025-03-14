import os
import io
import json
import time
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import win32clipboard
import win32con
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MemeGalleryApp:
    def __init__(self, root):
        self.root = root
        self.load_config()
        self.root.title("Meme Gallery")
        self.root.geometry(self.config.get('window_geometry', '800x600'))
        self.img_dir = self.config.get('image_dir', 'img/')
        self.image_width = self.config.get('image_width', 150)
        self.observer = None

        self.create_widgets()
        self.display_images()

        self.is_resizing = False
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.monitor_thread = threading.Thread(target=self.start_monitoring, daemon=True)
        self.monitor_thread.start()

    # 讀取 config.json
    def load_config(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    # 儲存 config.json
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f)

    # 創建 UI 元件
    def create_widgets(self):
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(fill="x", pady=5)

        self.reload_button = tk.Button(self.toolbar, text="🔄 重新載入圖片", command=self.display_images)
        self.reload_button.pack(side="left", padx=10)

        self.select_dir_button = tk.Button(self.toolbar, text="📁 選擇圖片目錄", command=self.select_image_dir)
        self.select_dir_button.pack(side="left", padx=10)

        self.open_dir_button = tk.Button(self.toolbar, text="📂 開啟圖片目錄", command=self.open_image_dir)
        self.open_dir_button.pack(side="left", padx=10)

        self.save_clipboard_button = tk.Button(self.toolbar, text="📋 保存剪貼簿圖片", command=self.save_clipboard_image)
        self.save_clipboard_button.pack(side="left", padx=10)

        self.search_frame = tk.Frame(self.toolbar)
        self.search_frame.pack(side="right", padx=10)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.display_images())
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side="right")

        self.search_label = tk.Label(self.search_frame, text="🔍")
        self.search_label.pack(side="right")

        self.status_label = tk.Label(self.toolbar, text="", fg="green")
        self.status_label.pack(side="left")

        self.canvas = tk.Canvas(self.root)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame = tk.Frame(self.canvas)
        self.frame_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", self.on_frame_configure)

        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", lambda event: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda event: self.canvas.yview_scroll(1, "units"))

        self.canvas.bind("<Button-3>", self.show_context_menu)

    # 複製圖片到剪貼簿
    def copy_image_to_clipboard(self, image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            output = io.BytesIO()
            img.save(output, format="BMP")
            data = output.getvalue()[14:]
            output.close()
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            return False

    # 圖片點擊事件
    def on_image_click(self, event, image_path):
        success = self.copy_image_to_clipboard(image_path)
        if success:
            self.status_label.config(text="✅ 已複製成功", foreground="green")
        else:
            self.status_label.config(text="❌ 失敗", foreground="red")
        self.root.after(2000, lambda: self.status_label.config(text=""))

    # 計算最大列數
    def get_max_columns(self):
        window_width = self.root.winfo_width()
        return max(1, window_width // (self.image_width + 6))  # 加上間距

    # 顯示所有圖片
    def display_images(self):
        if not os.path.exists(self.img_dir):
            return
        
        for widget in self.frame.winfo_children():
            widget.grid_forget()
        
        search_text = self.search_var.get().lower()
        image_files = [f for f in os.listdir(self.img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and search_text in f.lower()]
        
        if not image_files:
            return
        
        max_columns = self.get_max_columns()
        row, column = 0, 0

        for image_file in image_files:
            image_path = os.path.join(self.img_dir, image_file)
            img = Image.open(image_path)
            img.thumbnail((self.image_width, self.image_width))
            img_tk = ImageTk.PhotoImage(img)

            img_label = tk.Label(self.frame, image=img_tk, text=image_file, compound="top", cursor="hand2")
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
        if isinstance(widget, tk.Label):
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label="刪除圖片", command=lambda: self.delete_image(widget))
            self.context_menu.add_command(label="重命名圖片", command=lambda: self.rename_image(widget))
            self.context_menu.post(event.x_root, event.y_root)

    def delete_image(self, widget):
        image_path = widget.cget("text")
        if messagebox.askyesno("確認刪除", f"確定要刪除 {image_path} 嗎？"):
            os.remove(os.path.join(self.img_dir, image_path))
            self.display_images()

    def rename_image(self, widget):
        image_path = widget.cget("text")
        original_ext = os.path.splitext(image_path)[1]
        new_name = self.show_rename_dialog(image_path, original_ext)
        if new_name:
            if not new_name.endswith(original_ext):
                new_name += original_ext
            new_path = os.path.join(self.img_dir, new_name)
            os.rename(os.path.join(self.img_dir, image_path), new_path)
            self.display_images()

    def show_rename_dialog(self, image_path, original_ext):
        dialog = tk.Toplevel(self.root)
        dialog.title("重命名圖片")
        dialog.geometry(f"400x150+{self.root.winfo_x() + self.root.winfo_width() // 2 - 200}+{self.root.winfo_y() + self.root.winfo_height() // 2 - 50}")

        tk.Label(dialog, text="輸入新的圖片名稱：").pack(pady=10)
        new_name_var = tk.StringVar(value=os.path.splitext(image_path)[0])
        entry = tk.Entry(dialog, textvariable=new_name_var, width=50)
        entry.pack(pady=5)

        def on_ok():
            dialog.destroy()

        tk.Button(dialog, text="確定", command=on_ok).pack(pady=10)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return new_name_var.get()

    # 框架配置事件
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # 滾輪事件
    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 40), "units")

    # 視窗大小變化事件
    def on_resize(self, event):
        if not self.is_resizing:
            self.is_resizing = True
            self.root.after(100, lambda: (self.display_images(), self.reset_resize_flag()))

    # 重置大小變化標誌
    def reset_resize_flag(self):
        self.is_resizing = False

    # 視窗關閉事件
    def on_close(self):
        self.config['window_geometry'] = self.root.geometry()
        self.config['image_width'] = self.image_width
        self.save_config()
        self.stop_monitoring()
        self.root.destroy()

    # 選擇圖片目錄
    def select_image_dir(self):
        new_dir = filedialog.askdirectory()
        if new_dir:
            self.img_dir = new_dir
            self.config['image_dir'] = new_dir
            self.save_config()
            self.display_images()

    # 開啟圖片目錄
    def open_image_dir(self):
        abs_img_dir = os.path.abspath(self.img_dir)
        if os.path.exists(abs_img_dir):
            subprocess.Popen(['explorer', abs_img_dir])

    def save_clipboard_image(self):
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                image = Image.open(io.BytesIO(data))
                timestamp = time.strftime("%Y%m%d%H%M%S")
                image_path = os.path.join(self.img_dir, f"clipboard_{timestamp}.png")
                image.save(image_path)
                self.display_images()
                self.status_label.config(text="✅ 剪貼簿圖片已保存", foreground="green")
            else:
                self.status_label.config(text="❌ 剪貼簿中沒有圖片", foreground="red")
            win32clipboard.CloseClipboard()
        except Exception as e:
            self.status_label.config(text=f"❌ 保存失敗: {e}", foreground="red")
            win32clipboard.CloseClipboard()

    def start_monitoring(self):
        if self.observer is None or not self.observer.is_alive():
            self.observer = Observer()
            self.observer.schedule(DirectoryMonitor(self), path=self.img_dir, recursive=False)
            self.observer.start()

    def stop_monitoring(self):
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            self.observer = None

class DirectoryMonitor(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    # 目錄創建事件
    def on_created(self, event):
        if event.src_path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            self.app.display_images()

if __name__ == "__main__":
    root = tk.Tk()
    app = MemeGalleryApp(root)
    root.mainloop()
