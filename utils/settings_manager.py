import json
import os

class SettingsManager:
    SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'user_settings.json')

    @classmethod
    def get_last_pptx_path(cls):
        if os.path.exists(cls.SETTINGS_FILE):
            with open(cls.SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_pptx_path', '')
        return ''

    @classmethod
    def set_last_pptx_path(cls, path):
        with open(cls.SETTINGS_FILE, 'w') as f:
            json.dump({'last_pptx_path': path}, f)