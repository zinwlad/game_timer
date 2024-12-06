import tkinter as tk
from tkinter import ttk
from win32api import GetSystemMetrics
import winsound
import time
from PIL import Image, ImageTk, ImageDraw
import random
from logger import Logger
import os

class NotificationWindow:
    def __init__(self, parent, title="Уведомление", message=""):
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            self.logger = Logger("NotificationWindow", "logs/notifications.log")
            
            # Современные цвета
            self.bg_color = '#4A90E2'  # Яркий синий
            self.text_color = 'white'  # Белый текст
            
            # Сохраняем заголовок и сообщение
            self.title = title
            self.message = message
            
            # Создаем всплывающее окно
            self.popup = tk.Toplevel(parent)
            self.popup.withdraw()
            
            # Настройка окна
            self.popup.title("Время отдыха!")
            self.popup.overrideredirect(True)
            self.popup.configure(bg=self.bg_color)
            
            # Создаем основной контейнер
            self.content_frame = tk.Frame(
                self.popup,
                bg=self.bg_color,
                bd=0
            )
            self.content_frame.pack(expand=True, fill='both', padx=30, pady=30)
            
            # Создаем элементы интерфейса
            self._create_title()
            self._create_message()
            self._create_close_button()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification window: {str(e)}")
            raise

    def _create_title(self):
        """Создание заголовка"""
        self.title_label = tk.Label(
            self.content_frame,
            text="ЕГОР!",
            font=("Montserrat", 32, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.title_label.grid(row=0, column=0, pady=(0, 20), sticky="nsew")
        
        # Настраиваем веса для центрирования
        self.content_frame.grid_columnconfigure(0, weight=1)

    def _create_message(self):
        """Создание сообщения"""
        messages = [
            "Давай сделаем перерыв!\nТвои глазки устали 👀",
            "Время отдохнуть!\nПобегай немного 🏃",
            "Пора размяться!\nПоиграем в игрушки или порисуй? 🎯",
            "Перерыв!\nПора подвигаться 🌟"
        ]
        
        self.message_label = tk.Label(
            self.content_frame,
            text=random.choice(messages),
            font=("Montserrat", 18),
            wraplength=400,
            bg=self.bg_color,
            fg=self.text_color,
            justify=tk.CENTER
        )
        self.message_label.grid(row=1, column=0, pady=(0, 30), sticky="nsew")
        
        # Настраиваем веса для центрирования
        self.content_frame.grid_columnconfigure(0, weight=1)

    def _create_close_button(self):
        """Создание кнопки закрытия"""
        self.close_button = tk.Button(
            self.content_frame,
            text="Хорошо!",
            font=("Montserrat", 14, "bold"),
            command=self.close,
            bg='white',
            fg=self.bg_color,
            relief="flat",
            width=15,
            cursor="hand2"
        )
        self.close_button.grid(row=2, column=0, pady=10, sticky="nsew")
        
        # Настраиваем веса для центрирования
        self.content_frame.grid_columnconfigure(0, weight=1)

    def show(self, duration=15):
        """Показать уведомление"""
        try:
            # Получаем размеры экрана
            screen_width = GetSystemMetrics(0)
            screen_height = GetSystemMetrics(1)
            
            # Размеры окна
            window_width = 450
            window_height = 350
            
            # Позиция в правом нижнем углу с отступом
            x = screen_width - window_width - 20
            y = screen_height - window_height - 40
            
            # Устанавливаем позицию
            self.popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
            self.popup.attributes('-topmost', True)
            
            # Показываем окно
            self.popup.deiconify()
            
            # Воспроизводим звук
            winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
            
            # Автозакрытие через duration секунд
            self.auto_close_id = self.popup.after(duration * 1000, self.close)
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {str(e)}")
            raise

    def close(self):
        """Закрытие окна"""
        try:
            # Отменяем автозакрытие если оно было запланировано
            if hasattr(self, 'auto_close_id'):
                self.popup.after_cancel(self.auto_close_id)
                del self.auto_close_id
            self.popup.withdraw()
        except Exception as e:
            self.logger.error(f"Error closing notification: {str(e)}")

    def hide(self):
        """Скрыть окно"""
        self.close()
