import psutil
import time
import tkinter as tk
from tkinter import simpledialog, ttk
from threading import Thread
import json
import os
import winsound
import keyboard
import win32gui
import win32con
from datetime import datetime
import winreg
import sys
import win32api
import win32com.client
from win32api import GetSystemMetrics
import pyautogui
import concurrent.futures
from datetime import datetime, timedelta
import sqlite3
import os.path
from logger import Logger
import pystray
from PIL import Image, ImageDraw
from notification_window import NotificationWindow
from achievements import Achievements  # Добавляем импорт класса Achievements
from notification_window import NotificationWindow
from logger import Logger
from settings import Settings
from process_monitor import ProcessMonitor

class GameTimerApp:
    def __init__(self, root):
        try:
            # Создаем директорию для логов если её нет
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            self.logger = Logger("GameTimerApp", "logs/game_timer.log")
            self.root = root
            self.root.title("Game Timer")
            
            # Настраиваем стиль
            self.style = ttk.Style()
            self.style.theme_use('default')
            
            # Добавляем иконку в трей
            self.setup_tray_icon()
            
            # Делаем окно адаптивным
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_rowconfigure(0, weight=1)
            
            # Основной контейнер
            main_frame = ttk.Frame(root)
            main_frame.grid(sticky="nsew", padx=10, pady=10)
            main_frame.grid_columnconfigure(0, weight=1)
            
            # Инициализация компонентов с обработкой исключений
            try:
                self.settings = Settings()
            except Exception as e:
                self.logger.error(f"Failed to initialize settings: {str(e)}")
                self.show_break_notification("Ошибка", "Failed to load settings. Using defaults.")
                self.settings = Settings(use_defaults=True)

            try:
                self.process_monitor = ProcessMonitor()
            except Exception as e:
                self.logger.error(f"Failed to initialize process monitor: {str(e)}")
                self.show_break_notification("Ошибка", "Failed to initialize process monitoring.")
                
            self.achievements = Achievements(self.settings)
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            
            # Переменные для отслеживания активности
            self.last_mouse_pos = pyautogui.position()
            self.last_activity = time.time()
            self.logger.debug(f"last_activity initialized: {self.last_activity}")
            
            # Остальные переменные
            self.mode = tk.StringVar(value=self.settings.get("mode"))
            self.hours = tk.IntVar(value=self.settings.get("hours"))
            self.minutes = tk.IntVar(value=self.settings.get("minutes"))
            self.remaining_time = 0
            self.running = False
            self.paused = False
            
            self.create_widgets(main_frame)
            self.setup_hotkeys()
            self.check_autostart()
            
            # Запускаем мониторинг активности
            self.root.after(1000, self.check_user_activity)
            
            # Обработка закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            self.logger.critical(f"Failed to initialize application: {str(e)}")
            self.show_break_notification("Ошибка", f"Failed to initialize application.")
            raise

    def toggle_autostart(self):
        """Переключение автозапуска"""
        current_state = self.settings.get("autostart", False)
        new_state = not current_state
        self.settings.set("autostart", new_state)
        self.set_autostart(new_state)
        if hasattr(self, 'autostart_var'):
            self.autostart_var.set(new_state)
        return new_state

    def show_break_notification(self, title, message):
        """Показать окно уведомления с заданным заголовком и сообщением"""
        notification = NotificationWindow(self.root, title, message)
        notification.show()
    
    def setup_tray_icon(self):
        """Настройка иконки в трее"""
        try:
            self.tray_icon = pystray.Icon("Game Timer")
            self.tray_icon.icon = self.create_tray_icon()
            menu_items = (
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Exit", self.quit_app)
            )
            self.tray_icon.menu = pystray.Menu(*menu_items)
            Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            self.logger.error(f"Failed to setup tray icon: {str(e)}")

    def create_tray_icon(self):
        """Создание иконки для трея"""
        try:
            # Создаем простую иконку
            width = 64
            height = 64
            color1 = 'blue'
            color2 = 'white'
            
            image = Image.new('RGB', (width, height), color1)
            dc = ImageDraw.Draw(image)
            dc.ellipse([10, 10, width-10, height-10], fill=color2)
            
            return image
        except Exception as e:
            self.logger.error(f"Failed to create tray icon: {str(e)}")
            return None

    def show_window(self):
        """Показать окно из трея"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception as e:
            self.logger.error(f"Failed to show window: {str(e)}")

    def on_closing(self):
        """Обработка закрытия окна"""
        try:
            if self.show_break_notification("Quit", "Minimize to tray instead of closing?"):
                self.root.withdraw()
            else:
                self.quit_app()
        except Exception as e:
            self.logger.error(f"Error during window closing: {str(e)}")
            self.quit_app()

    def quit_app(self):
        """Полное закрытие приложения"""
        try:
            if hasattr(self, 'tray_icon'):
                self.tray_icon.stop()
            self.root.quit()
        except Exception as e:
            self.logger.error(f"Error during app quit: {str(e)}")
            sys.exit(1)

    def load_theme(self):
        """Загрузка темы оформления"""
        theme = self.settings.get("theme")
        if theme == "dark":
            self.root.configure(bg='#2b2b2b')
            self.style.configure("TFrame", background='#2b2b2b')
            self.style.configure("TLabel", background='#2b2b2b', foreground='white')
            self.style.configure("TButton", background='#404040', foreground='white')
        else:
            self.root.configure(bg='#f0f0f0')
            self.style.configure("TFrame", background='#f0f0f0')
            self.style.configure("TLabel", background='#f0f0f0', foreground='black')
            self.style.configure("TButton", background='#e0e0e0', foreground='black')

    def setup_hotkeys(self):
        """Настройка горячих клавиш"""
        try:
            keyboard.add_hotkey(self.settings.get("hotkeys")["pause"], self.pause_resume_timer)
            keyboard.add_hotkey(self.settings.get("hotkeys")["reset"], self.reset_timer)
        except Exception as e:
            print(f"Ошибка настройки горячих клавиш: {e}")

    def check_autostart(self):
        """Проверка и настройка автозапуска"""
        if self.settings.get("autostart"):
            self.set_autostart(True)

    def set_autostart(self, enable=True):
        """Включение/выключение автозапуска"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                winreg.SetValueEx(key, "GameTimer", 0, winreg.REG_SZ, sys.argv[0])
            else:
                winreg.DeleteValue(key, "GameTimer")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Ошибка настройки автозапуска: {e}")

    def check_user_activity(self):
        """Проверка активности пользователя с помощью pyautogui"""
        current_pos = pyautogui.position()
        current_time = time.time()

        # Убедимся, что last_activity всегда имеет корректное значение
        if self.last_activity is None:
            self.last_activity = current_time

        # Проверяем движение мыши и активность клавиатуры
        if current_pos != self.last_mouse_pos or any(keyboard.is_pressed(key) for key in self.settings.get("hotkeys", {}).values()):
            self.last_activity = current_time
            self.last_mouse_pos = current_pos

        # Если превышен таймаут неактивности
        inactivity_timeout = self.settings.get("inactivity_timeout", 300)
        if current_time - self.last_activity > inactivity_timeout:
            if not self.paused and self.running:
                self.pause_resume_timer()
                self.status_label.config(text="Статус: Приостановлено (нет активности)")

        # Обновляем статус процессов
        self.update_process_status()

        # Планируем следующую проверку
        self.root.after(1000, self.check_user_activity)

    def update_process_status(self):
        """Обновляет информацию о запущенных процессах"""
        active_processes = [p for p in self.process_monitor.get_active_processes()
                          if p in self.settings.get("processes")]
        if active_processes:
            self.process_status.config(
                text=f"Активные процессы: {', '.join(active_processes)}")
        else:
            self.process_status.config(text="Активные процессы: нет")

    def create_widgets(self, parent):
        """Создает адаптивный интерфейс"""
        # Основной заголовок
        title_frame = ttk.Frame(parent)
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(title_frame, text="Game Timer", 
                 font=("Comic Sans MS", 24, "bold")).grid(row=0, column=0)
        
        # Фрейм для пресетов (используем grid вместо pack)
        preset_frame = ttk.Frame(parent)
        preset_frame.grid(row=1, column=0, sticky="ew", pady=5)
        preset_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(preset_frame, text="Быстрый выбор:").grid(row=0, column=0, padx=5)
        
        presets_container = ttk.Frame(preset_frame)
        presets_container.grid(row=0, column=1, sticky="w")
        
        col = 0
        for name, time in self.settings.get("presets").items():
            ttk.Button(presets_container, text=name,
                      command=lambda h=time["hours"], m=time["minutes"]: 
                      self.set_preset(h, m)).grid(row=0, column=col, padx=2)
            col += 1
            
        # Добавляем кнопку автозапуска
        self.autostart_var = tk.BooleanVar(value=self.settings.get("autostart"))
        ttk.Checkbutton(preset_frame, text="Автозапуск", 
                       variable=self.autostart_var,
                       command=self.toggle_autostart).grid(row=0, column=2, padx=10)
        
        # Статус процессов
        self.process_status = ttk.Label(parent, text="Активные процессы: нет")
        self.process_status.grid(row=2, column=0, sticky="ew", pady=5)
        
        # Выбор режима
        mode_frame = ttk.LabelFrame(parent, text="Режим работы", padding=10)
        mode_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        ttk.Radiobutton(mode_frame, text="Таймер", variable=self.mode, value="timer").grid(row=0, column=0, padx=20)
        ttk.Radiobutton(mode_frame, text="Отслеживание игр", variable=self.mode, value="track").grid(row=0, column=1, padx=20)
        
        # Ввод времени
        time_frame = ttk.LabelFrame(parent, text="Установка времени", padding=10)
        time_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=5)
        
        ttk.Entry(time_frame, textvariable=self.hours, width=5).grid(row=0, column=0, padx=2)
        ttk.Label(time_frame, text="часов").grid(row=0, column=1, padx=(2, 10))
        
        ttk.Entry(time_frame, textvariable=self.minutes, width=5).grid(row=0, column=2, padx=2)
        ttk.Label(time_frame, text="минут").grid(row=0, column=3, padx=2)

        # Прогресс-бар
        self.progress = ttk.Progressbar(parent, length=400, mode='determinate')
        self.progress.grid(row=5, column=0, padx=20, pady=20, sticky="ew")

        # Кнопки управления
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        self.start_button = ttk.Button(btn_frame, text="Начать", command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(btn_frame, text="Пауза", command=self.pause_resume_timer, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.reset_button = ttk.Button(btn_frame, text="Сброс", command=self.reset_timer, state=tk.DISABLED)
        self.reset_button.grid(row=0, column=2, padx=5)

        # Кнопка настройки процессов
        ttk.Button(btn_frame, text="Настройка процессов", command=self.configure_processes).grid(row=0, column=3, padx=5)

        # Отображение времени
        self.timer_label = tk.Label(parent, text="Оставшееся время: --:--:--",
                                  font=("Arial", 16, "bold"))
        self.timer_label.grid(row=7, column=0, padx=20, pady=10, sticky="ew")

        # Статус
        self.status_label = tk.Label(parent, text="Статус: Ожидание",
                                   font=("Arial", 12))
        self.status_label.grid(row=8, column=0, padx=20, pady=5, sticky="ew")

    def set_preset(self, hours, minutes):
        """Устанавливает предустановленное время."""
        self.hours.set(hours)
        self.minutes.set(minutes)

    def configure_processes(self):
        """Настройка списка отслеживаемых процессов."""
        processes = "\n".join(self.settings.get("processes"))
        result = simpledialog.askstring("Настройка процессов",
                                      "Введите имена процессов (по одному на строку):",
                                      initialvalue=processes)
        if result:
            self.settings.set("processes", [p.strip() for p in result.split("\n") if p.strip()])

    def start_timer(self):
        """Запускает выбранный режим."""
        total_minutes = self.hours.get() * 60 + self.minutes.get()
        if total_minutes <= 0:
            self.show_break_notification("Предупреждение", "Пожалуйста, введите время больше 0")
            return

        self.remaining_time = total_minutes * 60
        self.initial_time = self.remaining_time
        self.running = True
        self.paused = False
        self.progress['maximum'] = self.initial_time
        self.progress['value'] = self.initial_time
        
        # Сохраняем настройки
        self.settings.set("mode", self.mode.get())
        self.settings.set("hours", self.hours.get())
        self.settings.set("minutes", self.minutes.get())

        # Обновляем состояние кнопок
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.NORMAL)

        if self.mode.get() == "timer":
            self.update_timer()
        else:
            Thread(target=self.track_games).start()

    def update_timer(self):
        """Обновляет обратный отсчет времени."""
        if self.remaining_time > 0 and self.running and not self.paused:
            hours, remainder = divmod(self.remaining_time, 3600)
            mins, secs = divmod(remainder, 60)
            self.timer_label.config(text=f"Оставшееся время: {int(hours):02}:{int(mins):02}:{int(secs):02}")
            self.progress['value'] = self.remaining_time
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        elif self.remaining_time <= 0 and self.running:
            self.show_break_notification("Время вышло", "Пора сделать перерыв!")

    def track_games(self):
        """Следит за играми и отслеживает время."""
        start_time = None
        last_update = 0
        update_interval = self.settings.get("ui_update_interval") / 1000  # в секундах
        
        while self.running and not self.paused:
            current_time = time.time()
            
            # Проверяем процессы через executor
            future = self.executor.submit(
                self.process_monitor.is_process_running,
                self.settings.get("processes")
            )
            game_running = future.result()
            
            if game_running:
                if start_time is None:
                    start_time = current_time
                    
                # Обновляем UI только с заданным интервалом
                if current_time - last_update >= update_interval:
                    elapsed = current_time - start_time
                    self.remaining_time -= elapsed
                    self.progress['value'] = self.remaining_time
                    
                    # Обновляем статистику использования
                    active_processes = [p for p in self.process_monitor.get_active_processes()
                                     if p in self.settings.get("processes")]
                    for process in active_processes:
                        self.process_monitor.log_usage(process, elapsed)
                    
                    # Обновляем UI
                    self.root.after(0, self.update_ui_status, "Игра запущена")
                    self.root.after(0, self.update_timer_display)
                    
                    last_update = current_time
                    start_time = current_time
                    
                if self.remaining_time <= 0:
                    self.root.after(0, self.show_break_notification)
                    break
            else:
                start_time = None
                self.root.after(0, self.update_ui_status, "Игра не запущена")
            
            # Используем короткие интервалы сна
            time.sleep(0.1)

    def update_ui_status(self, status):
        """Обновляет статус в UI"""
        self.status_label.config(text=f"Статус: {status}")

    def update_timer_display(self):
        """Обновляет отображение таймера"""
        hours, remainder = divmod(int(self.remaining_time), 3600)
        mins, secs = divmod(remainder, 60)
        self.timer_label.config(
            text=f"Оставшееся время: {hours:02}:{mins:02}:{secs:02}")

    def pause_resume_timer(self):
        """Приостанавливает или возобновляет таймер."""
        self.paused = not self.paused
        self.pause_button.config(text="Продолжить" if self.paused else "Пауза")
        if not self.paused and self.mode.get() == "timer":
            self.update_timer()

    def reset_timer(self):
        """Сбрасывает таймер."""
        self.running = False
        self.paused = False
        self.remaining_time = 0
        self.progress['value'] = 0
        self.timer_label.config(text="Оставшееся время: --:--:--")
        self.status_label.config(text="Статус: Ожидание")
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Пауза")
        self.reset_button.config(state=tk.DISABLED)

def show_break_notification(self, title, message):
    try:
        if not hasattr(self, 'notification_window'):
            self.notification_window = NotificationWindow(
                parent=self.root,
                title=title,
                message=message
            )
        self.notification_window.show()
    except Exception as e:
        self.logger.error(f"Ошибка показа уведомления: {str(e)}")
            

def simulate_esc_key():
    """Симулирует нажатие клавиши ESC"""
    keyboard.press_and_release('esc')

def bring_to_front(window):
    """Выводит окно на передний план"""
    # Устанавливаем окно на передний план
    window.lift()
    window.attributes('-topmost', True)
    window.attributes('-topmost', False)
    
    # Восстанавливаем окно если оно свернуто
    if win32gui.IsIconic(window.winfo_id()):
        win32gui.ShowWindow(window.winfo_id(), win32con.SW_RESTORE)
    
    # Активируем окно
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    window.focus_force()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = GameTimerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        app.show_break_notification("Ошибка", f"Произошла ошибка: {str(e)}")
