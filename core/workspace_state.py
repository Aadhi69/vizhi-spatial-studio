import os
import json

STATE_FILE = r"D:\vizhi-spatial-software\workspace_state.json"

DEFAULT_STATE = {
    "window_width": 1900,
    "window_height": 1050,
    "maximized": True,
    "fullscreen": False,
    "horizontal_splitter": [240, 1660],
    "middle_splitter": [1360, 300],
    "vertical_splitter": [900, 150],
    "active_project_path": "",
    "rtsp_url": "rtsp://127.0.0.1:8554/live",
    "sidebar_visible": True,
    "right_panel_visible": True,
    "logs_visible": True
}

class WorkspaceState:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WorkspaceState, cls).__new__(cls, *args, **kwargs)
            cls._instance.state = dict(DEFAULT_STATE)
            cls._instance.load()
        return cls._instance

    def load(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in DEFAULT_STATE.items():
                        self.state[k] = data.get(k, v)
        except Exception as e:
            print(f"Error loading workspace state: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"Error saving workspace state: {e}")

    def get(self, key, default=None):
        val = self.state.get(key)
        if val is None:
            return DEFAULT_STATE.get(key, default)
        return val

    def set(self, key, value):
        self.state[key] = value
        self.save()
