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

  @pyqtSlot()
  def goBack(self):
    self.reload_func('..')

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

    rel_path = os.path.relpath(cur_dir, base_img_dir)
    if rel_path == '.':
      rel_path = 'img/'
    else:
      rel_path = 'img/' + rel_path.replace('\\', '/') + '/'

    # 讀取外部 HTML template
    template_path = Path(__file__).parent / 'static' / 'template.html'
    with open(template_path, encoding='utf-8') as f:
        html_tpl = f.read()
    html = html_tpl.replace('{{folder_tags}}', folder_tags).replace('{{img_tags}}', img_tags).replace('{{rel_path}}', rel_path)
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
