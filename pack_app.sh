#!/bin/bash

# 切換到腳本所在目錄
cd "$(dirname "$0")"

# 用 pyinstaller 打包
pyinstaller --noconsole --onefile --name MemeGalleryApp \
  --add-data "font_dialog.py:." \
  --add-data "font_manager.py:." \
  --add-data "image_manager.py:." \
  --add-data "rename_dialog.py:." \
  --add-data "meme_gallery_app.py:." \
  --add-data "directory_monitor.py:." \
  --add-data "icon.png:." app.py

# 移動執行檔到當前目錄
mv -f dist/MemeGalleryApp.exe .

# 清理 build、dist 目錄和 spec 檔
rm -rf build dist MemeGalleryApp.spec
