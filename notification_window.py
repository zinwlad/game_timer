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
                background=self.gradient_colors[1],  # Используем второй цвет градиента
                thickness=10
            )
            
            self.window = tk.Tk()
            self.window.withdraw()  # Скрываем основное окно
            
            # Создаем всплывающее окно
            self.popup = tk.Toplevel()
            self.popup.withdraw()  # Сначала скрываем
            
            # Настройка окна
            self.popup.title("🎮 Перерыв!")
            self.popup.geometry("600x500")  # Увеличиваем размер окна
            
            # Создаем и устанавливаем градиентный фон
            self.background_image = self._create_gradient_background()
            background_label = tk.Label(self.popup, image=self.background_image)
            background_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Убираем рамку окна и делаем его поверх других окон
            self.popup.overrideredirect(True)
            self.popup.attributes('-topmost', True)
            
            # Создаем основной контейнер
            self.content_frame = tk.Frame(self.popup)
            self.content_frame.pack(expand=True, fill='both', padx=30, pady=30)
            self.content_frame.configure(bg=self.gradient_colors[0])  # Используем первый цвет градиента
            
            # Добавляем анимированную иконку
            self._create_animated_icon()
            
            # Добавляем заголовок с эффектом свечения
            self._create_glowing_title()
            
            # Добавляем мотивационное сообщение
            self._create_message()
            
            # Добавляем прогресс-бар здоровья
            self._create_health_bar()
            
            # Добавляем красивую кнопку закрытия
            self._create_close_button()
            
            # Позиционируем окно
            self._position_window()
            
            # Инициализируем счетчики для анимаций
            self.blink_count = 0
            self.glow_intensity = 0
            self.glow_increasing = True
            
            # Настраиваем автозакрытие
            self.popup.after(30000, self.close)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification window: {str(e)}")
            raise

    def _generate_gradient_colors(self):
        """Генерация случайных цветов для градиента"""
        try:
            colors = [
                ('#FF6B6B', '#4ECDC4'),  # Красный к бирюзовому
                ('#A8E6CF', '#FFD3B6'),  # Мятный к персиковому
                ('#FFB6B9', '#8AC6D1'),  # Розовый к голубому
                ('#B8F2E6', '#FFA69E')   # Бирюзовый к лососевому
            ]
            return random.choice(colors)
        except Exception as e:
            self.logger.error(f"Failed to generate gradient colors: {str(e)}")
            return ('#4A90E2', '#50E3C2')  # Возвращаем безопасные цвета по умолчанию

    def _create_gradient_background(self):
        """Создание градиентного фона"""
        try:
            width = 600
            height = 500
            image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(image)
            
            color1 = self.gradient_colors[0]
            color2 = self.gradient_colors[1]
            
            for y in range(height):
                r = int((1 - y/height) * int(color1[1:3], 16) + (y/height) * int(color2[1:3], 16))
                g = int((1 - y/height) * int(color1[3:5], 16) + (y/height) * int(color2[3:5], 16))
                b = int((1 - y/height) * int(color1[5:7], 16) + (y/height) * int(color2[5:7], 16))
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            return ImageTk.PhotoImage(image)
        except Exception as e:
            self.logger.error(f"Failed to create gradient background: {str(e)}")
            # Создаем одноцветный фон в случае ошибки
            image = Image.new('RGB', (600, 500), '#4A90E2')
            return ImageTk.PhotoImage(image)

    def _create_animated_icon(self):
        """Создание анимированной иконки"""
        self.icons = ["⏰", "⌛", "🎮", "🎯"]
        self.current_icon = 0
        self.icon_label = tk.Label(
            self.content_frame,
            text=self.icons[0],
            font=("Segoe UI Emoji", 82),
            bg=self.gradient_colors[0],
            fg='white'
        )
        self.icon_label.pack(pady=(0, 20))

    def _create_glowing_title(self):
        """Создание заголовка с эффектом свечения"""
        self.title_label = tk.Label(
            self.content_frame,
            text="ПОРА ОТДОХНУТЬ!",
            font=("Arial Black", 36, "bold"),
            bg=self.gradient_colors[0],
            fg='white'
        )
        self.title_label.pack(pady=(0, 20))

    def _create_message(self):
        """Создание мотивационного сообщения"""
        messages = [
            "Сделайте перерыв на 20 минут\nВаши глаза и спина скажут спасибо!",
            "Время размяться и отдохнуть!\nЗдоровье важнее игр 🌟",
            "Небольшой перерыв - большая польза!\nВстаньте и разомнитесь 💪",
            "Пора передохнуть и вернуться с новыми силами!\nВаше здоровье - главный приоритет 🌿"
        ]
        self.message = tk.Label(
            self.content_frame,
            text=random.choice(messages),
            font=("Segoe UI", 24),
            wraplength=500,
            bg=self.gradient_colors[0],
            fg='white'
        )
        self.message.pack(pady=20)

    def _create_health_bar(self):
        """Создание прогресс-бара здоровья"""
        self.health_frame = tk.Frame(self.content_frame, bg=self.gradient_colors[0])
        self.health_frame.pack(pady=20, fill='x')
        
        self.health_bar = ttk.Progressbar(
            self.health_frame,
            length=400,
            mode='determinate',
            style='Healthy.Horizontal.TProgressbar'
        )
        self.health_bar.pack()
        self.health_bar['value'] = 100

    def _create_close_button(self):
        """Создание красивой кнопки закрытия"""
        style = {
            'font': ('Arial', 16, 'bold'),
            'bg': 'white',
            'fg': self.gradient_colors[0],
            'relief': tk.FLAT,
            'padx': 30,
            'pady': 15,
            'cursor': 'hand2'  # Курсор в виде руки при наведении
        }
        
        self.close_btn = tk.Button(
            self.content_frame,
            text="Понятно, сделаю перерыв!",
            command=self.close,
            **style
        )
        self.close_btn.pack(pady=20)
        
        # Добавляем эффекты при наведении
        self.close_btn.bind('<Enter>', self._on_button_hover)
        self.close_btn.bind('<Leave>', self._on_button_leave)

    def _position_window(self):
        """Позиционирование окна в правом нижнем углу"""
        screen_width = GetSystemMetrics(0)
        screen_height = GetSystemMetrics(1)
        window_width = 600
        window_height = 500
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60
        self.popup.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def _on_button_hover(self, event):
        """Эффект при наведении на кнопку"""
        self.close_btn.configure(
            bg=self.gradient_colors[0],
            fg='white'
        )

    def _on_button_leave(self, event):
        """Эффект при уходе курсора с кнопки"""
        self.close_btn.configure(
            bg='white',
            fg=self.gradient_colors[0]
        )

    def _animate_icon(self):
        """Анимация иконки"""
        if hasattr(self, 'icon_label'):
            self.current_icon = (self.current_icon + 1) % len(self.icons)
            self.icon_label.configure(text=self.icons[self.current_icon])
            if self.popup.winfo_exists():
                self.popup.after(1000, self._animate_icon)

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
            size = 36 + int(self.glow_intensity * 4)
            self.title_label.configure(font=("Arial Black", size, "bold"))
            
            if self.popup.winfo_exists():
                self.popup.after(50, self._animate_glow)

    def show(self):
        """Показ уведомления с анимацией"""
        try:
            self.popup.deiconify()
            
            # Анимация появления
            for i in range(11):
                self.popup.attributes('-alpha', i/10)
                self.popup.update()
                time.sleep(0.02)
            
            # Запускаем все анимации
            self._animate_icon()
            self._animate_glow()
            self.blink_window()
            
            # Воспроизводим звук
            winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
            
        except Exception as e:
            self.logger.error(f"Error showing notification: {str(e)}")

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
        """Закрытие с плавной анимацией"""
        try:
            # Анимация исчезновения
            for i in range(10, -1, -1):
                self.popup.attributes('-alpha', i/10)
                self.popup.update()
                time.sleep(0.02)
            self.popup.withdraw()
            
        except Exception as e:
            self.logger.error(f"Error closing notification: {str(e)}")
            self.popup.withdraw()  # Принудительно скрываем в случае ошибки
