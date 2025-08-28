# pip install PyQt6 PyQt6-WebEngine
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QObject, pyqtSlot, QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QMimeData
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import sys, os
from pathlib import Path

class Bridge(QObject):
  @pyqtSlot(str, str)
  def moveFile(self, src_path, target_folder):
    import shutil, os
    src_path = os.path.abspath(src_path)
    target_folder = os.path.abspath(target_folder)
    if not os.path.isfile(src_path) or not os.path.isdir(target_folder):
      print(f"[Move File Error] 檔案或目標資料夾不存在: {src_path} -> {target_folder}")
      return
    fname = os.path.basename(src_path)
    dst_path = os.path.join(target_folder, fname)
    # 防呆：不可覆蓋
    if os.path.exists(dst_path):
      print(f"[Move File Error] 目標已存在: {dst_path}")
      return
    try:
      shutil.move(src_path, dst_path)
      self.reload_func(os.path.dirname(src_path))
    except Exception as e:
      print(f"[Move File Error] {e}")

  @pyqtSlot(str, str)
  def moveFolder(self, src_path, target_folder):
    import shutil, os
    src_path = os.path.abspath(src_path)
    target_folder = os.path.abspath(target_folder)
    if not os.path.isdir(src_path) or not os.path.isdir(target_folder):
      print(f"[Move Folder Error] 資料夾不存在: {src_path} -> {target_folder}")
      return
    # 防止移動到自己或子資料夾
    if src_path == target_folder or target_folder.startswith(src_path + os.sep):
      print(f"[Move Folder Error] 不能移動到自己或子資料夾")
      return
    fname = os.path.basename(src_path)
    dst_path = os.path.join(target_folder, fname)
    if os.path.exists(dst_path):
      print(f"[Move Folder Error] 目標已存在: {dst_path}")
      return
    try:
      shutil.move(src_path, dst_path)
      self.reload_func(os.path.dirname(src_path))
    except Exception as e:
      print(f"[Move Folder Error] {e}")
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
      print(f"[Create Folder Error] {e}")
  @pyqtSlot(str)
  def deleteFolder(self, folder_path):
    import shutil
    folder_path = os.path.abspath(folder_path)
    try:
      shutil.rmtree(folder_path)
      self.reload_func(os.path.dirname(folder_path))
    except Exception as e:
      print(f"[Delete Folder Error] {e}")
  @pyqtSlot(str)
  def deleteFile(self, file_path):
    import os
    file_path = os.path.abspath(file_path)
    try:
      os.remove(file_path)
      self.reload_func(os.path.dirname(file_path))
    except Exception as e:
      print(f"[Delete File Error] {e}")
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
      print(f"[Rename Folder Error] {e}")
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
      print(f"[Rename Error] {e}")
  def __init__(self, reload_func):
    super().__init__()
    self.reload_func = reload_func

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
      folder_tags += f'<div class="folderbox" data-folder="{folder_path}"><div class="foldericon">📁</div><div class="foldername">{folder}</div></div>'

    img_tags = ''
    for fname in img_files:
      fpath = os.path.abspath(os.path.join(cur_dir, fname))
      furl = QUrl.fromLocalFile(fpath).toString()
      ext = os.path.splitext(fname)[1].lower()
      # 針對 gif/apng 加上 loop 屬性（雖然大多數瀏覽器會自動循環）
      loop_attr = ' loop' if ext in ['.gif', '.apng'] else ''
      img_tags += f'<div class="imgbox"><img src="{furl}" data-path="{fpath}" alt="{fname}"{loop_attr}/><div class="imgname">{fname}</div></div>'


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

    # 產生 data-curr-dir 屬性的 span，直接用目前目錄 abspath
    rel_path_html = f'<span class="path" data-curr-dir="{cur_dir}">{rel_path}</span>'

    # 讀取外部 HTML template
    template_path = Path(__file__).parent / 'static' / 'template.html'
    with open(template_path, encoding='utf-8') as f:
        html_tpl = f.read()
    html = html_tpl.replace('{{folder_tags}}', folder_tags).replace('{{img_tags}}', img_tags).replace('{{rel_path}}', rel_path_html)
    # baseUrl 設為專案根目錄，確保 static/ 可正確載入
    project_root = Path(__file__).parent
    base_url = QUrl.fromLocalFile(str(project_root) + os.sep)
    view.setHtml(html, baseUrl=base_url)

  channel = QWebChannel(view.page())
  bridge = Bridge(reload_dir)
  channel.registerObject("bridge", bridge)
  view.page().setWebChannel(channel)

  show_dir()
  view.resize(1000, 800)
  view.show()
  return app.exec()

if __name__ == "__main__":
    sys.exit(main())
