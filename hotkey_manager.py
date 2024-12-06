import keyboard
import queue
import threading
import time
from logger import Logger
from typing import Dict, Callable, Optional

class HotkeyManager:
    """Менеджер горячих клавиш с очередью событий"""
    
    def __init__(self):
        self.logger = Logger("HotkeyManager")
        self.event_queue = queue.Queue()
        self.hotkeys: Dict[str, Callable] = {}
        self.last_event_time: Dict[str, float] = {}
        self.cooldown = 0.1  # Минимальный интервал между событиями (100мс)
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
        self.processing_thread.start()
        self.logger.info("HotkeyManager initialized")

    def add_hotkey(self, hotkey: str, callback: Callable, cooldown: Optional[float] = None) -> None:
        """
        Добавляет горячую клавишу
        :param hotkey: комбинация клавиш (например, 'ctrl+space')
        :param callback: функция обратного вызова
        :param cooldown: опциональное время задержки между срабатываниями (в секундах)
        """
        try:
            if hotkey in self.hotkeys:
                keyboard.remove_hotkey(hotkey)
                
            self.hotkeys[hotkey] = callback
            self.last_event_time[hotkey] = 0
            
            # Создаем обработчик для добавления события в очередь
            def queue_event():
                current_time = time.time()
                if current_time - self.last_event_time.get(hotkey, 0) >= (cooldown or self.cooldown):
                    self.event_queue.put((hotkey, current_time))
                    self.last_event_time[hotkey] = current_time
            
            keyboard.add_hotkey(hotkey, queue_event)
            self.logger.debug(f"Added hotkey: {hotkey}")
            
        except Exception as e:
            self.logger.error(f"Error adding hotkey {hotkey}: {e}")
            raise

    def remove_hotkey(self, hotkey: str) -> None:
        """Удаляет горячую клавишу"""
        try:
            if hotkey in self.hotkeys:
                keyboard.remove_hotkey(hotkey)
                del self.hotkeys[hotkey]
                del self.last_event_time[hotkey]
                self.logger.debug(f"Removed hotkey: {hotkey}")
        except Exception as e:
            self.logger.error(f"Error removing hotkey {hotkey}: {e}")

    def _process_events(self) -> None:
        """Обработка событий из очереди"""
        while self.running:
            try:
                # Ждем событие с таймаутом
                try:
                    hotkey, event_time = self.event_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Проверяем, существует ли еще этот хоткей
                if hotkey in self.hotkeys:
                    try:
                        self.hotkeys[hotkey]()
                    except Exception as e:
                        self.logger.error(f"Error executing hotkey callback for {hotkey}: {e}")
                
                self.event_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in event processing loop: {e}")
                time.sleep(0.1)  # Предотвращаем слишком частые ошибки

    def clear_all_hotkeys(self) -> None:
        """Очищает все горячие клавиши"""
        for hotkey in list(self.hotkeys.keys()):
            self.remove_hotkey(hotkey)

    def __del__(self) -> None:
        """Очистка при удалении объекта"""
        self.running = False
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join(timeout=1.0)
        self.clear_all_hotkeys()
