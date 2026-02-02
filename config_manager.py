import json
import os

class ConfigManager:
    def __init__(self, config_file="history.json"):
        self.config_file = config_file
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_file):
            self.save_all({})

    def load_history(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_all(self, data):
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=4)

    def add_to_history(self, key, value):
        if not value:
            return
            
        data = self.load_history()
        if key not in data:
            data[key] = []
        
        # Avoid duplicates and move to top
        if value in data[key]:
            data[key].remove(value)
        
        data[key].insert(0, value)
        
        # Limit history size (optional, e.g., keep last 10)
        data[key] = data[key][:10]
        
        self.save_all(data)

    def get_history(self, key):
        data = self.load_history()
        return data.get(key, [])
