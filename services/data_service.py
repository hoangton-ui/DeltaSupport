import json
import os
from utils.resource_manager import resource_manager

class DataService:
    _instance = None
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataService, cls).__new__(cls)
        return cls._instance

    def get_data(self, filename, force_reload=False):
        if not force_reload and filename in self._cache:
            return self._cache[filename]

        file_path = resource_manager.get_data_file_path(filename)
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[filename] = data
                return data
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return []

    def clear_cache(self, filename=None):
        if filename:
            self._cache.pop(filename, None)
        else:
            self._cache.clear()

data_service = DataService()
