import tkinter as tk
from datetime import datetime
import winsound
from notification_window import NotificationWindow
import threading

class TimerManager:
    def __init__(self, root, game_blocker, ui_manager, settings):
        """
        Инициализация менеджера таймера
        
        Args:
            root: Корневое окно tkinter
            game_blocker: Экземпляр GameBlocker для управления блокировкой игр
            ui_manager: Менеджер UI для обновления интерфейса
            settings: Настройки приложения
        """
        self.root = root
        self.game_blocker = game_blocker
        self.ui_manager = ui_manager
        self.settings = settings
        
        # Состояние таймера
        self.remaining_time = 0
        self.running = False
        self.paused = False
        self.start_time = None  # Время начала отсчета
        
        # UI элементы (будут установлены позже)
        self.timer_label = None
        self.start_button = None
        self.pause_button = None
        self.reset_button = None
        self.mode = None
        
        # Поток мониторинга игр
        self._monitor_thread = None
        
    def set_ui_elements(self, timer_label, start_button, pause_button, reset_button, mode):
        """Установка UI элементов после их создания"""
        self.timer_label = timer_label
        self.start_button = start_button
        self.pause_button = pause_button
        self.reset_button = reset_button
        self.mode = mode
        
    def start_timer(self, hours, minutes):
        """Запуск таймера"""
        try:
            # Проверяем корректность введенных значений
            if hours < 0 or minutes < 0:
                raise ValueError("Время не может быть отрицательным")
                
            if hours == 0 and minutes == 0 and self.mode.get() == "countdown":
                raise ValueError("Установите время больше нуля")
            
            # Сохраняем время начала
            self.start_time = datetime.now()
            
            # Сохраняем настройки
            self.settings.set("hours", hours)
            self.settings.set("minutes", minutes)
            self.settings.save()
            
            # Сбрасываем флаг истечения таймера при старте
            self.game_blocker.timer_expired = False
            
            # Устанавливаем начальное время
            if self.mode.get() == "countdown":
                self.remaining_time = hours * 3600 + minutes * 60
            else:
                self.remaining_time = 0
                
            # Обновляем состояние
            self.running = True
            self.paused = False
            
            # Запускаем мониторинг игр
            if not self._monitor_thread or not self._monitor_thread.is_alive():
                self.game_blocker.is_monitoring = True
                self._monitor_thread = threading.Thread(target=self.game_blocker.monitor_games, daemon=True)
                self._monitor_thread.start()
            
            # Обновляем состояние кнопок
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            
            # Показываем начальное время и запускаем таймер
            self.update_timer_display()  # Показываем время до начала отсчета
            self.update_timer()  # Запускаем отсчет
            self.ui_manager.queue_update('status', "Таймер запущен")
            
            return True
                
        except Exception as e:
            return False, str(e)
            
    def update_timer(self):
        """Обновляет таймер"""
        if not self.running or self.paused:  # Если таймер остановлен или на паузе - не обновляем
            return
            
        if self.mode.get() == "countdown":
            # Режим обратного отсчета
            if self.remaining_time > 0:
                self.update_timer_display()  # Показываем текущее время
                self.remaining_time -= 1     # Уменьшаем время
                self.root.after(1000, self.update_timer)  # Планируем следующее обновление
            else:
                # Таймер истек
                self.running = False
                self.ui_manager.queue_update('status', "Время истекло!")
                self.start_button.config(state=tk.NORMAL)
                self.pause_button.config(state=tk.DISABLED)
                self.reset_button.config(state=tk.NORMAL)
                self.update_timer_display()  # Показываем финальное время
                
                # Создаем и показываем окно уведомления
                notification = NotificationWindow(self.root, "Время вышло!", "Пора сделать перерыв!")
                notification.show()
                
                # После показа уведомления устанавливаем флаг истечения таймера
                self.game_blocker.timer_expired = True
                
        else:
            # Режим прямого отсчета
            self.update_timer_display()  # Показываем текущее время
            self.remaining_time += 1     # Увеличиваем время
            self.root.after(1000, self.update_timer)  # Планируем следующее обновление
            
    def update_timer_display(self):
        """Обновляет отображение таймера"""
        hours = self.remaining_time // 3600
        minutes = (self.remaining_time % 3600) // 60
        seconds = self.remaining_time % 60
        
        if self.mode.get() == "countdown":
            self.timer_label.config(text=f"Оставшееся время: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.timer_label.config(text=f"Прошло времени: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
    def pause_timer(self):
        """Ставит таймер на паузу или возобновляет его."""
        if self.running:
            if self.paused:
                self.paused = False
                self.pause_button.config(text="Пауза")
                self.ui_manager.queue_update('status', "Таймер возобновлен")
                self.update_timer()  # Возобновляем обновление
            else:
                self.paused = True
                self.pause_button.config(text="Продолжить")
                self.ui_manager.queue_update('status', "Таймер на паузе")
                
    def reset_timer(self):
        """Сбрасывает таймер."""
        try:
            self.running = False
            self.paused = False
            self.start_time = None
            
            # Останавливаем мониторинг игр
            if self._monitor_thread:
                self.game_blocker.is_monitoring = False
                self._monitor_thread = None
            
            # Сбрасываем флаг истечения таймера
            self.game_blocker.timer_expired = False
            
            # Обновляем состояние кнопок
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED, text="Пауза")
            self.reset_button.config(state=tk.DISABLED)
            
            # Восстанавливаем начальное время
            if self.mode.get() == "countdown":
                hours = self.settings.get("hours", 0)
                minutes = self.settings.get("minutes", 0)
                self.remaining_time = hours * 3600 + minutes * 60
            else:
                self.remaining_time = 0
                
            # Показываем начальное время
            self.update_timer_display()
            self.ui_manager.queue_update('status', "Таймер сброшен")
            return True
            
        except Exception as e:
            return False, str(e)
            
    def get_elapsed_time(self):
        """Возвращает прошедшее время с момента запуска таймера"""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            return int(elapsed.total_seconds())
        return 0
        
    def is_running(self):
        """Возвращает True если таймер запущен"""
        return self.running
        
    def is_paused(self):
        """Возвращает True если таймер на паузе"""
        return self.paused
        
    def add_time(self, seconds):
        """Добавляет указанное количество секунд к таймеру"""
        if self.running and not self.paused:
            self.remaining_time += seconds
            self.update_timer_display()
