import keyboard
import logging
from typing import Callable

class HotkeyManager:
    def __init__(self):
        """Инициализация менеджера горячих клавиш"""
        self.logger = logging.getLogger('HotkeyManager')
        self.hotkeys = {}
        
    def add_hotkey(self, hotkey: str, callback: Callable):
        """Добавляет горячую клавишу"""
        try:
            keyboard.add_hotkey(hotkey, callback)
            self.hotkeys[hotkey] = callback
            self.logger.info(f"Added hotkey: {hotkey}")
        except Exception as e:
            self.logger.error(f"Failed to add hotkey {hotkey}: {str(e)}")
            
    def remove_hotkey(self, hotkey: str):
        """Удаляет горячую клавишу"""
        try:
            if hotkey in self.hotkeys:
                keyboard.remove_hotkey(hotkey)
                del self.hotkeys[hotkey]
                self.logger.info(f"Removed hotkey: {hotkey}")
        except Exception as e:
            self.logger.error(f"Failed to remove hotkey {hotkey}: {str(e)}")

    def register_limit_hotkeys(self, increase_cb: Callable, decrease_cb: Callable):
        """Регистрирует горячие клавиши для изменения лимита времени (Ctrl+Alt+Up/Down)"""
        try:
            self.add_hotkey('ctrl+alt+up', increase_cb)
            self.add_hotkey('ctrl+alt+down', decrease_cb)
            self.logger.info("Registered limit hotkeys: Ctrl+Alt+Up/Down")
        except Exception as e:
            self.logger.error(f"Failed to register limit hotkeys: {str(e)}")

    def register_blocker_hotkey(self, unblock_cb: Callable):
        """Регистрирует горячую клавишу для быстрого выключения блокировки (Ctrl+Alt+B)"""
        try:
            self.add_hotkey('ctrl+alt+b', unblock_cb)
            self.logger.info("Registered blocker hotkey: Ctrl+Alt+B")
        except Exception as e:
            self.logger.error(f"Failed to register blocker hotkey: {str(e)}")

            if hotkey in self.hotkeys:
                keyboard.remove_hotkey(hotkey)
                del self.hotkeys[hotkey]
                self.logger.info(f"Removed hotkey: {hotkey}")
        except Exception as e:
            self.logger.error(f"Failed to remove hotkey {hotkey}: {str(e)}")
            
    def stop(self):
        """Останавливает все горячие клавиши"""
        try:
            for hotkey in list(self.hotkeys.keys()):
                self.remove_hotkey(hotkey)
            self.logger.info("All hotkeys stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop hotkeys: {str(e)}")
