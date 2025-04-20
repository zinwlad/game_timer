import logging
import pystray
"""
Файл: tray_manager.py

Модуль для управления значком приложения в системном трее и взаимодействия через контекстное меню.
Используется в приложении Game Timer.
"""
from PIL import Image
import os
import tkinter as tk
from typing import Callable

class TrayManager:
    def __init__(self, show_window_callback: Callable, quit_callback: Callable):
        """Инициализация менеджера трея"""
        self.logger = logging.getLogger('TrayManager')
        self.show_window_callback = show_window_callback
        self.quit_callback = quit_callback
        self.icon = None
        self._setup_tray_icon()
        
    def _create_menu(self):
        """Создает меню для иконки в трее"""
        return pystray.Menu(
            pystray.MenuItem("Показать", self._show_window),
            pystray.MenuItem("Выход", self._quit_app)
        )
        
    def _setup_tray_icon(self):
        """Настройка иконки в трее"""
        try:
            # Создаем простую иконку
            image = Image.new('RGB', (64, 64), color='red')
            
            # Если есть файл иконки Icon_game_timer.png в корне проекта, используем его
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            icon_path = os.path.join(project_root, 'Icon_game_timer.png')
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
            else:
                # fallback: icon.png рядом с этим файлом
                local_icon = os.path.join(os.path.dirname(__file__), 'icon.png')
                if os.path.exists(local_icon):
                    image = Image.open(local_icon)
            
            # Создаем иконку
            self.icon = pystray.Icon(
                "game_timer",
                image,
                "Game Timer",
                self._create_menu()
            )
            
            # Запускаем иконку в отдельном потоке
            self.icon.run_detached()
            self.logger.info("Tray icon initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup tray icon: {str(e)}")
            
    def _show_window(self):
        """Показывает главное окно"""
        try:
            self.show_window_callback()
        except Exception as e:
            self.logger.error(f"Failed to show window: {str(e)}")
            
    def _quit_app(self):
        """Закрывает приложение"""
        try:
            self.stop()
            self.quit_callback()
        except Exception as e:
            self.logger.error(f"Failed to quit app: {str(e)}")
            
    def stop(self):
        """Останавливает иконку в трее"""
        try:
            if self.icon:
                self.icon.stop()
                self.logger.info("Tray icon stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop tray icon: {str(e)}")
            
    def update_icon(self, icon_path: str):
        """Обновляет иконку"""
        try:
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                if self.icon:
                    self.icon.icon = image
                    self.logger.info("Tray icon updated")
        except Exception as e:
            self.logger.error(f"Failed to update icon: {str(e)}")
