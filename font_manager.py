from tkinter import font as tkfont

class FontManager:
    def __init__(self, config):
        self.config = config
        self.font_family = self.config.get('font_family', 'NaikaiFont')
        self.font_size = self.config.get('font_size', 12)
        try:
            self.custom_font = tkfont.Font(family=self.font_family, size=self.font_size)
        except tk.TclError:
            self.custom_font = tkfont.Font(size=self.font_size)  # Fallback to default font

    def update_font(self, family, size):
        self.font_family = family
        self.font_size = size
        self.custom_font.config(family=self.font_family, size=self.font_size)
        self.config['font_family'] = self.font_family
        self.config['font_size'] = self.font_size
