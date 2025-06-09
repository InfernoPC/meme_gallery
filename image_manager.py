import os
import io
import time
from PIL import Image
import win32clipboard
import win32con

class ImageManager:
    def __init__(self, img_dir, image_width):
        self.img_dir = img_dir
        self.image_width = image_width

    def get_image_files(self, search_text):
        return [f for f in os.listdir(self.img_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and search_text in f.lower()]

    def remove_transparency(self, img, bg_color=(255, 255, 255)):
        """若圖片含有透明背景，則自動轉為白底"""
        if img.mode in ('RGBA', 'LA'):
            bg = Image.new("RGB", img.size, bg_color)
            bg.paste(img, mask=img.split()[-1])  # 用 alpha channel 作為遮罩
            return bg
        else:
            return img.convert("RGB")

    def copy_image_to_clipboard(self, image_path):
        try:
            img = Image.open(image_path)
            img = self.remove_transparency(img)
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

    def save_clipboard_image(self):
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                image = Image.open(io.BytesIO(data))
                image = self.remove_transparency(image)

                timestamp = time.strftime("%Y%m%d%H%M%S")
                image_path = os.path.join(self.img_dir, f"clipboard_{timestamp}.png")
                image.save(image_path)
                return image_path
            else:
                return None
        except Exception as e:
            return None
        finally:
            win32clipboard.CloseClipboard()
