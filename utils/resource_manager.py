import os
import customtkinter as ctk
from PIL import Image

class ResourceManager:
    _instance = None
    _icon_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cls._instance.data_path = os.path.join(cls._instance.base_path, "data")
        return cls._instance

    def get_data_file_path(self, filename):
        return os.path.join(self.data_path, filename)

    def load_icon(self, filename, size=(24, 24)):
        cache_key = (filename, size)
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        file_path = self.get_data_file_path(filename)
        if not os.path.exists(file_path):
            return None

        try:
            image = Image.open(file_path)
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)
            self._icon_cache[cache_key] = ctk_image
            return ctk_image
        except Exception:
            return None

    def load_icon_photo(self, filename):
        from PIL import ImageTk
        file_path = self.get_data_file_path(filename)
        if not os.path.exists(file_path):
            return None
        try:
            icon_image = Image.open(file_path)
            return ImageTk.PhotoImage(icon_image)
        except Exception:
            return None

resource_manager = ResourceManager()
