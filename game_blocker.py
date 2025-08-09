from logger import Logger
import threading
import time
import psutil
from block_screen import BlockScreen
import json
"""
Файл: game_blocker.py

Модуль для блокировки игр и управления блокировкой по лимиту времени в приложении Game Timer.
"""

import os

class GameBlocker:
    def __init__(self, settings):
        """Инициализация блокировщика игр"""
        self.settings = settings
        self.logger = Logger('GameBlocker')
        self.block_screen = None
        self.timer_expired = False  # Флаг истечения таймера

    def update_timer_state(self, expired):
        """Обновляет состояние таймера (истек/не истек)"""
        self.timer_expired = expired
        self.logger.debug(f"Timer state updated: expired={expired}")

    def start_blocking_sequence(self):
        """Запускает окно блокировки с отсчетом (через PyQt5 BlockScreen)"""
        try:
            if self.block_screen and self.block_screen.isVisible():
                return

            countdown_seconds = self.settings.get("block_delay", 10)
            self.block_screen = BlockScreen(self.settings, countdown_seconds=countdown_seconds)
            self.block_screen.exec_()
            self.logger.info("BlockScreen (PyQt5) was shown.")
        except Exception as e:
            self.logger.error(f"Error showing BlockScreen (PyQt5): {e}")

    def unblock(self):
        """Закрывает окно блокировки, если оно открыто."""
        if self.block_screen and self.block_screen.isVisible():
            self.logger.info("Unblocking screen via hotkey.")
            self.block_screen.accept()
            self.block_screen = None

