import json
import os

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.create_default_config()
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def create_default_config(self):
        default_config = {
            "font_family": "NaikaiFont",
            "font_size": 12,
            "image_dir": "img/",
            "image_width": 150,
            "window_geometry": "800x600"
        }
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
