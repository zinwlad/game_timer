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
    def __init__(self):
        try:
            # Создаем директорию для логов если её нет
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            self.logger = Logger("NotificationWindow", "logs/notifications.log")
            
            # Инициализируем цвета градиента сразу
            self.gradient_colors = self._generate_gradient_colors()
            
            # Настраиваем стиль для прогресс-бара
            self.style = ttk.Style()
            self.style.configure(
                "Healthy.Horizontal.TProgressbar",
                troughcolor='white',
                background=self.gradient_colors[1],
                thickness=10
            )
            
            # Создаем всплывающее окно
            self.popup = tk.Toplevel()
            self.popup.withdraw()
            
            # Настройка окна
            self.popup.title("🎮 Перерыв!")
            self.popup.overrideredirect(True)  # Убираем заголовок окна
            self.popup.configure(bg=self.gradient_colors[0])  # Устанавливаем цвет фона
            
            # Создаем основной контейнер
            self.content_frame = tk.Frame(self.popup, bg=self.gradient_colors[0])
            self.content_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            # Иконки для анимации
            self.icons = ["🎮", "⭐", "🌟", "✨"]
            self.current_icon = 0
            
            # Создаем все элементы интерфейса
            self._create_animated_icon()
            self._create_title()
            self._create_message()
            self._create_health_bar()
            self._create_close_button()
            
            # Инициализируем счетчики для анимаций
            self.blink_count = 0
            self.glow_intensity = 0
            self.glow_increasing = True
            
            # Добавляем обработку закрытия окна
            self.popup.protocol("WM_DELETE_WINDOW", self.close)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification window: {str(e)}")
            raise

    def _generate_gradient_colors(self):
        """Генерация цветов для градиента"""
        try:
            colors = [
                ('#FF4500', '#FF8C00'),  # Красно-оранжевый к темно-оранжевому
                ('#FF8000', '#FFA500'),  # Оранжевый к светло-оранжевому
                ('#FF0000', '#FF6347'),  # Красный к томатному
                ('#F09327', '#FFE4B5')   # Оранжевый к персиковому
            ]
            gradient = random.choice(colors)
            return gradient
        except Exception as e:
            self.logger.error(f"Failed to generate gradient colors: {str(e)}")
            return ('#FF4500', '#FF8C00')  # Безопасные цвета по умолчанию

    def _create_gradient_background(self):
        """Создание градиентного фона"""
        width = 600
        height = 500
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Конвертируем hex в RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        color1 = hex_to_rgb(self.gradient_colors[0])
        color2 = hex_to_rgb(self.gradient_colors[1])
        
        for y in range(height):
            r = int(color1[0] + (color2[0] - color1[0]) * y / height)
            g = int(color1[1] + (color2[1] - color1[1]) * y / height)
            b = int(color1[2] + (color2[2] - color1[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return ImageTk.PhotoImage(image)

    def _create_animated_icon(self):
        """Создание анимированной иконки"""
        self.icon_label = tk.Label(
            self.content_frame,
            text=self.icons[0],
            font=("Segoe UI Emoji", 64),
            bg=self.gradient_colors[0],
            fg=self.gradient_colors[1]
        )
        self.icon_label.pack(pady=(0, 10))

    def _create_title(self):
        """Создание заголовка"""
        self.title_label = tk.Label(
            self.content_frame,
            text="ЕГОР, ПОРА ОТДОХНУТЬ!",
            font=("Comic Sans MS", 28, "bold"),
            bg=self.gradient_colors[0],
            fg=self.gradient_colors[1]
        )
        self.title_label.pack(pady=(0, 10))

    def _create_message(self):
        """Создание сообщения"""
        messages = [
            "Давай сделаем перерыв!\nТвои глазки устали от экрана 👀",
            "Время размяться!\nПобегай и поиграй немного 🦸‍♂️",
            "Пора отдохнуть!\nМожет, поиграем в другую игру? 🎯",
            "Перерыв - это здорово!\nПора подвигаться и размяться 🌟"
        ]
        self.message = tk.Label(
            self.content_frame,
            text=random.choice(messages),
            font=("Comic Sans MS", 20),
            wraplength=400,
            bg=self.gradient_colors[0],
            fg=self.gradient_colors[1],
            justify=tk.CENTER
        )
        self.message.pack(pady=10)

    def _create_health_bar(self):
        """Создание прогресс-бара здоровья"""
        self.health_frame = tk.Frame(self.content_frame, bg=self.gradient_colors[0])
        self.health_frame.pack(pady=10, fill='x')
        
        self.health_bar = ttk.Progressbar(
            self.health_frame,
            length=300,
            mode='determinate',
            style='Healthy.Horizontal.TProgressbar'
        )
        self.health_bar.pack()
        self.health_bar['value'] = 100

    def _create_close_button(self):
        """Создание кнопки закрытия"""
        self.close_button = tk.Button(
            self.content_frame,
            text="Понял, сделаю перерыв! 👍",
            font=("Comic Sans MS", 12),
            command=self.close,
            bg=self.gradient_colors[1],
            fg=self.gradient_colors[0],
            relief=tk.FLAT,
            activebackground=self.gradient_colors[0],
            activeforeground=self.gradient_colors[1]
        )
        self.close_button.pack(pady=10)

    def animate_icon(self):
        """Анимация иконки"""
        self.current_icon = (self.current_icon + 1) % len(self.icons)
        self.icon_label.config(text=self.icons[self.current_icon])
        self.popup.after(1000, self.animate_icon)  # Каждую секунду

    def _animate_glow(self):
        """Анимация свечения заголовка"""
        if hasattr(self, 'title_label'):
            if self.glow_increasing:
                self.glow_intensity += 0.1
                if self.glow_intensity >= 1:
                    self.glow_increasing = False
            else:
                self.glow_intensity -= 0.1
                if self.glow_intensity <= 0:
                    self.glow_increasing = True
            
            # Создаем эффект свечения, изменяя размер шрифта
            size = 28 + int(self.glow_intensity * 4)
            self.title_label.configure(font=("Comic Sans MS", size, "bold"))
            
            if self.popup.winfo_exists():
                self.popup.after(50, self._animate_glow)

    def show(self, duration=15):
        """Показать уведомление"""
        try:
            # Получаем размеры экрана
            screen_width = GetSystemMetrics(0)
            screen_height = GetSystemMetrics(1)
            
            # Размеры окна
            window_width = 500
            window_height = 400
            
            # Позиция в правом нижнем углу с отступом 20 пикселей
            x = screen_width - window_width - 20
            y = screen_height - window_height - 40  # 40 для учета панели задач
            
            # Устанавливаем позицию и убираем рамку
            self.popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
            self.popup.attributes('-topmost', True)
            self.popup.overrideredirect(True)
            
            # Обновляем сообщение с именем
            messages = [
                f"ЕГОР, давай сделаем перерыв!\nТвои глазки устали от экрана 👀",
                f"ЕГОР, время размяться!\nПобегай и поиграй немного 🦸‍♂️",
                f"ЕГОР, пора отдохнуть!\nМожет, поиграем в другую игру? 🎯",
                f"ЕГОР, перерыв - это здорово!\nПора подвигаться и размяться 🌟"
            ]
            self.message.config(text=random.choice(messages))
            
            # Показываем окно
            self.popup.deiconify()
            
            # Запускаем анимации
            self.animate_icon()
            self._animate_glow()
            self.blink_window()
            
            # Устанавливаем таймер на автозакрытие
            self.popup.after(duration * 1000, self.close)
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {str(e)}")
            raise

    def blink_window(self):
        """Улучшенное мигание окном"""
        try:
            if self.blink_count < 6:
                current_alpha = self.popup.attributes('-alpha')
                new_alpha = 0.4 if current_alpha == 1.0 else 1.0
                self.popup.attributes('-alpha', new_alpha)
                self.blink_count += 1
                
                # Уменьшаем частоту мигания со временем
                delay = 500 + (self.blink_count * 100)
                self.popup.after(delay, self.blink_window)
                
        except Exception as e:
            self.logger.error(f"Error during window blinking: {str(e)}")

    def close(self):
        """Закрытие окна с анимацией"""
        try:
            # Отменяем все отложенные задачи
            self.popup.after_cancel("all")
            
            # Плавно уменьшаем прозрачность
            for i in range(10, -1, -1):
                self.popup.attributes('-alpha', i/10)
                self.popup.update()
                time.sleep(0.02)
            
            # Скрываем окно
            self.popup.withdraw()
            self.popup.update()
            
        except Exception as e:
            self.logger.error(f"Error closing notification: {str(e)}")
            try:
                self.popup.withdraw()
            except:
                pass

    def hide(self):
        """Закрытие окна"""
        self.close()
