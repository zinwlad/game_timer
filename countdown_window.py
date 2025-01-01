import tkinter as tk
from tkinter import ttk
import time
from logger import Logger

class CountdownWindow:
    def __init__(self, parent, seconds=15):
        """
        Создает окно обратного отсчета перед блокировкой
        :param parent: родительское окно
        :param seconds: количество секунд для отсчета
        """
        self.logger = Logger("CountdownWindow")
        self.window = tk.Toplevel(parent)
        self.window.title("Предупреждение")
        self.seconds = seconds
        self.remaining = seconds
        
        # Настройка окна
        self.window.overrideredirect(True)  # Убираем заголовок окна
        self.window.attributes('-topmost', True)  # Поверх всех окон
        
        # Получаем размеры экрана
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Размеры окна
        window_width = 300
        window_height = 100
        
        # Позиционируем окно в правом верхнем углу
        x = screen_width - window_width - 20
        y = 20
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Настройка стиля
        style = ttk.Style()
        style.configure('Warning.TFrame', background='#ff9999')
        style.configure('Warning.TLabel', background='#ff9999', foreground='black')
        
        # Создаем и размещаем виджеты
        main_frame = ttk.Frame(self.window, style='Warning.TFrame', padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # Сообщение
        warning_label = ttk.Label(
            main_frame,
            text="Внимание! Блокировка через:",
            font=("Arial", 12, "bold"),
            style='Warning.TLabel',
            wraplength=280
        )
        warning_label.grid(row=0, column=0, pady=(0, 10))
        
        # Таймер
        self.time_label = ttk.Label(
            main_frame,
            text=str(self.seconds),
            font=("Arial", 16, "bold"),
            style='Warning.TLabel'
        )
        self.time_label.grid(row=1, column=0)
        
        # Настройка фона
        self.window.configure(bg='#ff9999')
        
        # Запускаем обновление таймера
        self.update_timer()
        
    def update_timer(self):
        """Обновляет отображение таймера"""
        try:
            if self.remaining > 0:
                self.time_label.configure(text=str(self.remaining))
                self.remaining -= 1
                self.window.after(1000, self.update_timer)
        except Exception as e:
            self.logger.error(f"Error updating timer: {str(e)}")
            
    def show(self):
        """Показывает окно"""
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            # Обновляем окно
            self.window.update()
        except Exception as e:
            self.logger.error(f"Error showing countdown window: {str(e)}")
