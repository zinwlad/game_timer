"""
Файл: timer_manager.py

Модуль для управления таймером (countdown и countup), логикой отсчёта времени, обновлением интерфейса и обработкой событий окончания таймера.
Используется в приложении Game Timer.
"""

from datetime import datetime
import winsound
from notification_window import NotificationWindow
import threading
import logging
import time
import psutil

# Настройка логгера управляется центральным Logger; не вызываем basicConfig здесь
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger('TimerManager')

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
        self.expired = False  # Явный флаг истечения таймера
        
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
            self.expired = False
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



    def reset_timer(self):
        """Сбрасывает таймер"""
        self.running = False
        self.paused = False
        self.remaining_time = 0
        self._start_time = None
        self._elapsed_before_pause = 0
        self.expired = False
        self.qtimer.stop()
        self.update_timer_display()
        self.update_button_states()
        self.logger.info("Timer reset")

    def update_timer_display(self):
        """Обновляет отображение времени"""
        try:
            if not self.running:
                return
            hours = self.remaining_time // 3600
            minutes = (self.remaining_time % 3600) // 60
            seconds = self.remaining_time % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            # Обновляем метку в UI
            if hasattr(self.ui_manager, 'time_display'):
                self.ui_manager.time_display.setText(time_str)
            self.logger.debug(f"Display updated: {time_str}")
        except Exception as e:
            self.logger.error(f"Error updating display: {str(e)}")

            
    def update_button_states(self):
        """Обновляет состояние кнопок (PyQt5)"""
        try:
            if hasattr(self.ui_manager, 'start_button'):
                self.ui_manager.start_button.setEnabled(not self.running)
            if hasattr(self.ui_manager, 'pause_button'):
                self.ui_manager.pause_button.setEnabled(self.running)
                self.ui_manager.pause_button.setText("Продолжить" if self.paused else "Пауза")
            if hasattr(self.ui_manager, 'reset_button'):
                self.ui_manager.reset_button.setEnabled(self.running)
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
        self.expired = True

    def _handle_timer_expiration(self):
        self.running = False
        self.qtimer.stop()
        self._finalize_timer_expiration()
        self.game_blocker.update_timer_state(True)

    def is_running(self):
        """Возвращает True, если таймер запущен"""
        return self.running

    def is_expired(self):
        """Возвращает True, если таймер истек"""
        return bool(self.expired)

    def is_paused(self):
        """Возвращает True, если таймер на паузе."""
        return self.paused

    def get_mode(self):
        """Возвращает текущий режим таймера (countdown/countup)."""
        return self.mode

    def set_ui_elements(self, time_display, start_button, pause_button, reset_button):
        """Устанавливает UI элементы для таймера"""
        self.ui_manager.time_display = time_display
        self.ui_manager.start_button = start_button
        self.ui_manager.pause_button = pause_button
        self.ui_manager.reset_button = reset_button
        self.update_timer_display()
        
    def get_elapsed_time(self):
        """Возвращает прошедшее время в секундах с момента запуска таймера (для достижений)"""
        if not self.running and self._elapsed_before_pause == 0:
            return 0
        elapsed = self._elapsed_before_pause
        if self.running and not self.paused and self._start_time is not None:
            elapsed += time.time() - self._start_time
        return int(elapsed)


