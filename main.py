# pip install PyQt6 PyQt6-WebEngine
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, QMimeData, QThread
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import sys, os
from pathlib import Path
from util.stickerdownloader import StickerDownloader

class Bridge(QObject):
  
  @pyqtSlot(str, str)
  def downloadLineSticker(self, url, target_folder):
    self.thread = QThread()
    self.worker = StickerDownloader(url, target_folder)
    self.worker.moveToThread(self.thread)

    # 連接訊號
    self.thread.started.connect(self.worker.run)
    self.worker.progress.connect(self.showHint)
    self.worker.finished.connect(self._on_download_finished)

    # 清理
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.thread.finished.connect(self.thread.deleteLater)

    self.thread.start()

  def _on_download_finished(self, save_dir):
    self.reload_func(save_dir)

  @pyqtSlot(str)
  def pasteImageFromClipboard(self, target_folder):
    import os, datetime
    from PyQt6.QtGui import QGuiApplication
    from PIL import Image
    from io import BytesIO
    clipboard = QGuiApplication.clipboard()
    mime = clipboard.mimeData()
    
    if mime.hasImage():
      qtimg = clipboard.image()
      if qtimg.isNull():
        self.showHint('[Paste Image Error] 剪貼簿圖片為空', 'error')
        return
      # 轉成 PIL Image
      buffer = BytesIO()
      pil_img = Image.fromqimage(qtimg)
      # 自動產生檔名
      ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
      fname = f'paste_{ts}.png'
      out_path = os.path.join(target_folder, fname)
      pil_img.save(out_path)
      self.reload_func(target_folder)
      self.showHint(f'[Paste Image] 已儲存 {out_path}', 'info')
    elif mime.hasUrls():
      # 有些截圖工具會以檔案方式放剪貼簿
      for url in mime.urls():
        local_path = url.toLocalFile()
        if os.path.isfile(local_path):
          ext = os.path.splitext(local_path)[1].lower()
          if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            fname = f'paste_{ts}{ext}'
            out_path = os.path.join(target_folder, fname)
            with open(local_path, 'rb') as src, open(out_path, 'wb') as dst:
              dst.write(src.read())
            self.reload_func(target_folder)
            self.showHint(f'[Paste Image] 已儲存 {out_path}', 'info')
            return
      self.showHint('[Paste Image Error] 剪貼簿沒有圖片檔案', 'error')
    else:
      self.showHint('[Paste Image Error] 剪貼簿沒有圖片', 'error')

  @pyqtSlot(str, str)
  def saveClipboardImage(self, target_folder, base64data):
    import os, base64, re, datetime
    from PIL import Image
    from io import BytesIO
    # base64data: data:image/png;base64,...
    m = re.match(r'data:(image/\w+);base64,(.+)', base64data)
    if not m:
      self.showHint('[Paste Image Error] 格式錯誤', 'error')
      return
    mime, b64 = m.groups()
    ext = {
      'image/png': '.png',
      'image/jpeg': '.jpg',
      'image/gif': '.gif',
      'image/webp': '.webp',
    }.get(mime, '.png')
    try:
      imgdata = base64.b64decode(b64)
      # 自動產生檔名
      ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
      fname = f'paste_{ts}{ext}'
      out_path = os.path.join(target_folder, fname)
      # gif 直接寫檔，其他用 PIL 處理
      if ext == '.gif':
        with open(out_path, 'wb') as f:
          f.write(imgdata)
      else:
        img = Image.open(BytesIO(imgdata))
        img.save(out_path)
      self.reload_func(target_folder)
      self.showHint(f'[Paste Image] 已儲存 {out_path}', 'info')
    except Exception as e:
      self.showHint(f'[Paste Image Error] {e}', 'error')
  @pyqtSlot(str, str)
  def moveFile(self, src_path, target_folder):
    import shutil, os
    src_path = os.path.abspath(src_path)
    target_folder = os.path.abspath(target_folder)
    if not os.path.isfile(src_path) or not os.path.isdir(target_folder):
      self.showHint(f"[Move File Error] 檔案或目標資料夾不存在: {src_path} -> {target_folder}", 'error')
      return
    fname = os.path.basename(src_path)
    dst_path = os.path.join(target_folder, fname)
    # 防呆：不可覆蓋
    if os.path.exists(dst_path):
      self.showHint(f"[Move File Error] 目標已存在: {dst_path}", 'error')
      return
    try:
      shutil.move(src_path, dst_path)
      self.reload_func(os.path.dirname(src_path))
    except Exception as e:
      self.showHint(f"[Move File Error] {e}", 'error')

  @pyqtSlot(str, str)
  def moveFolder(self, src_path, target_folder):
    import shutil, os
    src_path = os.path.abspath(src_path)
    target_folder = os.path.abspath(target_folder)
    if not os.path.isdir(src_path) or not os.path.isdir(target_folder):
      self.showHint(f"[Move Folder Error] 資料夾不存在: {src_path} -> {target_folder}", 'error')
      return
    # 防止移動到自己或子資料夾
    if src_path == target_folder or target_folder.startswith(src_path + os.sep):
      self.showHint("[Move Folder Error] 不能移動到自己或子資料夾", 'error')
      return
    fname = os.path.basename(src_path)
    dst_path = os.path.join(target_folder, fname)
    if os.path.exists(dst_path):
      self.showHint(f"[Move Folder Error] 目標已存在: {dst_path}", 'error')
      return
    try:
      shutil.move(src_path, dst_path)
      self.reload_func(os.path.dirname(src_path))
    except Exception as e:
      self.showHint(f"[Move Folder Error] {e}", 'error')
  @pyqtSlot(str, str)
  def createFolder(self, cur_path, folder_name):
    import os
    # cur_path 可能為相對路徑
    if not cur_path:
      cur_path = os.path.join(os.path.dirname(__file__), 'img')
    abs_path = os.path.abspath(cur_path)
    new_folder = os.path.join(abs_path, folder_name)
    if os.path.exists(new_folder):
      return
    try:
      os.makedirs(new_folder)
      self.reload_func(abs_path)
    except Exception as e:
      self.showHint(f"[Create Folder Error] {e}", 'error')
  @pyqtSlot(str)
  def deleteFolder(self, folder_path):
    import shutil
    folder_path = os.path.abspath(folder_path)
    try:
      shutil.rmtree(folder_path)
      self.reload_func(os.path.dirname(folder_path))
    except Exception as e:
      self.showHint(f"[Delete Folder Error] {e}", 'error')
  @pyqtSlot(str)
  def deleteFile(self, file_path):
    import os
    file_path = os.path.abspath(file_path)
    try:
      os.remove(file_path)
      self.reload_func(os.path.dirname(file_path))
    except Exception as e:
      self.showHint(f"[Delete File Error] {e}", 'error')
  @pyqtSlot(str, str)
  def renameFolder(self, old_path, new_name):
    import shutil
    import pathlib
    old_path = os.path.abspath(old_path)
    new_path = os.path.join(os.path.dirname(old_path), new_name)
    # 防呆：不可覆蓋已存在資料夾
    if os.path.exists(new_path):
      return
    try:
      shutil.move(old_path, new_path)
      self.reload_func(os.path.dirname(new_path))
    except Exception as e:
      self.showHint(f"[Rename Folder Error] {e}", 'error')
  @pyqtSlot(str, str)
  def renameFile(self, old_path, new_name):
    import shutil
    import pathlib
    old_path = os.path.abspath(old_path)
    new_path = os.path.join(os.path.dirname(old_path), new_name)
    # 防呆：不可覆蓋已存在檔案
    if os.path.exists(new_path):
      return
    try:
      shutil.move(old_path, new_path)
      self.reload_func(os.path.dirname(new_path))
    except Exception as e:
      self.showHint(f"[Rename File Error] {e}", 'error')
  def __init__(self, reload_func, view):
    super().__init__()
    self.reload_func = reload_func
    self.view = view
    # 確保前端載入完成再呼叫 showHint
    self.view.page().loadFinished.connect(self._on_load_finished)
    self._pending_hints = []
    
  def _on_load_finished(self, ok):
    if ok:
      for msg, hint_type, timeout in self._pending_hints:
        js = f"showHint({msg!r}, {hint_type!r}, {timeout});"
        self.view.page().runJavaScript(js)
      self._pending_hints.clear()
    
  def showHint(self, msg, hint_type='info', timeout=2000):
    if not self.view or not self.view.page():
      return
    if not self.view.page().url().isValid():  # 還沒載入完成
      self._pending_hints.append((msg, hint_type, timeout))
    else:
      js = f"showHint({msg!r}, {hint_type!r}, {timeout});"
      self.view.page().runJavaScript(js)

  @pyqtSlot(str)
  def copyApngFile(self, img_path):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(img_path)])
    QGuiApplication.clipboard().setMimeData(mime)

  @pyqtSlot(str)
  def openFolder(self, folder_path):
    self.reload_func(folder_path)

