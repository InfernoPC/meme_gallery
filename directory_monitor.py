from watchdog.events import FileSystemEventHandler

class DirectoryMonitor(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        if event.src_path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            self.app.display_images()
