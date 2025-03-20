@echo off

REM Navigate to the directory containing the app
cd /d "%~dp0"

REM Use pyinstaller to pack app.py and related files into an executable
pyinstaller --noconsole --onefile --name MemeGalleryApp --add-data "font_dialog.py;." --add-data "font_manager.py;." --add-data "image_manager.py;." --add-data "rename_dialog.py;." --add-data "meme_gallery_app.py;." --add-data "directory_monitor.py;." --add-data "icon.png;." app.py

REM Move the executable to the current directory
move /y dist\MemeGalleryApp.exe .

REM Clean up build files
rmdir /s /q build
rmdir /s /q dist
del MemeGalleryApp.spec
