"""
Файл: logger.py

Модуль-обёртка для логирования событий приложения Game Timer.
"""

import logging
import os
from datetime import datetime
import getpass
import sys
import uuid
from logging.handlers import RotatingFileHandler

# Генерируем session_id при первом импорте
SESSION_ID = uuid.uuid4().hex[:8]
USER = getpass.getuser()
PID = os.getpid()

class ContextFormatter(logging.Formatter):
    def format(self, record):
        record.user = USER
        record.pid = PID
        record.session = SESSION_ID
        record.func = record.funcName
        record.lineno = record.lineno
        return super().format(record)

class Logger:
    def __init__(self, name="game_timer", log_file=None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Очищаем существующие обработчики
        self.logger.handlers = []
        
        # Создаем директорию для логов если её нет
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Определяем путь к лог-файлу
        if log_file is None:
            log_file = os.path.join(log_dir, "game_timer.log")
        
        # Rotating file handler
        file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Формат логов
        fmt = (
            "%(asctime)s | user=%(user)s | pid=%(pid)s | session=%(session)s | "
            "%(name)s.%(func)s:%(lineno)d | %(levelname)s | %(message)s"
        )
        formatter = ContextFormatter(fmt)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(message, stacklevel=2)

    def info(self, message):
        self.logger.info(message, stacklevel=2)

    def warning(self, message):
        self.logger.warning(message, stacklevel=2)

    def error(self, message, exc_info=True):
        self.logger.error(message, exc_info=exc_info, stacklevel=2)

    def critical(self, message, exc_info=True):
        self.logger.critical(message, exc_info=exc_info, stacklevel=2)
        self.logger.critical(message)
