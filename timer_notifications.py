import tkinter as tk
from datetime import datetime

class TimerNotifications:
    def __init__(self, parent_window):
        """
        Инициализация менеджера уведомлений
        
        Args:
            parent_window: Родительское окно tkinter
        """
        self.parent = parent_window
        
        # Создаем фрейм для уведомлений внизу окна
        self.notification_frame = tk.Frame(self.parent)
        self.notification_frame.grid(row=9, column=0, sticky="ew", pady=5)  # Используем row=9, так как row=8 занят status_label
        
        # Настраиваем колонки для центрирования
        self.notification_frame.grid_columnconfigure(0, weight=1)
        
        # Метка для отображения уведомлений
        self.notification_label = tk.Label(
            self.notification_frame,
            text="",
            font=("Arial", 10),
            fg="#666666",
            justify=tk.LEFT,
            padx=10
        )
        self.notification_label.grid(row=0, column=0, sticky="ew")  # Используем grid вместо pack
        
        # Для временных уведомлений
        self.temp_notification = None
        self.last_extension_time = None
        
        # Показываем горячие клавиши при запуске
        self.show_hotkeys_hint()
    
    def show_hotkeys_hint(self):
        """Показывает подсказки о горячих клавишах"""
        hint_text = (
            "Горячие клавиши:\n"
            "⌨️ Ctrl+Alt+5 - добавить 5 минут\n"
            "⌨️ Ctrl+Alt+0 - добавить 10 минут\n"
            "⌨️ Ctrl+Space - пауза/продолжить"
        )
        self.notification_label.config(text=hint_text)
    
    def show_extension_success(self, minutes: int, remaining_extensions: int):
        """
        Показывает уведомление об успешном продлении
        
        Args:
            minutes: Количество добавленных минут
            remaining_extensions: Оставшееся количество продлений
        """
        # Проверяем, не слишком ли часто используются продления
        current_time = datetime.now()
        if self.last_extension_time:
            time_diff = (current_time - self.last_extension_time).total_seconds()
            if time_diff < 60:  # Меньше минуты между продлениями
                self._show_temporary_notification(
                    "⚠️ Подождите немного перед следующим продлением",
                    duration=2000
                )
                return
        
        self.last_extension_time = current_time
        success_text = (
            f"✅ Добавлено {minutes} минут!\n"
            f"Осталось продлений: {remaining_extensions}"
        )
        self._show_temporary_notification(success_text)
    
    def show_extension_limit(self):
        """Показывает уведомление о достижении лимита продлений"""
        limit_text = "⚠️ Достигнут лимит продлений на эту сессию!"
        self._show_temporary_notification(limit_text, duration=4000)
    
    def show_pause_status(self, is_paused: bool):
        """
        Показывает статус паузы
        
        Args:
            is_paused: True если таймер на паузе, False если работает
        """
        status_text = "⏸️ Таймер на паузе" if is_paused else "▶️ Таймер запущен"
        self._show_temporary_notification(status_text)
    
    def show_timer_start(self, hours: int, minutes: int):
        """Показывает уведомление о запуске таймера"""
        if hours > 0 and minutes > 0:
            message = f"⏰ Таймер запущен на {hours} ч. {minutes} мин."
        elif hours > 0:
            message = f"⏰ Таймер запущен на {hours} ч."
        else:
            message = f"⏰ Таймер запущен на {minutes} мин."
            
        self._show_temporary_notification(message, duration=3000)
    
    def _show_temporary_notification(self, text: str, duration: int = 3000):
        """
        Показывает временное уведомление и возвращает подсказки
        
        Args:
            text: Текст уведомления
            duration: Продолжительность показа в миллисекундах
        """
        # Сохраняем текущий текст подсказок
        original_text = self.notification_label.cget("text")
        
        # Показываем новое уведомление
        self.notification_label.config(text=text)
        
        # Отменяем предыдущий таймер если есть
        if self.temp_notification:
            self.parent.after_cancel(self.temp_notification)
        
        # Устанавливаем таймер на возврат подсказок
        self.temp_notification = self.parent.after(
            duration,
            lambda: self.notification_label.config(text=original_text)
        )
    
    def update_theme(self, is_dark: bool = False):
        """
        Обновляет цвета в соответствии с темой
        
        Args:
            is_dark: True для темной темы, False для светлой
        """
        bg_color = "#2D2D2D" if is_dark else "#FFFFFF"
        fg_color = "#E0E0E0" if is_dark else "#666666"
        
        self.notification_frame.config(bg=bg_color)
        self.notification_label.config(
            bg=bg_color,
            fg=fg_color
        )
