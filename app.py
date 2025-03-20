import tkinter as tk
from meme_gallery_app import MemeGalleryApp  # Import the new MemeGalleryApp class

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap('icon.png')  # Set the app icon
    app = MemeGalleryApp(root)
    root.mainloop()