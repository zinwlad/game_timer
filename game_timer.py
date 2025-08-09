"""
Главный модуль приложения Game Timer.
"""
import sys
import logging
import ctypes
from PyQt5 import QtWidgets, QtCore, QtGui
from notification_window import NotificationWindow

from settings_manager import SettingsManager
from game_blocker import GameBlocker
from timer_manager import TimerManager
from process_manager import ProcessManager
from hotkey_manager import HotkeyManager
from activity_monitor import ActivityMonitor
from achievement_manager import AchievementManager
from sound_manager import SoundManager
from tray_manager import TrayManager

# --- Single instance helper (Windows named mutex) ---
def _acquire_single_instance_mutex():
    """Возвращает (handle, acquired). Если уже запущено — acquired=False."""
    try:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, "Global\\GameTimerMutex")
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if mutex == 0:
            return None, True  # не удалось создать — не блокируем запуск
        if last_error == ERROR_ALREADY_EXISTS:
            return mutex, False
        return mutex, True
    except Exception:
        return None, True

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class GUIManager(QtWidgets.QWidget):
    """Управляет всеми элементами пользовательского интерфейса."""
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(self.__class__.__name__)
        self.process_manager = None  # Будет установлен позже
        self._build_ui()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        # ... (UI code remains the same as the corrected version)
        # --- Статистика ---
        stats_group = QtWidgets.QGroupBox("Статистика")
        stats_layout = QtWidgets.QVBoxLayout()
        self.stats_today = QtWidgets.QLabel("Сегодня сыграно: 00:00:00")
        self.stats_left = QtWidgets.QLabel("Осталось: 02:00:00")
        self.stats_week = QtWidgets.QLabel("За неделю: 00:00:00")
        stats_layout.addWidget(self.stats_today)
        stats_layout.addWidget(self.stats_left)
        stats_layout.addWidget(self.stats_week)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # --- Заголовок ---
        title = QtWidgets.QLabel("Game Timer")
        title.setFont(QtGui.QFont("Helvetica", 22, QtGui.QFont.Bold))
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # --- Таймер ---
        self.time_display = QtWidgets.QLabel("00:00:00")
        font = self.time_display.font()
        font.setFamily("Helvetica")
        font.setPointSize(48)
        self.time_display.setFont(font)
        self.time_display.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.time_display)

        # --- Ввод времени ---
        time_group = QtWidgets.QGroupBox("Время")
        time_layout = QtWidgets.QHBoxLayout()
        self.hours = QtWidgets.QLineEdit('0')
        self.minutes = QtWidgets.QLineEdit('0')
        self.seconds = QtWidgets.QLineEdit('0')
        for widget, label in zip([self.hours, self.minutes, self.seconds], ["Часы:", "Минуты:", "Секунды:"]):
            time_layout.addWidget(QtWidgets.QLabel(label))
            widget.setMaximumWidth(40)
            widget.setValidator(QtGui.QIntValidator(0, 99))
            time_layout.addWidget(widget)
        time_group.setLayout(time_layout)
        main_layout.addWidget(time_group)

        # --- Режим таймера ---
        mode_group = QtWidgets.QGroupBox("Режим таймера")
        mode_layout = QtWidgets.QHBoxLayout()
        self.mode = QtWidgets.QComboBox()
        self.mode.addItems(['Обратный отсчет', 'Прямой отсчет'])
        mode_layout.addWidget(self.mode)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # --- Кнопки управления ---
        control_group = QtWidgets.QGroupBox("Управление")
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton('Старт')
        self.pause_button = QtWidgets.QPushButton('Пауза')
        self.reset_button = QtWidgets.QPushButton('Сброс')
        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.pause_button)
        btn_layout.addWidget(self.reset_button)
        control_group.setLayout(btn_layout)
        main_layout.addWidget(control_group)

        # --- Пресеты ---
        presets_group = QtWidgets.QGroupBox("Пресеты")
        presets_layout = QtWidgets.QHBoxLayout()
        presets = [
            ("10 сек", 0, 0, 10),
            ("30 мин", 0, 30, 0),
            ("1 час", 1, 0, 0),
            ("2 часа", 2, 0, 0)
        ]
        for text, h, m, s in presets:
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(lambda _, h=h, m=m, s=s: self.app.apply_preset(h, m, s))
            presets_layout.addWidget(btn)
        presets_group.setLayout(presets_layout)
        main_layout.addWidget(presets_group)

        # --- Список процессов ---
        apps_group = QtWidgets.QGroupBox("Отслеживаемые приложения")
        apps_layout = QtWidgets.QVBoxLayout()
        self.apps_list = QtWidgets.QListWidget()
        apps_layout.addWidget(self.apps_list)
        proc_btn_layout = QtWidgets.QHBoxLayout()
        self.add_proc_button = QtWidgets.QPushButton("Добавить")
        self.remove_proc_button = QtWidgets.QPushButton("Удалить")
        proc_btn_layout.addWidget(self.add_proc_button)
        proc_btn_layout.addWidget(self.remove_proc_button)
        apps_layout.addLayout(proc_btn_layout)
        apps_group.setLayout(apps_layout)
        main_layout.addWidget(apps_group)

        # Подключение сигналов к кнопкам
        self.start_button.clicked.connect(self.app.start_timer)
        self.pause_button.clicked.connect(self.app.pause_timer)
        self.reset_button.clicked.connect(self.app.reset_timer)
        self.add_proc_button.clicked.connect(self.add_process)
        self.remove_proc_button.clicked.connect(self.remove_process)

    def start_process_monitoring(self, process_manager):
        self.process_manager = process_manager
        self.update_process_list()
        self.process_timer = QtCore.QTimer(self)
        self.process_timer.timeout.connect(self.update_process_list)
        self.process_timer.start(self.app.settings.get('process_check_interval_ms', 5000))  # Настраиваемый интервал проверки

    def update_process_list(self):
        if self.process_manager is None: return
        try:
            self.apps_list.clear()
            monitored_apps = self.process_manager.get_monitored_processes()
            active_apps = self.process_manager.get_active_processes()
            for app_name in monitored_apps:
                status = "запущен" if app_name.lower() in active_apps else "не запущен"
                item_text = f"{app_name} — {status}"
                self.apps_list.addItem(item_text)
            self.app.update_stats()
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении списка процессов: {e}")

    def add_process(self):
        proc_name, ok = QtWidgets.QInputDialog.getText(self, "Добавить процесс", "Имя процесса (например, 'game.exe'):")
        if ok and proc_name:
            self.process_manager.add_process_to_monitor(proc_name)
            self.update_process_list()

    def remove_process(self):
        selected = self.apps_list.currentItem()
        if not selected: return
        proc_name = selected.text().split(" — ")[0]
        self.process_manager.remove_process_from_monitor(proc_name)
        self.update_process_list()

