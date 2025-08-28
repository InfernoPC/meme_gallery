# pip install PyQt6 PyQt6-WebEngine
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QObject, pyqtSlot, QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QMimeData
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import sys, os

HTML_TMPL = """
<!doctype html>
<html>
<head>
<meta charset=\"utf-8\" />
<title>APNG WebView</title>
<style>
  html,body{{height:100%;margin:0}}
  #navbox{{position:fixed;top:0;left:0;width:100vw;background:#222;color:#fff;padding:10px 0 6px 0;z-index:20;display:flex;align-items:center;}}
  #navbox button{{margin-left:16px;margin-right:16px;padding:4px 12px;font-size:15px;}}
  #navbox .path{{font-size:13px;opacity:.7;user-select:all;}}
  #wrap{{min-height:100vh;display:flex;flex-wrap:wrap;align-items:flex-start;justify-content:center;background:#111;padding-top:60px;}}
  .folderbox,.imgbox{{margin:12px;background:#222;padding:8px 8px 0 8px;border-radius:10px;box-shadow:0 2px 8px #0004;display:flex;flex-direction:column;align-items:center;width:336px;min-height:304px;box-sizing:border-box;}}
  .folderbox{{cursor:pointer;}}
  .foldericon{{font-size:120px;width:320px;height:240px;display:flex;align-items:center;justify-content:center;}}
  .foldername{{color:#ffb84d;font-size:16px;margin-bottom:8px;word-break:break-all;max-width:320px;text-align:center;}}
  .imgbox img{{max-width:320px;max-height:240px;cursor:pointer;display:block;}}
  /* 針對 gif/apng 動圖加上動畫效果（瀏覽器自動循環） */
  .imgbox img[alt$='.gif'], .imgbox img[alt$='.apng']{{animation: none;}}
  .imgbox .imgname{{color:#fff;font-size:16px;margin:16px 0 8px 0;word-break:break-all;max-width:320px;text-align:center;}}
  #hint{{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);color:#fff;background:rgba(0,0,0,.6);padding:8px 12px;border-radius:8px;font:14px/1.4 system-ui;opacity:0;transition:opacity .2s;z-index:100;}}
</style>
<script src=\"qrc:///qtwebchannel/qwebchannel.js\"></script>
</head>
<body>
<div id=\"navbox\">
  <button id=\"backbtn\">⬅ 上一層</button>
  <span class=\"path\">{rel_path}</span>
</div>
<div id=\"wrap\">
  {folder_tags}
  {img_tags}
</div>
<div id=\"hint\">已複製檔案到剪貼簿</div>
<script>
  // 初始化 WebChannel
  new QWebChannel(qt.webChannelTransport, function(channel){{
    const bridge = channel.objects.bridge;
    const hint = document.getElementById('hint');
    document.querySelectorAll('.imgbox img').forEach(function(img){{
      img.addEventListener('click', function(){{
        bridge.copyApngFile(img.getAttribute('data-path'));
        hint.textContent = '已複製檔案到剪貼簿';
        hint.style.opacity = 1;
        setTimeout(()=> hint.style.opacity = 0, 900);
      }});
      img.addEventListener('dragstart', e => e.preventDefault());
    }});
    document.querySelectorAll('.folderbox').forEach(function(box){{
      box.addEventListener('click', function(){{
        bridge.openFolder(box.getAttribute('data-folder'));
      }});
    }});
    document.getElementById('backbtn').addEventListener('click', function(){{
      bridge.goBack();
    }});
  }});
</script>
</body>
</html>
"""

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

    dir_url = QUrl.fromLocalFile(cur_dir + os.sep)
    html = HTML_TMPL.format(folder_tags=folder_tags, img_tags=img_tags, rel_path=rel_path)
    view.setHtml(html, baseUrl=dir_url)

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
