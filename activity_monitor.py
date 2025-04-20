"""
Файл: activity_monitor.py

Модуль для мониторинга активности пользователя (мышь, клавиатура) для автопаузы таймера в Game Timer.
"""

import time
import pyautogui
import keyboard
from typing import Dict, Any, Tuple, Optional
from logger import Logger

class ActivityMonitor:
    """Монитор активности пользователя"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.logger = Logger("ActivityMonitor")
        self.settings = settings
        self.last_mouse_pos = pyautogui.position()
        self.last_activity_time = time.time()
        self.inactivity_timeout = settings.get("inactivity_timeout", 300)
        self.logger.info("ActivityMonitor initialized")
        
    def check_activity(self) -> Tuple[bool, float]:
        """
        Проверяет активность пользователя
        Возвращает: (активен ли пользователь, время с последней активности)
        """
        try:
            current_pos = pyautogui.position()
            current_time = time.time()
            
            # Проверяем движение мыши и активность клавиатуры
            if (current_pos != self.last_mouse_pos or 
                any(keyboard.is_pressed(key) 
                    for key in self.settings.get("hotkeys", {}).values())):
                self.last_activity_time = current_time
                self.last_mouse_pos = current_pos
                
            inactivity_duration = current_time - self.last_activity_time
            is_active = inactivity_duration <= self.inactivity_timeout
            
            return is_active, inactivity_duration
            
        except Exception as e:
            self.logger.error(f"Error checking activity: {str(e)}")
            return True, 0.0  # В случае ошибки считаем пользователя активным
            
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Обновляет настройки монитора"""
        try:
            self.settings = settings
            self.inactivity_timeout = settings.get("inactivity_timeout", 300)
            self.logger.info("Settings updated")
        except Exception as e:
            self.logger.error(f"Error updating settings: {str(e)}")
            
    def reset_activity(self) -> None:
        """Сбрасывает таймер активности"""
        try:
            self.last_activity_time = time.time()
            self.last_mouse_pos = pyautogui.position()
            self.logger.debug("Activity timer reset")
        except Exception as e:
            self.logger.error(f"Error resetting activity: {str(e)}")
            
    def get_last_activity_time(self) -> Optional[float]:
        """Возвращает время последней активности"""
        return self.last_activity_time