class GameTimerApp(QtWidgets.QMainWindow):
    """Основной класс приложения."""
    def __init__(self, app):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setWindowTitle("Game Timer")
        self.setMinimumSize(500, 800)
        self.app = app
        self.settings = SettingsManager()
        self.process_manager = ProcessManager(self.settings)
        self.sound_manager = SoundManager(self.settings)
        self.gui_manager = GUIManager(self)
        self.setCentralWidget(self.gui_manager)
        self.game_blocker = GameBlocker(self.settings)
        self.timer_manager = TimerManager(self, self.game_blocker, self.gui_manager, self.settings)
        self.hotkey_manager = HotkeyManager()
        self.activity_monitor = ActivityMonitor(self.settings)
        self.tray_manager = TrayManager(self)
        self.achievement_manager = AchievementManager(self.settings, notification_callback=self.tray_manager.show_message)
        self.daily_limit_seconds = self.settings.get('daily_limit_hours', 2) * 3600

        # Сброс флага истечения таймера
        self.game_blocker.update_timer_state(False)
        # Флаг ручного запуска таймера
        self.manual_start = False

        self.setup_connections()
        self.gui_manager.start_process_monitoring(self.process_manager)
        self.update_stats()
        self.check_achievements()

        self.periodic_timer = QtCore.QTimer(self)
        self.periodic_timer.timeout.connect(self.run_periodic_tasks)
        self.periodic_timer.start(self.settings.get('periodic_tasks_interval_ms', 1000))

    def setup_connections(self):
        self._init_hotkeys()

    def run_periodic_tasks(self):
        self.check_activity()
        self._autocountup_monitor()
        self.check_achievements()

    def start_timer(self):
        try:
            mode_text = self.gui_manager.mode.currentText()
            mode = 'countdown' if 'Обратный' in mode_text else 'countup'
            if mode == 'countdown':
                h = int(self.gui_manager.hours.text() or 0)
                m = int(self.gui_manager.minutes.text() or 0)
                s = int(self.gui_manager.seconds.text() or 0)
                self.timer_manager.start_timer(h * 3600 + m * 60 + s, mode)
            else:
                self.timer_manager.start_timer(0, mode)
            # Установка флага ручного запуска
            # Сброс показать-один-раз уведомления и таймера проверки, если были
            if hasattr(self, 'post_notification_timer'):
                self.post_notification_timer.stop()
            if hasattr(self, 'notification_shown'):
                del self.notification_shown
            self.manual_start = True
        except Exception as e:
            self.logger.error(f"Ошибка при запуске таймера: {e}")

    def pause_timer(self): self.timer_manager.pause_timer()
    def reset_timer(self): 
        self.timer_manager.reset_timer()
        # Сброс флага истечения таймера
        self.game_blocker.update_timer_state(False)
        # Сброс флага ручного запуска
        self.manual_start = False
        # Остановка таймера проверки после уведомления и сброс метки показа уведомления
        if hasattr(self, 'post_notification_timer'):
            self.post_notification_timer.stop()
        if hasattr(self, 'notification_shown'):
            del self.notification_shown

    def check_activity(self):
        """Проверяет активность пользователя и при необходимости ставит таймер на паузу."""
        try:
            is_active, _ = self.activity_monitor.check_activity()
            if not is_active and self.timer_manager.is_running():
                self.timer_manager.pause_timer()
                self.logger.info("Таймер поставлен на паузу из-за неактивности пользователя.")
        except Exception as e:
            self.logger.error(f"Ошибка при проверке активности: {e}")

    def start_timer_from_ui(self):
        """Запускает таймер с параметрами, установленными в UI."""
        try:
            mode_text = self.gui_manager.mode.currentText()
            mode = 'countdown' if 'Обратный' in mode_text else 'countup'
            if mode == 'countdown':
                h = int(self.gui_manager.hours.text() or 0)
                m = int(self.gui_manager.minutes.text() or 0)
                s = int(self.gui_manager.seconds.text() or 0)
                self.timer_manager.start_timer(h * 3600 + m * 60 + s, mode)
                self.logger.info(f"Игра запущена, таймер запущен в режиме countdown на {h:02d}:{m:02d}:{s:02d}.")
            else:
                self.timer_manager.start_timer(0, mode)
                self.logger.info("Игра запущена, таймер запущен в режиме countup.")
        except Exception as e:
            self.logger.error(f"Ошибка при запуске таймера из UI: {e}")

    def _autocountup_monitor(self):
        """Мониторинг процессов для авто-таймера"""
        any_game_running = self.process_manager.is_any_monitored_process_running()
        timer_running = self.timer_manager.is_running()
        is_countup = self.timer_manager.get_mode() == 'countup'
        
        # Проверяем, не истек ли таймер
        timer_expired = self.timer_manager.is_expired()
        
        # Если таймер истек, но игра все еще запущена, показываем уведомление
        if any_game_running and timer_expired and not hasattr(self, 'notification_shown'):
            # Показываем приятное уведомление
            self.notification_window = NotificationWindow(
                message="Время истекло!\nТы молодец, пора сделать перерыв.",
                on_close_callback=self._on_notification_closed
            )
            self.notification_window.show()
            self.notification_shown = True
            
            # Запускаем таймер на 10 секунд для проверки завершения игры
            self.post_notification_timer = QtCore.QTimer(self)
            self.post_notification_timer.timeout.connect(self._check_game_after_notification)
            self.post_notification_timer.start(self.settings.get('notification_check_delay_ms', 10000))
        elif not any_game_running and timer_running and is_countup:
            self.timer_manager.pause_timer()
            self.logger.info("Все игры закрыты, авто-таймер на паузе.")

    def _on_notification_closed(self):
        """Callback when notification window is closed by user"""
        self.logger.info("Notification window closed by user")
        # Останавливаем таймер проверки игры
        if hasattr(self, 'post_notification_timer'):
            self.post_notification_timer.stop()
        # Запускаем таймер на 10 секунд для проверки завершения игры
        self.post_notification_timer = QtCore.QTimer(self)
        self.post_notification_timer.timeout.connect(self._check_game_after_notification)
        self.post_notification_timer.start(self.settings.get('notification_check_delay_ms', 10000))

    def _check_game_after_notification(self):
        """Проверяет, завершена ли игра через 10 секунд после уведомления"""
        # Останавливаем таймер
        self.post_notification_timer.stop()
        
        # Проверяем, запущена ли игра
        if self.process_manager.is_any_monitored_process_running():
            # Показываем предупреждение и включаем блокировку
            self.logger.warning("Игра не завершена в течение 10 секунд после уведомления.")
            self.game_blocker.update_timer_state(True)
            self.game_blocker.start_blocking_sequence()
        else:
            self.logger.info("Игра завершена в течение 10 секунд после уведомления.")

    def check_achievements(self):
        """Проверяет ежедневные достижения при запуске."""
        self.achievement_manager.on_daily_check()

    def update_stats(self):
        try:
            today = self.process_manager.get_daily_usage()
            week = self.process_manager.get_weekly_usage()
            left = max(0, self.daily_limit_seconds - today)
            self.gui_manager.stats_today.setText(f"Сегодня: {today//3600:02d}:{(today%3600)//60:02d}:{today%60:02d}")
            self.gui_manager.stats_left.setText(f"Осталось: {left//3600:02d}:{(left%3600)//60:02d}:{left%60:02d}")
            self.gui_manager.stats_week.setText(f"За неделю: {week//3600:02d}:{(week%3600)//60:02d}:{week%60:02d}")
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")

    def _init_hotkeys(self):
        self.hotkey_manager.register_limit_hotkeys(self.increase_daily_limit, self.decrease_daily_limit)
        self.hotkey_manager.register_blocker_hotkey(self.game_blocker.unblock)

    def increase_daily_limit(self): self.daily_limit_seconds += 600; self.update_stats()
    def decrease_daily_limit(self): self.daily_limit_seconds = max(0, self.daily_limit_seconds - 600); self.update_stats()

    def show_main_window(self):
        """Показывает главное окно приложения."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        """Корректно завершает работу приложения."""
        self.tray_manager.tray_icon.hide()
        self.app.quit()

    def closeEvent(self, event): self.hide(); event.ignore()

    def apply_preset(self, hours, minutes, seconds):
        self.gui_manager.hours.setText(str(hours))
        self.gui_manager.minutes.setText(str(minutes))
        self.gui_manager.seconds.setText(str(seconds))

if __name__ == "__main__":
    # Гарантия единственного экземпляра через именованный mutex
    _mutex_handle, _acquired = _acquire_single_instance_mutex()
    if not _acquired:
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "Приложение уже запущено.",
                "Game Timer",
                0x10  # MB_ICONHAND
            )
        except Exception:
            pass
        sys.exit(0)

    app = QtWidgets.QApplication(sys.argv)
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(None, "Критическая ошибка", "Системный трей не поддерживается.")
        sys.exit(1)
    app.setQuitOnLastWindowClosed(False)
    window = GameTimerApp(app)
    window.show()
    try:
        rc = app.exec_()
    finally:
        try:
            if _mutex_handle:
                ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        except Exception:
            pass
    sys.exit(rc)
