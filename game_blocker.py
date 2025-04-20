from logger import Logger
import threading
import time
import psutil
from block_screen import BlockScreen
import json
import os
import random
from PIL import Image, ImageTk

class GameBlocker:
    def __init__(self, settings):
        """Инициализация блокировщика игр"""
        self._lock = threading.Lock()
        self.timer_expired = False
        self.block_timer = None
        self.countdown_window = None
        self.block_screen = None
        self.is_monitoring = False
        self.settings = settings
        self.logger = Logger('GameBlocker')
        self.monitored_processes = self.settings.get("processes", [])
        self.block_delay = 3  # ускоренный тест: 3 секунды
        
    def update_timer_state(self, is_expired):
        """Обновляет состояние таймера"""
        with self._lock:
            self.logger.debug(f"[update_timer_state] called with is_expired={is_expired}")
            self.timer_expired = is_expired
            if not is_expired:
                self.block_timer = None
                self._close_countdown_window()
            self.logger.info(f"Timer state updated: expired={is_expired}")
            
    def monitor_games(self):
        """Мониторит запущенные игры"""
        self.logger.info("[monitor_games] Monitoring started")
        self.is_monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        self.logger.debug("[_monitor_loop] Monitoring loop started")
        while self.is_monitoring:
            try:
                if self.timer_expired:
                    self._check_running_games()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {str(e)}", exc_info=True)
                
    def _check_running_games(self):
        """Проверяет запущенные игры"""
        try:
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_info = proc.info
                    if not proc_info:
                        continue
                    proc_name = proc_info.get('name', '')
                    proc_path = proc_info.get('exe', '')
                    proc_name = proc_name.lower() if proc_name else ''
                    proc_path = proc_path.lower() if proc_path else ''
                    
                    if self._is_monitored_process(proc_name, proc_path):
                        self.logger.info(f"Monitored process detected: {proc_name} or {proc_path}")
                        if not self.block_timer:
                            self._start_countdown()
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied) as ex:
                    self.logger.warning(f"Process access error: {ex}")
                    continue
                except Exception as ex:
                    self.logger.error(f"Unexpected process error: {ex}", exc_info=True)
                    continue
            # Если дошли сюда, значит игры не запущены
            if self.block_timer:
                self.logger.info("No monitored games running, closing countdown window.")
                self._close_countdown_window()
        except Exception as e:
            self.logger.error(f"Error checking games: {str(e)}", exc_info=True)
            
    def _is_monitored_process(self, proc_name: str, proc_path: str) -> bool:
        for monitored in self.monitored_processes:
            if not isinstance(monitored, str) or monitored.strip() == "":
                self.logger.debug(f"Skipping invalid monitored process: {monitored!r}")
                continue
            if monitored.lower() in proc_name or monitored.lower() in proc_path:
                self.logger.info(f"Process {proc_name} or {proc_path} matches monitored: {monitored}")
                return True
        return False

    def is_any_monitored_game_running(self):
        """Проверяет, запущена ли хоть одна отслеживаемая игра"""
        try:
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info.get('name', '').lower() if proc_info.get('name') else ''
                    proc_path = proc_info.get('exe', '').lower() if proc_info.get('exe') else ''
                    if self._is_monitored_process(proc_name, proc_path):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        return False

    def start_blocking_sequence(self):
        """Запускает окно блокировки с отсчетом (через PyQt5 BlockScreen)"""
        try:
            # Получить настройки и длительность отсчета
            countdown_seconds = self.settings.get("block_delay", 10)
            # Показать окно блокировки с отсчетом
            block_screen = BlockScreen(self.settings, countdown_seconds=countdown_seconds)
            block_screen.exec_()
            self.logger.info("BlockScreen (PyQt5) was shown.")
        except Exception as e:
            self.logger.error(f"Error showing BlockScreen (PyQt5): {e}")
        return False
        
    def _start_countdown(self):
        """Запускает обратный отсчет перед блокировкой"""
        try:
            self.logger.info("[_start_countdown] Countdown started")
            if not self.countdown_window:
                self.countdown_window = CountdownWindow(self.block_delay)
            self.block_timer = time.time()
        except Exception as e:
            self.logger.error(f"Error starting countdown: {str(e)}", exc_info=True)
            
    def _on_countdown_finished(self):
        """Обработчик завершения обратного отсчета"""
        try:
            self.logger.info("[_on_countdown_finished] Countdown finished, showing block screen")
            if not self.block_screen:
                self.block_screen = BlockScreen(self.settings)
            self.block_screen.show()
        except Exception as e:
            self.logger.error(f"Error showing block screen: {str(e)}", exc_info=True)
            
    def _close_countdown_window(self):
        """Закрывает окно обратного отсчета"""
        try:
            self.logger.info("[_close_countdown_window] Closing countdown window")
            if self.countdown_window:
                self.countdown_window.close()
                self.countdown_window = None
            self.block_timer = None
        except Exception as e:
            self.logger.error(f"Error closing countdown: {str(e)}", exc_info=True)
            
    def stop(self):
        """Останавливает мониторинг"""
        self.logger.info("[stop] Monitoring stopped")
        self.is_monitoring = False
        self._close_countdown_window()
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=1.0)
            
    def update_monitored_processes(self, processes):
        """Обновляет список отслеживаемых процессов"""
        with self._lock:
            self.logger.info(f"[update_monitored_processes] Updating monitored processes: {processes}")
            self.monitored_processes = processes
            self.settings.set("processes", processes)
            self.settings.save()
            
if __name__ == "__main__":
    with open('settings.json') as f:
        settings = json.load(f)
        
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    blocker = GameBlocker(settings)
    blocker.monitor_games()
