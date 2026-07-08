import json
import os

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")


class ConfigManager:
    """Persists recently-used field values in a JSON file next to the app."""

    MAX_HISTORY = 10

    def __init__(self, config_file=_DEFAULT_PATH):
        self.config_file = config_file

    def _load(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            return {}

    def _save(self, data):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except OSError:
            pass  # history is a convenience; never crash the app over it

    def add_to_history(self, key, value):
        if not value:
            return
        data = self._load()
        history = data.get(key, [])
        if value in history:
            history.remove(value)
        history.insert(0, value)
        data[key] = history[:self.MAX_HISTORY]
        self._save(data)

    def get_history(self, key):
        history = self._load().get(key, [])
        return history if isinstance(history, list) else []

    def set_value(self, key, value):
        data = self._load()
        data[key] = value
        self._save(data)

    def get_value(self, key, default=""):
        value = self._load().get(key, default)
        return value if isinstance(value, str) else default
