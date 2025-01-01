import psutil
import time
import tkinter as tk
from tkinter import simpledialog, ttk, messagebox
from threading import Thread
import concurrent.futures
import os
import winsound
from datetime import datetime
import win32gui
import win32con
import win32com.client
import keyboard

from logger import Logger
from settings import Settings
from theme_manager import ThemeManager
from hotkey_manager import HotkeyManager
from ui_manager import UIManager
from tray_manager import TrayManager
from autostart_manager import AutostartManager
from process_monitor import ProcessMonitor
from activity_monitor import ActivityMonitor
from achievement_manager import AchievementManager
from timer_notifications import TimerNotifications
from game_blocker import GameBlocker
from timer_manager import TimerManager

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
            
            # Инициализация блокировщика игр
            self.game_blocker = GameBlocker(self.root, self.settings.get('processes', []))
            
            self.activity_monitor = ActivityMonitor(self.settings)
            self.process_monitor = self._init_process_monitor()
            self.achievement_manager = AchievementManager(self.settings, root)
            self.notifications = TimerNotifications(self.root)
            
            # Делаем окно адаптивным
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_rowconfigure(0, weight=1)
            
            # Основной контейнер
            main_frame = ttk.Frame(root)
            main_frame.grid(sticky="nsew", padx=10, pady=10)
            main_frame.grid_columnconfigure(0, weight=1)
            
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            
            # Остальные переменные
            self.mode = tk.StringVar(value=self.settings.get("mode", "countdown"))
            self.hours = tk.IntVar(value=self.settings.get("hours", 0))
            self.minutes = tk.IntVar(value=self.settings.get("minutes", 0))
            
            # Создаем виджеты
            self.create_widgets(main_frame)
            
            # Инициализируем менеджер таймера
            self.timer_manager = TimerManager(root, self.game_blocker, self.ui_manager, self.settings)
            self.timer_manager.set_ui_elements(
                self.timer_label,
                self.start_button,
                self.pause_button,
                self.reset_button,
                self.mode
            )
            
            self.setup_hotkeys()
            self.check_autostart()
            
            # Применяем тему
            self.theme_manager.apply_theme(self.settings.get("theme", "light"))
            
            # Запускаем мониторинг активности
            self.root.after(1000, self.check_user_activity)
            
            # Обработка закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GameTimerApp: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось инициализировать приложение: {str(e)}")
            self.quit_app()
            
    def start_timer(self):
        """Запускает выбранный режим."""
        hours = self.hours.get()
        minutes = self.minutes.get()
        result = self.timer_manager.start_timer(hours, minutes)
        
        if isinstance(result, tuple):  # Если возникла ошибка
            _, error_message = result
            self.logger.error(f"Failed to start timer: {error_message}")
            messagebox.showerror("Ошибка", f"Не удалось запустить таймер: {error_message}")
            
    def pause_timer(self):
        """Ставит таймер на паузу или возобновляет его."""
        self.timer_manager.pause_timer()
        
    def reset_timer(self):
        """Сбрасывает таймер."""
        result = self.timer_manager.reset_timer()
        if isinstance(result, tuple):  # Если возникла ошибка
            _, error_message = result
            self.logger.error(f"Error resetting timer: {error_message}")
            messagebox.showerror("Ошибка", f"Не удалось сбросить таймер: {error_message}")
            
    def _init_settings(self):
        """Инициализация настроек"""
        try:
            return Settings()
        except Exception as e:
            self.logger.error(f"Failed to initialize settings: {str(e)}")
            # Показываем уведомление только при ошибке
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
        
        if not is_active and not self.timer_manager.is_paused() and self.timer_manager.is_running():
            self.pause_timer()
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
            # Добавляем горячие клавиши для продления времени
            self.hotkey_manager.add_hotkey('ctrl+alt+5', lambda: self.add_time(5))
            self.hotkey_manager.add_hotkey('ctrl+alt+0', lambda: self.add_time(10))
            self.hotkey_manager.add_hotkey('ctrl+space', self.pause_timer)
        except Exception as e:
            self.logger.error(f"Failed to setup hotkeys: {str(e)}")
            
    def add_time(self, minutes: int):
        """Добавляет время к таймеру"""
        if not self.timer_manager.is_running():
            return
            
        # Проверяем лимит продлений (максимум 3)
        if not hasattr(self, 'extensions_count'):
            self.extensions_count = 0
            
        if self.extensions_count >= 3:
            self.notifications.show_extension_limit()
            return
            
        self.timer_manager.add_time(minutes * 60)
        self.extensions_count += 1
        self.notifications.show_extension_success(minutes, 3 - self.extensions_count)
        
    def create_widgets(self, parent):
        """Создает адаптивный интерфейс"""
        # Основной заголовок
        title_frame = ttk.Frame(parent)
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(title_frame, text="Game Timer", 
                 font=("Comic Sans MS", 24, "bold")).grid(row=0, column=0)
        
        # Фрейм для пресетов
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
        ttk.Radiobutton(mode_frame, text="Таймер", variable=self.mode, value="countdown").grid(row=0, column=0, padx=20)
        ttk.Radiobutton(mode_frame, text="Отслеживание игр", variable=self.mode, value="track").grid(row=0, column=1, padx=20)
        
        # Ввод времени
        time_frame = ttk.LabelFrame(parent, text="Установка времени", padding=10)
        time_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=5)
        
        ttk.Entry(time_frame, textvariable=self.hours, width=5).grid(row=0, column=0, padx=2)
        ttk.Label(time_frame, text="часов").grid(row=0, column=1, padx=(2, 10))
        
        ttk.Entry(time_frame, textvariable=self.minutes, width=5).grid(row=0, column=2, padx=2)
        ttk.Label(time_frame, text="минут").grid(row=0, column=3, padx=2)

        # Кнопки управления
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        self.start_button = ttk.Button(btn_frame, text="Начать", command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(btn_frame, text="Пауза", command=self.pause_timer, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.reset_button = ttk.Button(btn_frame, text="Сброс", command=self.reset_timer, state=tk.DISABLED)
        self.reset_button.grid(row=0, column=2, padx=5)

        # Кнопка настройки процессов
        ttk.Button(btn_frame, text="Настройка процессов", command=self.configure_processes).grid(row=0, column=3, padx=5)

        # Отображение времени
        self.timer_label = tk.Label(parent, text="Оставшееся время: --:--:--",
                                  font=("Arial", 16, "bold"))
        self.timer_label.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # Статус
        self.status_label = tk.Label(parent, text="Статус: Ожидание",
                                   font=("Arial", 12))
        self.status_label.grid(row=7, column=0, padx=20, pady=5, sticky="ew")

        # Регистрируем виджеты в UI менеджере
        self.ui_manager.register_widget('timer', self.timer_label)
        self.ui_manager.register_widget('status', self.status_label)
        self.ui_manager.register_widget('process_list', self.process_status)

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

    def update_process_status(self):
        """Обновляет информацию о запущенных процессах"""
        active_processes = [p for p in self.process_monitor.get_active_processes()
                          if p in self.settings.get("processes")]
        if active_processes:
            processes_text = ', '.join(active_processes)
        else:
            processes_text = "нет"
        self.ui_manager.queue_update('process_list', processes_text)

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
        app.quit_app()
