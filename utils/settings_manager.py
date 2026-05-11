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
        cls._save_setting('last_pptx_path', path)

    @classmethod
    def get_video_storage_folder(cls):
        """Videoların kalıcı olarak kaydedileceği varsayılan klasörü döndürür."""
        if os.path.exists(cls.SETTINGS_FILE):
            with open(cls.SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                folder = data.get('video_storage_folder', '')
                if folder and os.path.isdir(folder):
                    return folder
        return ''

    @classmethod
    def set_video_storage_folder(cls, folder):
        cls._save_setting('video_storage_folder', folder)

    @classmethod
    def _save_setting(cls, key, value):
        data = {}
        if os.path.exists(cls.SETTINGS_FILE):
            with open(cls.SETTINGS_FILE, 'r') as f:
                data = json.load(f)
        data[key] = value
        os.makedirs(os.path.dirname(cls.SETTINGS_FILE), exist_ok=True)
        with open(cls.SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)