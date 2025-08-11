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
                "6 минут": {"hours": 0, "minutes": 6, "seconds": 0},
                "10 минут": {"hours": 0, "minutes": 10},
                "1 час": {"hours": 1, "minutes": 0},
                "2 часа": {"hours": 2, "minutes": 0}
            },
            "theme": "light",
            "check_interval": 5,
            # Интервалы/задержки в миллисекундах
            "periodic_tasks_interval_ms": 1000,
            "process_check_interval_ms": 5000,
            "notification_check_delay_ms": 10000,
            "notification_countdown_seconds": 15,
            "passive_logging_interval_ms": 600000,
            "autostart": False,
            "hotkeys": {
                "pause": "ctrl+space",
                "reset": "ctrl+r"
            },
            "block_delay": 30,
            "notification_sound": True,
            "start_minimized": False,
            "block_screen_message": "Время игры истекло!\nПожалуйста, сделайте перерыв.",
            # Параметры логирования
            "logging": {
                "file_level": "DEBUG",
                "console_level": "WARNING",
                "max_bytes": 1000000,
                "backup_count": 5,
                "log_dir": "logs",
                "log_file": "game_timer.log"
            },
            # Горячие клавиши
            "hotkeys": {
                "start": "ctrl+alt+s",
                "pause_resume": "ctrl+alt+p",
                "reset": "ctrl+alt+r",
                "add_5_min": "ctrl+alt+plus"
            },
            # Лимиты и перерывы (cooldown)
            "daily_limit_hours": 4,
            "enforced_rest_minutes": 60,
            "block_until_next_day_on_limit": True,
            "enforce_cooldown_between_sessions": True,
            # Конец текущего перерыва в ISO-формате (локальное время). Пусто, если перерыва нет
            "rest_until": "",
            # Авто-запуск таймера при обнаружении игры
            "auto_start_on_game_detect": True,
            "auto_start_mode": "countup",  # 'countup' или 'countdown'
            "auto_countdown_seconds": 3600,  # если выбран countdown
            "auto_prompt_text": "Обнаружена игра. Начать таймер?",
            "auto_prompt_snooze_minutes": 5,
            # Подписи к ключевым настройкам (для удобства редактирования в settings.json)
            "settings_descriptions": {
                "mode": "Режим работы таймера: 'timer' — отсчет вниз, может быть и другие режимы при расширении",
                "hours": "Стартовые часы таймера для сессии (целое число)",
                "minutes": "Стартовые минуты таймера для сессии (целое число)",
                "processes": "Список исполняемых файлов игр/приложений для мониторинга (можно добавлять/удалять строки)",
                "presets": "Набор пресетов на главном экране. Можно добавлять/удалять. Формат: имя: {hours, minutes, seconds}",
                "theme": "Тема интерфейса: 'light' или 'dark' (если поддерживается)",
                "check_interval": "Интервал (сек) для некоторых проверок в приложении",
                "periodic_tasks_interval_ms": "Период (мс) запуска фоновых задач UI (1 000 = 1 сек)",
                "process_check_interval_ms": "Период (мс) сканирования запущенных процессов (5 000 = каждые 5 сек)",
                "notification_check_delay_ms": "Через сколько мс после уведомления проверить, закрыта ли игра (по умолчанию 10 000)",
                "notification_countdown_seconds": "Сколько секунд показывать обратный отсчёт перед блокировкой",
                "passive_logging_interval_ms": "Раз в сколько мс писать пассивные записи логов (600 000 = 10 минут)",
                "autostart": "Автозапуск приложения при старте системы (true/false)",
                "hotkeys": "Горячие клавиши приложения. Можно менять сочетания (например 'ctrl+alt+s')",
                "block_delay": "Задержка (сек) перед началом принудительной блокировки после уведомления",
                "notification_sound": "Включить звук уведомления (true/false)",
                "start_minimized": "Запускать свернутым (true/false)",
                "block_screen_message": "Текст сообщения на экране блокировки",
                "daily_limit_hours": "Дневной лимит игрового времени (часы). Пример: 4 или 6",
                "enforced_rest_minutes": "Обязательный перерыв после принудительной блокировки (минуты). Пример: 60",
                "block_until_next_day_on_limit": "Если true — при достижении дневного лимита блокируем до следующего дня",
                "enforce_cooldown_between_sessions": "Если true — после принудительной блокировки включается перерыв (cooldown)",
                "rest_until": "Техническое поле: время окончания текущего перерыва в ISO-формате. Лучше не менять вручную",
                "auto_start_on_game_detect": "Если true — при запуске отслеживаемой игры будет показан вопрос и можно автоматически запустить таймер",
                "auto_start_mode": "Режим авто-таймера: 'countup' — прямой отсчет, 'countdown' — обратный",
                "auto_countdown_seconds": "Длительность (сек), если выбран режим 'countdown' (по умолчанию 3600 = 1 час)",
                "auto_prompt_text": "Текст вопроса в окне при обнаружении игры",
                "auto_prompt_snooze_minutes": "Через сколько минут повторно спрашивать, если нажали 'Нет' или закрыли окно"
            }
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