def main():
  app = QApplication(sys.argv)

  base_img_dir = os.path.join(os.path.dirname(__file__), 'img')
  cur_dir = base_img_dir
  if len(sys.argv) > 1:
    arg_path = sys.argv[1]
    if os.path.isabs(arg_path):
      cur_dir = arg_path
    else:
      cur_dir = os.path.abspath(arg_path)
  if not os.path.isdir(cur_dir):
    cur_dir = base_img_dir

  view = QWebEngineView()
  view.setWindowTitle("Meme Gallery")
  view.setWindowIcon(QIcon('favicon.ico'))
      

  def reload_dir(target_dir):
    nonlocal cur_dir
    if target_dir == '..':
      parent = os.path.dirname(cur_dir)
      # 不可超過 base_img_dir
      if os.path.commonpath([parent, base_img_dir]) == base_img_dir:
        cur_dir = parent
    else:
      if os.path.isdir(target_dir):
        # 防止跳出 base_img_dir
        if os.path.commonpath([os.path.abspath(target_dir), base_img_dir]) == base_img_dir:
          cur_dir = os.path.abspath(target_dir)
    show_dir()

  def show_dir():
    # 支援 png, apng, gif, jpg
    exts = ('.png', '.apng', '.gif', '.jpg', '.jpeg')
    items = os.listdir(cur_dir)
    folders = [f for f in items if os.path.isdir(os.path.join(cur_dir, f))]
    img_files = [f for f in items if f.lower().endswith(exts)]


    folder_tags = ''
    # 非最上層才顯示 ..
    if os.path.normpath(cur_dir) != os.path.normpath(base_img_dir):
      parent_path = os.path.dirname(cur_dir)
      folder_tags += f'<div class="folderbox" data-folder="{parent_path}" data-up="1"><div class="foldericon">⬆️</div><div class="foldername">..</div></div>'
    for folder in folders:
      folder_path = os.path.abspath(os.path.join(cur_dir, folder))
      
      try:
        sub_items = os.listdir(folder_path)
      except Exception:
        sub_items = []
      sub_imgs = [f for f in sub_items if f.lower().endswith(exts)]
      
      if sub_imgs:
        first_img = os.path.join(folder_path, sub_imgs[0])
        first_img_url = QUrl.fromLocalFile(first_img).toString()
        folder_icon_html = f'''
          <div class="foldericon">
            📁
            <img src="{first_img_url}" class="folderthumb" />
          </div>
        '''
      else:
        folder_icon_html = '<div class="foldericon">📁</div>'

      folder_tags += f'<div class="folderbox" data-folder="{folder_path}">{folder_icon_html}<div class="foldername">{folder}</div></div>'

    img_tags = ''
    for fname in img_files:
      fpath = os.path.abspath(os.path.join(cur_dir, fname))
      furl = QUrl.fromLocalFile(fpath).toString()
      ext = os.path.splitext(fname)[1].lower()
      # 針對 gif/apng 加上 loop 屬性（雖然大多數瀏覽器會自動循環）
      loop_attr = ' loop' if ext in ['.gif', '.apng'] else ''
      img_tags += f'<div class="imgbox"><img src="{furl}" data-path="{fpath}" alt="{fname}"{loop_attr} /><div class="imgname">{fname}</div></div>'


    # 產生可點擊 breadcrumb
    rel_parts = []
    cur = cur_dir
    while True:
      if os.path.normpath(cur) == os.path.normpath(base_img_dir):
        rel_parts.append(('img', base_img_dir))
        break
      rel_parts.append((os.path.basename(cur), cur))
      cur = os.path.dirname(cur)
    rel_parts = rel_parts[::-1]
    breadcrumb = []
    for name, abspath in rel_parts:
      breadcrumb.append(f'<a href="#" class="breadcrumb" data-folder="{abspath}">{name}</a>')
    rel_path = ' / '.join(breadcrumb)

    # 產生 rel_path_html 與 cur_dir 給模板
    rel_path_html = rel_path
    # 讀取外部 HTML template
    template_path = Path(__file__).parent / 'static' / 'template.html'
    with open(template_path, encoding='utf-8') as f:
      html_tpl = f.read()
    html = html_tpl.replace('{{folder_tags}}', folder_tags) \
      .replace('{{img_tags}}', img_tags) \
      .replace('{{rel_path}}', rel_path_html) \
      .replace('{{cur_dir}}', cur_dir)
    # baseUrl 設為專案根目錄，確保 static/ 可正確載入
    project_root = Path(__file__).parent
    base_url = QUrl.fromLocalFile(str(project_root) + os.sep)
    view.setHtml(html, baseUrl=base_url)

  channel = QWebChannel(view.page())
  bridge = Bridge(reload_dir, view)
  channel.registerObject("bridge", bridge)
  view.page().setWebChannel(channel)

  show_dir()
  view.resize(1000, 800)
  view.show()
  return app.exec()

if __name__ == "__main__":
    sys.exit(main())
