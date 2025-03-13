import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import win32clipboard
import win32con
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 複製圖片到剪貼簿
def copy_image_to_clipboard(image_path):
    try:
        img = Image.open(image_path).convert("RGB")  # 避免透明問題
        output = io.BytesIO()
        img.save(output, format="BMP")
        data = output.getvalue()[14:]  # 移除 BMP 頭部
        output.close()
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        win32clipboard.CloseClipboard()

        # 顯示訊息
        status_label.config(text="✅ 已複製成功", foreground="green")
        root.after(2000, lambda: status_label.config(text=""))  # 2 秒後清除訊息
    except Exception as e:
        status_label.config(text=f"❌ 失敗: {e}", foreground="red")

# 計算適當的 max_columns
def get_max_columns():
    window_width = root.winfo_width()
    return max(1, window_width // 200)  # 確保至少 1 列

# 顯示所有圖片
def display_images(img_dir="img/"):
    if not os.path.exists(img_dir):
        return
    
    for widget in frame.winfo_children():
        widget.grid_forget()
    
    image_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    
    if not image_files:
        return
    
    max_columns = get_max_columns()
    row, column = 0, 0

    for image_file in image_files:
        image_path = os.path.join(img_dir, image_file)
        img = Image.open(image_path)
        img.thumbnail((150, 150))
        img_tk = ImageTk.PhotoImage(img)

        img_label = tk.Label(frame, image=img_tk, text=image_file, compound="top", cursor="hand2")
        img_label.image = img_tk
        img_label.grid(row=row, column=column, padx=3, pady=3)
        img_label.bind("<Button-1>", lambda event, path=image_path: copy_image_to_clipboard(path))

        column += 1
        if column >= max_columns:
            column = 0
            row += 1

    frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# 監控 img/ 目錄變化
class DirectoryMonitor(FileSystemEventHandler):
    def __init__(self, img_dir):
        self.img_dir = img_dir

    def on_created(self, event):
        if event.src_path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            display_images(self.img_dir)

# 啟動監控
def start_monitoring():
    observer = Observer()
    observer.schedule(DirectoryMonitor(img_dir="img/"), path="img/", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


is_resizing = False

def on_resize(event):
    global is_resizing
    if not is_resizing:
        is_resizing = True
        root.after(100, lambda: (display_images("img/"), reset_resize_flag()))

def reset_resize_flag():
    global is_resizing
    is_resizing = False


# 創建 Tkinter 視窗
root = tk.Tk()
root.title("Meme Gallery")
root.geometry("800x600")

# 工具列框架
toolbar = tk.Frame(root)
toolbar.pack(fill="x", pady=5)

reload_button = tk.Button(toolbar, text="🔄 重新載入圖片", command=lambda: display_images("img/"))
reload_button.pack(side="left", padx=10)

status_label = tk.Label(toolbar, text="", fg="green")
status_label.pack(side="left")

# 滾動區域
canvas = tk.Canvas(root)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# 圖片框架
frame = tk.Frame(canvas)
frame_id = canvas.create_window((0, 0), window=frame, anchor="nw")

# 讓 Frame 內的內容可滾動
def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

frame.bind("<Configure>", on_frame_configure)

# 綁定滾輪事件
def on_mouse_wheel(event):
    canvas.yview_scroll(-1 * (event.delta // 40), "units")

canvas.bind_all("<MouseWheel>", on_mouse_wheel)  # Windows
canvas.bind_all("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))  # Linux 滾輪上
canvas.bind_all("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))   # Linux 滾輪下

# 綁定視窗大小變化事件
root.bind("<Configure>", on_resize)

# 初始顯示圖片
display_images("img/")

# 監控 img/ 目錄變化
monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
monitor_thread.start()

root.mainloop()
