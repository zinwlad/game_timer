from datetime import datetime
import winsound
from notification_window import NotificationWindow
import threading
import logging
import time
import psutil

# Настройка логгера
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TimerManager')

class TimerManager:
    def __init__(self, root, game_blocker, ui_manager, settings, notification_enabled=True):
        from PyQt5 import QtCore
        self.root = root
        self.game_blocker = game_blocker
        self.ui_manager = ui_manager
        self.settings = settings
        
        self.running = False
        self.paused = False
        self.remaining_time = 0
        self.mode = "countdown"
        self._start_time = None  # Для расчета прошедшего времени
        self._elapsed_before_pause = 0
        
        # Инициализация логгера
        self.logger = logging.getLogger('TimerManager')
        
        self.qtimer = QtCore.QTimer()
        self.qtimer.setInterval(1000)
        self.qtimer.timeout.connect(self.update_timer)
        self.notification_enabled = notification_enabled
        # Убираем создание кнопок отсюда, теперь они будут передаваться через set_ui_elements


    def start_timer(self, total_seconds, mode):
        """Запуск таймера"""
        try:
            self.logger.info(f"Starting timer: {total_seconds} seconds, mode: {mode}")
            total_seconds = int(total_seconds)
            
            if total_seconds < 0:
                raise ValueError("Negative time value")

            # Поддержка русских и английских названий режимов
            if mode.lower() in ["countdown", "обратный отсчет"]:
                self.mode = "countdown"
            else:
                self.mode = "countup"
            self.remaining_time = total_seconds if self.mode == "countdown" else 0
            self.running = True
            self.paused = False
            self._start_time = time.time()
            self._elapsed_before_pause = 0
            self.update_timer_display()
            self.update_button_states()
            self.qtimer.start(1000)
        except Exception as e:
            self.logger.error(f"Error starting timer: {str(e)}")
            return False

    def pause_timer(self):
        """Пауза таймера"""
        if not self.running or self.paused:
            return
        self.paused = True
        self._elapsed_before_pause += time.time() - self._start_time
        self.qtimer.stop()
        self.update_button_states()
        self.logger.info("Timer paused")

    def resume_timer(self):
        """Продолжение таймера"""
        if not self.running or not self.paused:
            return
        self.paused = False
        self._start_time = time.time()
        self.qtimer.start(1000)
        self.update_button_states()
        self.logger.info("Timer resumed")

    def reset_timer(self):
        """Сбрасывает таймер"""
        self.running = False
        self.paused = False
        self.remaining_time = 0
        self._start_time = None
        self._elapsed_before_pause = 0
        self.qtimer.stop()
        self.update_timer_display()
        self.update_button_states()
        self.logger.info("Timer reset")

    def update_timer_display(self):
        """Обновляет отображение времени"""
        try:
            if not self.running and not hasattr(self, 'time_display'):
                return
            hours = self.remaining_time // 3600
            minutes = (self.remaining_time % 3600) // 60
            seconds = self.remaining_time % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            # Если есть time_display (например, QLabel), обновляем его
            if hasattr(self, 'time_display'):
                self.time_display.setText(time_str)
            self.logger.debug(f"Display updated: {time_str}")
        except Exception as e:
            self.logger.error(f"Error updating display: {str(e)}")

            
    def update_button_states(self):
        """Обновляет состояние кнопок (PyQt5)"""
        try:
            if hasattr(self, 'start_button'):
                self.start_button.setEnabled(not self.running)
            if hasattr(self, 'pause_button'):
                self.pause_button.setEnabled(self.running)
                self.pause_button.setText("Продолжить" if self.paused else "Пауза")
            if hasattr(self, 'reset_button'):
                self.reset_button.setEnabled(self.running)
        except Exception as e:
            self.logger.error(f"Error updating button states: {str(e)}")


    def update_timer(self):
        """Обновляет таймер"""
        try:
            if not self.running or self.paused:
                return

            if self.mode == "countdown":
                if self.remaining_time > 0:
                    self.remaining_time -= 1
                    self.update_timer_display()
                    self.qtimer.start(1000)
                else:
                    self.running = False
                    self.qtimer.stop()
                    self._handle_timer_expiration()
                    return
            else:  # countup
                self.remaining_time += 1
                self.update_timer_display()
                self.qtimer.start(1000)
                
        except Exception as e:
            self.logger.error(f"Error in update_timer: {str(e)}")
            # Пытаемся восстановить таймер
            if self.running and not self.paused:
                self.qtimer.start(1000)

    def _finalize_timer_expiration(self):
        """Завершает таймер"""
        self.running = False
        self.paused = False
        self.update_timer_display()
        self.update_button_states()
        self._start_time = None
        self._elapsed_before_pause = 0
        self.game_blocker.update_timer_state(True)

    def _handle_timer_expiration(self):
        """Обрабатывает истечение таймера"""
        self.running = False
        self.qtimer.stop()
        self._finalize_timer_expiration()
        if self.notification_enabled:
            # Показываем уведомление о завершении таймера с callback
            self.notification_closed = False
            def on_notification_close():
                self.notification_closed = True
            notification = NotificationWindow("Время истекло!", "Пора сделать перерыв!\nПожалуйста, закройте игру и нажмите ОК.", on_close_callback=on_notification_close)
            notification.exec_()  # Модально ждём закрытия окна
            # После нажатия ОК ищем запущенные игры и посылаем ESC, не завершаем процессы
            import ctypes
            import time
            import sys
            import platform
            import psutil
            import os
            import signal
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            import subprocess

            games_were_running = False
            for proc_name in self.settings.get("processes", []):
                for proc in psutil.process_iter(['name', 'exe', 'pid']):
                    try:
                        if not proc.info or 'name' not in proc.info:
                            continue
                        pname = proc.info['name'].lower() if proc.info.get('name') else ''
                        ppath = proc.info.get('exe', '').lower() if proc.info.get('exe') else ''
                        if proc_name.lower() in pname or proc_name.lower() in ppath:
                            games_were_running = True
                            # Попытаться отправить ESC в окно процесса (только для Windows)
                            try:
                                import win32gui, win32con, win32process
                                pid = proc.info['pid']
                                def enum_handler(hwnd, result):
                                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                                    if found_pid == pid:
                                        # Активируем окно
                                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                        win32gui.SetForegroundWindow(hwnd)
                                        # Отправляем ESC
                                        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, 0x1B, 0)
                                        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, 0x1B, 0)
                                win32gui.EnumWindows(enum_handler, None)
                            except Exception as esc_e:
                                self.logger.warning(f"Не удалось послать ESC процессу {pname}: {esc_e}")
                    except Exception:
                        continue
            if games_were_running:
                # Показываем уведомление и блокируем
                self.notification_closed = False
                def on_notification_close():
                    self.notification_closed = True
                notification = NotificationWindow("Время истекло!", "Пора сделать перерыв!\nПожалуйста, закройте игру и нажмите ОК.", on_close_callback=on_notification_close)
                notification.exec_()
                self.game_blocker.start_blocking_sequence()
                self.logger.info("Timer expired successfully")
                try:
                    winsound.PlaySound('SystemExclamation', winsound.SND_ASYNC)
                except Exception:
                    pass
            else:
                self.logger.info("Таймер завершился, но ни одной игры не было запущено — блокировка не требуется.")
                pass


    def is_running(self):
        """Возвращает True, если таймер запущен."""
        return self.running

    def is_paused(self):
        """Возвращает True, если таймер на паузе."""
        return self.paused

    def set_ui_elements(self, time_display, start_button, pause_button, reset_button):
        """Устанавливает UI элементы для таймера"""
        self.time_display = time_display
        self.start_button = start_button
        self.pause_button = pause_button
        self.reset_button = reset_button
        self.update_timer_display()
        
    def get_elapsed_time(self):
        """Возвращает прошедшее время в секундах с момента запуска таймера (для достижений)"""
        if not self.running and self._elapsed_before_pause == 0:
            return 0
        elapsed = self._elapsed_before_pause
        if self.running and not self.paused and self._start_time is not None:
            elapsed += time.time() - self._start_time
        return int(elapsed)

    def timer_expired(self):
        """Обработка истечения таймера"""
        self.running = False
        self.game_blocker.update_timer_state(True)
        winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
        
        if hasattr(self.ui_manager, 'show_notification'):
            self.ui_manager.show_notification(
                "Время истекло!",
                "Пора сделать перерыв!"
            )
