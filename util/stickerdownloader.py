# stickerdownloader.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal
import os, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class StickerDownloader(QObject):
  progress = pyqtSignal(str, str, int)   # (msg, type, timeout)
  finished = pyqtSignal(str)             # emit 存放資料夾路徑

  def __init__(self, url, target_folder):
    super().__init__()
    self.url = url
    self.target_folder = target_folder

  def run(self):
    try:
      if not re.match(r"^https://store\.line\.me/stickershop/product/\d+(/|/\w{2}-\w{4})?$", self.url):
        self.progress.emit('[Line 貼圖] 請輸入正確的 Line 貼圖網址', 'error', 2000)
        return

      resp = requests.get(self.url, headers={"User-Agent": "Mozilla/5.0"})
      if resp.status_code != 200:
        self.progress.emit(f'[Line 貼圖] 下載頁面失敗: {resp.status_code}', 'error', 2000)
        return

      soup = BeautifulSoup(resp.text, 'html.parser')
      title_tag = soup.select_one('p.mdCMN38Item01Ttl')
      title = title_tag.get_text(strip=True) if title_tag else "LineSticker"
      safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)

      save_dir = os.path.join(self.target_folder, safe_title)
      os.makedirs(save_dir, exist_ok=True)

      # ====== 抓圖片 ======
      img_urls = set()
      for img in soup.select('span.mdCMN09Image img, .FnStickerPreviewItem img'):
        src = img.get('src')
        if isinstance(src, str) and 'stickershop.line-scdn.net/stickershop/v1/sticker/' in src:
          img_urls.add(src.split(';')[0])

      for span in soup.select('span.mdCMN09Image'):
        style = span.get('style') or ''
        m = re.search(r'url\((https://stickershop\.line-scdn\.net/stickershop/v1/sticker/[^\)]+)\)', style)
        if m:
          img_urls.add(m.group(1).split(';')[0])

      if not img_urls:
        self.progress.emit('[Line 貼圖] 找不到貼圖圖片', 'error', 2000)
        return

      # ====== 下載 ======
      total = len(img_urls)
      for i, img_url in enumerate(sorted(img_urls), 1):
        ext = os.path.splitext(urlparse(img_url).path)[1] or '.png'
        fname = f'line_sticker_{i:02d}{ext}'
        out_path = os.path.join(save_dir, fname)

        try:
          img_data = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}).content
          with open(out_path, 'wb') as f:
            f.write(img_data)
          self.progress.emit(f'[Line 貼圖] {safe_title} 下載中... {i}/{total}', 'info', 800)
        except Exception as e:
          self.progress.emit(f'[Line 貼圖] 下載失敗: {img_url} {e}', 'error', 2000)

      self.progress.emit(f'[Line 貼圖] {safe_title} 下載完成，共 {total} 張', 'info', 3000)
      self.finished.emit(save_dir)

    except Exception as e:
      self.progress.emit(f'[Line 貼圖] 發生錯誤: {e}', 'error', 2000)
