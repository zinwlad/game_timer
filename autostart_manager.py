import winreg
"""
Файл: autostart_manager.py

Модуль для управления автозапуском приложения Game Timer при старте системы (Windows).
"""

import sys
from logger import Logger
from typing import Optional

class AutostartManager:
    """Менеджер автозапуска приложения"""
    
    def __init__(self):
        self.logger = Logger("AutostartManager")
        self.key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.app_name = "GameTimer"
        
    def set_autostart(self, enable: bool = True) -> bool:
        """Включение/выключение автозапуска"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                self.key_path, 
                0, 
                winreg.KEY_ALL_ACCESS
            )
            
            if enable:
                winreg.SetValueEx(
                    key, 
                    self.app_name, 
                    0, 
                    winreg.REG_SZ, 
                    sys.argv[0]
                )
                self.logger.info("Autostart enabled")
            else:
                winreg.DeleteValue(key, self.app_name)
                self.logger.info("Autostart disabled")
                
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring autostart: {str(e)}")
            return False
            
    def is_autostart_enabled(self) -> bool:
        """Проверяет, включен ли автозапуск"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                self.key_path, 
                0, 
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking autostart status: {str(e)}")
            return False
            
    def get_autostart_path(self) -> Optional[str]:
        """Возвращает путь к исполняемому файлу в автозапуске"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                self.key_path, 
                0, 
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return value
            except FileNotFoundError:
                winreg.CloseKey(key)
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting autostart path: {str(e)}")
            return None
