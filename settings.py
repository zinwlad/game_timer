from logger import Logger
import json

class Settings:
    """Класс для работы с настройками"""
    def __init__(self, filename="timer_settings.json"):
        self.logger = Logger("Settings")
        self.filename = filename
        self.default_settings = {
            "mode": "timer",
            "hours": 2,
            "minutes": 0,
            "processes": ["game.exe", "minecraft.exe", "CorelDRW.exe"],
            "presets": {
                "30 минут": {"hours": 0, "minutes": 30},
                "1 час": {"hours": 1, "minutes": 0},
                "2 часа": {"hours": 2, "minutes": 0}
            },
            "theme": "light",
            "check_interval": 5,
            "autostart": False,
            "hotkeys": {
                "pause": "ctrl+space",
                "reset": "ctrl+r"
            }
        }
        self.settings = self.default_settings.copy()

    def get(self, key, default=None):
        """Получение значения настройки"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Установка значения настройки"""
        self.settings[key] = value
        self.save()

    def save(self):
        """Сохранение настроек в файл"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            self.logger.info("Settings saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            raise

    # Additional methods and logic for Settings class
