"""
Файл: settings_manager.py

Модуль для загрузки, сохранения и управления настройками пользователя в приложении Game Timer.
"""

import json
import os
import time
from logger import Logger

class SettingsManager:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.settings = {}
        self.logger = Logger("SettingsManager")
        # Вспомогательные поля для троттлинга сохранений
        self._last_save_ts = 0.0
        self._save_interval_sec = 5.0  # не чаще одного сохранения в 5 секунд
        self._last_saved_snapshot = None
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
            },
            "block_delay": 30,
            "notification_sound": True,
            "start_minimized": False,
            "block_screen_message": "Время игры истекло!\nПожалуйста, сделайте перерыв."
        }
        self.load()

    def load(self):
        """Загружает настройки из файла"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                    self.logger.info("Settings loaded successfully")
            else:
                self.settings = self.default_settings.copy()
                self.save()
                self.logger.info("Created default settings")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error loading settings: Invalid JSON format. {e}")
            self.settings = self.default_settings.copy()
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            self.settings = self.default_settings.copy()

    def save(self):
        """Сохраняет настройки в файл"""
        try:
            # Преобразуем объекты типа set в list перед сохранением
            settings_to_save = self._convert_sets_to_lists(self.settings)
            # Избегаем лишних записей, если ничего не изменилось
            current_snapshot = json.dumps(settings_to_save, sort_keys=True, ensure_ascii=False)
            if self._last_saved_snapshot == current_snapshot:
                return
            # Троттлинг частых сохранений
            now = time.time()
            if (now - self._last_save_ts) < self._save_interval_sec:
                return
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=4, ensure_ascii=False)
            self._last_saved_snapshot = current_snapshot
            self._last_save_ts = now
            self.logger.debug("Settings saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def _convert_sets_to_lists(self, data):
        """Рекурсивно преобразует все объекты типа set в list"""
        if isinstance(data, set):
            return list(data)
        elif isinstance(data, dict):
            return {key: self._convert_sets_to_lists(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._convert_sets_to_lists(item) for item in data]
        return data

    def get(self, key, default=None):
        """Получает значение настройки"""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Устанавливает значение настройки"""
        self.settings[key] = value
        self.save()