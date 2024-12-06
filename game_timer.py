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
from PIL import Image, ImageDraw
from notification_window import NotificationWindow
from achievements import Achievements
from notification_window import NotificationWindow
from logger import Logger
from settings import Settings
from process_monitor import ProcessMonitor
from hotkey_manager import HotkeyManager
from ui_manager import UIManager
from tray_manager import TrayManager
from theme_manager import ThemeManager
from autostart_manager import AutostartManager
from activity_monitor import ActivityMonitor
from achievement_manager import AchievementManager

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
            
            # Инициализируем менеджеры
            self.settings = self._init_settings()
            self.theme_manager = ThemeManager(root, self.style)
            self.hotkey_manager = HotkeyManager()
            self.ui_manager = UIManager(root)
            self.tray_manager = TrayManager(
                show_window_callback=self.show_window,
                quit_callback=self.quit_app
            )
            self.autostart_manager = AutostartManager()
            self.activity_monitor = ActivityMonitor(self.settings)
            self.process_monitor = self._init_process_monitor()
            self.achievement_manager = AchievementManager(self.settings, root)
            
            # Делаем окно адаптивным
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_rowconfigure(0, weight=1)
            
            # Основной контейнер
            main_frame = ttk.Frame(root)
            main_frame.grid(sticky="nsew", padx=10, pady=10)
            main_frame.grid_columnconfigure(0, weight=1)
            
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            
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
            
            # Применяем тему
            self.theme_manager.apply_theme(self.settings.get("theme", "light"))
            
            # Запускаем мониторинг активности
            self.root.after(1000, self.check_user_activity)
            
            # Обработка закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            self.logger.critical(f"Failed to initialize application: {str(e)}")
            self.show_break_notification("Ошибка", f"Failed to initialize application.")
            raise

    def _init_settings(self):
        """Инициализация настроек"""
        try:
            return Settings()
        except Exception as e:
            self.logger.error(f"Failed to initialize settings: {str(e)}")
            self.show_break_notification("Ошибка", "Failed to load settings. Using defaults.")
            return Settings(use_defaults=True)

    def _init_process_monitor(self):
        """Инициализация монитора процессов"""
        try:
            return ProcessMonitor()
        except Exception as e:
            self.logger.error(f"Failed to initialize process monitor: {str(e)}")
            self.show_break_notification("Ошибка", "Failed to initialize process monitoring.")
            return None

    def toggle_autostart(self):
        """Переключение автозапуска"""
        current_state = self.settings.get("autostart", False)
        new_state = not current_state
        if self.autostart_manager.set_autostart(new_state):
            self.settings.set("autostart", new_state)
            if hasattr(self, 'autostart_var'):
                self.autostart_var.set(new_state)
        return new_state

    def check_autostart(self):
        """Проверка и настройка автозапуска"""
        if self.settings.get("autostart"):
            self.autostart_manager.set_autostart(True)

    def check_user_activity(self):
        """Проверка активности пользователя"""
        is_active, inactivity_duration = self.activity_monitor.check_activity()
        
        if not is_active and not self.paused and self.running:
            self.pause_resume_timer()
            self.ui_manager.queue_update('status', "Статус: Приостановлено (нет активности)")

        # Обновляем статус процессов
        self.update_process_status()

        # Планируем следующую проверку
        self.root.after(1000, self.check_user_activity)

    def show_break_notification(self, title, message):
        """Показать окно уведомления с заданным заголовком и сообщением"""
        notification = NotificationWindow(self.root, title, message)
        notification.show()
    
    def show_window(self):
        """Показывает главное окно"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

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
            # Останавливаем менеджеры
            if hasattr(self, 'hotkey_manager'):
                self.hotkey_manager.clear_all_hotkeys()
            if hasattr(self, 'ui_manager'):
                self.ui_manager.stop()
            if hasattr(self, 'tray_manager'):
                self.tray_manager.stop()
                
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
        """Настройка горячих клавиш с использованием менеджера"""
        try:
            # Добавляем горячие клавиши через менеджер
            self.hotkey_manager.add_hotkey(
                self.settings.get("hotkeys")["pause"],
                self.pause_resume_timer,
                cooldown=0.3  # Добавляем задержку 300мс между срабатываниями
            )
            self.hotkey_manager.add_hotkey(
                self.settings.get("hotkeys")["reset"],
                self.reset_timer,
                cooldown=0.5  # Добавляем задержку 500мс между срабатываниями
            )
            self.logger.info("Hotkeys setup completed")
        except Exception as e:
            self.logger.error(f"Error setting up hotkeys: {e}")

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

        # Регистрируем виджеты в UI менеджере
        self.ui_manager.register_widget('timer', self.timer_label)
        self.ui_manager.register_widget('progress', self.progress)
        self.ui_manager.register_widget('status', self.status_label)
        self.ui_manager.register_widget('process_list', self.process_status, 2.0)

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
            # Обновляем данные через UI менеджер
            self.ui_manager.queue_update('timer', self.remaining_time)
            self.ui_manager.queue_update('progress', self.remaining_time)
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        elif self.remaining_time <= 0 and self.running:
            # Проверяем достижения при завершении таймера
            self.achievement_manager.check_achievements({
                'current_time': datetime.now()
            })
            self.show_break_notification("Время вышло", "Пора сделать перерыв!")

    def update_timer_display(self):
        """Метод больше не используется напрямую"""
        pass

    def update_ui_status(self, status):
        """Обновляет статус в UI"""
        self.ui_manager.queue_update('status', status)

    def update_process_status(self):
        """Обновляет информацию о запущенных процессах"""
        active_processes = [p for p in self.process_monitor.get_active_processes()
                          if p in self.settings.get("processes")]
        if active_processes:
            processes_text = ', '.join(active_processes)
        else:
            processes_text = "нет"
        self.ui_manager.queue_update('process_list', processes_text)

    def track_games(self):
        """Следит за играми и отслеживает время."""
        start_time = None
        last_update = time.time()
        poll_interval = 1.0  # интервал проверки в секундах

        while self.running and not self.paused:
            active_processes = [p for p in self.process_monitor.get_active_processes()
                            if p in self.settings.get("processes")]
            
            if active_processes:
                current_time = time.time()
                
                if start_time is None:
                    start_time = current_time
                
                # Обновляем UI и проверяем достижения каждые N секунд
                update_interval = 5  # интервал обновления в секундах
                if current_time - last_update >= update_interval:
                    elapsed = current_time - start_time
                    self.remaining_time -= elapsed
                    self.ui_manager.queue_update('progress', self.remaining_time)
                    
                    # Обновляем статистику использования
                    for process in active_processes:
                        self.process_monitor.log_usage(process, elapsed)
                    
                    # Проверяем достижения
                    self.achievement_manager.add_break_time(int(elapsed))
                    self.achievement_manager.check_achievements({
                        'current_time': datetime.now()
                    })
                    
                    # Обновляем UI
                    self.ui_manager.queue_update('status', "Игра запущена")
                    self.ui_manager.queue_update('timer', self.remaining_time)
                    
                    last_update = current_time
                    start_time = current_time
                
                # Проверяем окончание времени
                if self.remaining_time <= 0:
                    self.show_break_notification("Время вышло", "Пора сделать перерыв!")
                    break
            else:
                start_time = None
                self.ui_manager.queue_update('status', "Игра не запущена")
            
            # Используем увеличенный интервал сна
            time.sleep(poll_interval)

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
