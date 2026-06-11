import os
import json

CONFIG_FILE = r"D:\vizhi-spatial-software\config.json"

DEFAULT_CONFIG = {
    "default_rtsp": "rtsp://127.0.0.1:8554/live",
    "capture_interval": 5,
    "gpu_selection": "CUDA:0",
    "theme": "Matte Graphite",
    "autosave": True,
    "default_export_path": r"D:\vizhi-spatial-software\outputs",
    "cache_limit_gb": 10
}

class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.config = dict(DEFAULT_CONFIG)
            cls._instance.load()
        return cls._instance

    def load(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # merge defaults with saved data to ensure all keys exist
                    for k, v in DEFAULT_CONFIG.items():
                        self.config[k] = data.get(k, v)
            else:
                self.save()
        except Exception as e:
            print(f"Error loading config: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        val = self.config.get(key)
        if val is None:
            return DEFAULT_CONFIG.get(key, default)
        return val

    def set(self, key, value):
        self.config[key] = value
        self.save()
