from PyQt5 import QtWidgets, QtCore, QtGui

class GUIManager(QtWidgets.QWidget):
    start_timer_signal = QtCore.pyqtSignal()
    pause_timer_signal = QtCore.pyqtSignal()
    reset_timer_signal = QtCore.pyqtSignal()
    preset_applied_signal = QtCore.pyqtSignal(int, int, int)  # hours, minutes, seconds

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.process_timer = None
        self.process_manager = None
        self.hotkey_manager = None
        self.daily_limit_seconds = 2 * 60 * 60  # 2 часа по умолчанию
        self.autocountup_limit = self.daily_limit_seconds
        self.autocountup_active = False
        self._build_ui()

    def _build_ui(self):
        # Основная компоновка
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

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
            btn.clicked.connect(lambda _, h=h, m=m, s=s: self.preset_applied_signal.emit(h, m, s))
            presets_layout.addWidget(btn)
        presets_group.setLayout(presets_layout)
        main_layout.addWidget(presets_group)

        # --- Список приложений ---
        apps_group = QtWidgets.QGroupBox("Список отслеживаемых приложений")
        apps_layout = QtWidgets.QVBoxLayout()
        self.apps_list = QtWidgets.QListWidget()
        apps_layout.addWidget(self.apps_list)
        apps_group.setLayout(apps_layout)
        main_layout.addWidget(apps_group, stretch=1)

        # --- Добавление/удаление процесса ---
        input_layout = QtWidgets.QHBoxLayout()
        self.process_input = QtWidgets.QLineEdit()
        self.process_input.setPlaceholderText("Имя процесса.exe")
        self.add_process_button = QtWidgets.QPushButton("Добавить")
        self.remove_process_button = QtWidgets.QPushButton("Удалить")
        input_layout.addWidget(self.process_input)
        input_layout.addWidget(self.add_process_button)
        input_layout.addWidget(self.remove_process_button)
        main_layout.addLayout(input_layout)

        self.add_process_button.clicked.connect(self.add_process)
        self.remove_process_button.clicked.connect(self.remove_process)

        self.setLayout(main_layout)

        # Сигналы кнопок
        self.start_button.clicked.connect(self.start_timer_signal.emit)
        self.pause_button.clicked.connect(self.pause_timer_signal.emit)
        self.reset_button.clicked.connect(self.reset_timer_signal.emit)

    def set_buttons_enabled(self, running: bool):
        self.start_button.setEnabled(not running)
        self.pause_button.setEnabled(running)
        self.reset_button.setEnabled(running)

    def start_process_monitoring(self, process_manager):
        self.process_manager = process_manager
        self.update_process_list()
        from PyQt5.QtCore import QTimer
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.update_process_list)
        self.process_timer.start(5000)

    def update_process_list(self):
        if self.process_manager is None:
            return
        self.apps_list.clear()
        import psutil
        try:
            monitored = self.process_manager.settings.get("processes", [])
            running = set()
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    pname = proc.info['name'].lower() if proc.info.get('name') else ''
                    ppath = proc.info.get('exe', '').lower() if proc.info.get('exe') else ''
                    for m in monitored:
                        if m.lower() in pname or m.lower() in ppath:
                            running.add(m)
                except Exception:
                    continue
            # --- автотаймер: если есть запущенные игры, включаем прямой отсчет ---
            if hasattr(self.app, 'timer_manager'):
                timer = self.app.timer_manager
                any_game_running = bool(running)
                if any_game_running:
                    if not timer.running or timer.mode != 'countup':
                        timer.start_timer(0, 'countup')
                        self.autocountup_active = True
                else:
                    if timer.running and timer.mode == 'countup':
                        timer.pause_timer()
                        self.autocountup_active = False
            for m in monitored:
                status = "Запущен" if m in running else "Не запущен"
                self.apps_list.addItem(f"{m} — {status}")
            self.update_stats()
        except Exception as e:
            print(f"Ошибка при обновлении списка процессов: {e}")

    def get_ui_elements(self):
        """Возвращает основные UI элементы для использования в других компонентах"""
        return {
            'time_display': self.time_display,
            'start_button': self.start_button,
            'pause_button': self.pause_button,
            'reset_button': self.reset_button,
            'apps_list': self.apps_list,
            'hours': self.hours,
            'minutes': self.minutes,
            'seconds': self.seconds,
            'mode': self.mode
        }
        
    def update_button_states(self, is_running):
        """Обновляет состояние кнопок"""
        if is_running:
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.reset_button.config(state=tk.DISABLED)

    # --- Методы для управления списком процессов ---
    def add_process(self):
        name = self.process_input.text().strip()
        if not name or self.process_manager is None:
            return
        procs = self.process_manager.settings.get("processes", [])
        if name not in procs:
            procs.append(name)
            self.process_manager.settings.set("processes", procs)
        self.process_input.clear()
        self.update_process_list()

    def remove_process(self):
        items = self.apps_list.selectedItems()
        if not items or self.process_manager is None:
            return
        procs = self.process_manager.settings.get("processes", [])
        for item in items:
            pname = item.text().split(" — ")[0]
            if pname in procs:
                procs.remove(pname)
        self.process_manager.settings.set("processes", procs)
        self.update_process_list()

from settings_manager import SettingsManager
from game_blocker import GameBlocker
from timer_manager import TimerManager
from process_manager import ProcessManager
from hotkey_manager import HotkeyManager

from tray_manager import TrayManager
from hotkey_manager import HotkeyManager
from notification_window import NotificationWindow
from activity_monitor import ActivityMonitor
from autostart_manager import AutostartManager
from achievement_manager import AchievementManager

class GameTimerApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Timer")
        self.setMinimumSize(500, 800)
        self.settings = SettingsManager()
        self.process_manager = ProcessManager(self.settings)
        self.gui_manager = GUIManager(self)
        self.setCentralWidget(self.gui_manager)
        self.gui_manager.start_process_monitoring(self.process_manager)

        # Менеджеры
        self.game_blocker = GameBlocker(self.settings)
        self.activity_monitor = ActivityMonitor(self.settings)
        self.achievement_manager = AchievementManager(self.settings)
        self.notification_window = None
        self.timer_manager = TimerManager(self, self.game_blocker, self.gui_manager, self.settings)

        # Подключение сигналов GUI
        self.gui_manager.start_timer_signal.connect(self.start_timer)
        self.gui_manager.pause_timer_signal.connect(self.pause_timer)
        self.gui_manager.reset_timer_signal.connect(self.reset_timer)
        self.gui_manager.preset_applied_signal.connect(self.apply_preset)

        # Таймеры для периодических задач
        self.activity_timer = QtCore.QTimer(self)
        self.activity_timer.timeout.connect(self.check_activity)
        self.activity_timer.start(1000)

        self.achievement_timer = QtCore.QTimer(self)
        self.achievement_timer.timeout.connect(self.check_achievements)
        self.achievement_timer.start(60000)

    def start_timer(self):
        hours = int(self.gui_manager.hours.text() or 0)
        minutes = int(self.gui_manager.minutes.text() or 0)
        seconds = int(self.gui_manager.seconds.text() or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        mode = self.gui_manager.mode.currentText()
        if total_seconds > 0 or mode == "Прямой отсчет":
            self.timer_manager.start_timer(total_seconds, mode)
            self.gui_manager.set_buttons_enabled(True)
            self.achievement_manager.on_timer_start()

    def pause_timer(self):
        self.timer_manager.pause_timer()
        self.gui_manager.set_buttons_enabled(False)

    def reset_timer(self):
        self.timer_manager.reset_timer()
        self.gui_manager.set_buttons_enabled(False)

    def apply_preset(self, hours, minutes, seconds):
        self.gui_manager.hours.setText(str(hours))
        self.gui_manager.minutes.setText(str(minutes))
        self.gui_manager.seconds.setText(str(seconds))

    def show_notification(self, title="Уведомление", message=""):
        if not self.notification_window:
            self.notification_window = NotificationWindow(title, message)
        else:
            self.notification_window.update_message(message)
        self.notification_window.show()
        self.achievement_manager.on_notification_shown()

    def check_activity(self):
        if self.timer_manager.is_running():
            is_active = self.activity_monitor.check_activity()
            if not is_active and not self.timer_manager.is_paused():
                self.pause_timer()
                self.show_notification("Таймер на паузе", "Нет активности пользователя")

    def check_achievements(self):
        self.achievement_manager.check_time_achievements()
        self.achievement_manager.on_daily_check()
        if self.timer_manager.is_running():
            elapsed = self.timer_manager.get_elapsed_time()
            self.achievement_manager.on_timer_tick(elapsed)

    # --- Автоматический контроль лимита для прямого отсчета ---
    def _autocountup_monitor(self):
        timer = self.timer_manager
        # --- Проверяем дневной лимит ---
        pm = self.process_manager
        if pm is not None:
            today_used = pm.get_daily_usage()
            left = max(0, self.daily_limit_seconds - today_used)
            self.autocountup_limit = self.daily_limit_seconds
            # Обновляем статистику
            self.update_stats()
            # Если лимит исчерпан — блокировка
            if today_used >= self.daily_limit_seconds:
                self.show_notification("Дневной лимит!", f"Сегодня вы уже сыграли {today_used//3600:02}:{(today_used%3600)//60:02}:{today_used%60:02}. Пора сделать перерыв!")
                self.game_blocker.start_blocking_sequence()
                if timer.running and timer.mode == 'countup':
                    timer.pause_timer()
        # --- Сессионный лимит (для совместимости) ---
        if timer.running and timer.mode == 'countup':
            elapsed = timer.get_elapsed_time()
            limit = self.autocountup_limit
            if elapsed >= limit:
                # Показываем уведомление и блокируем
                self.show_notification("Лимит времени!", f"Вы играете уже {elapsed//3600:02}:{(elapsed%3600)//60:02}:{elapsed%60:02}. Пора сделать перерыв!")
                self.game_blocker.start_blocking_sequence()
                timer.pause_timer()

    def closeEvent(self, event):
        # Здесь можно добавить логику для сохранения состояния или подтверждения выхода
        event.accept()

    # --- Методы для статистики и лимитов ---
    def update_stats(self):
        pm = self.process_manager
        if pm is None:
            return
        today = pm.get_daily_usage()
        week = pm.get_weekly_usage()
        left = max(0, self.daily_limit_seconds - today)
        self.gui_manager.stats_today.setText(f"Сегодня сыграно: {today//3600:02}:{(today%3600)//60:02}:{today%60:02}")
        self.gui_manager.stats_left.setText(f"Осталось: {left//3600:02}:{(left%3600)//60:02}:{left%60:02}")
        self.gui_manager.stats_week.setText(f"За неделю: {week//3600:02}:{(week%3600)//60:02}:{week%60:02}")

    def _init_hotkeys(self):
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.register_limit_hotkeys(self.increase_daily_limit, self.decrease_daily_limit)
        self.hotkey_manager.register_blocker_hotkey(self.unblock_block_screen)

    def increase_daily_limit(self):
        self.daily_limit_seconds += 10 * 60  # +10 минут
        self.update_stats()

    def decrease_daily_limit(self):
        self.daily_limit_seconds = max(0, self.daily_limit_seconds - 10 * 60)
        self.update_stats()

    def unblock_block_screen(self):
        """Быстрое снятие блокировки по горячей клавише (Ctrl+Alt+B)"""
        # Найти и закрыть активное окно BlockScreen (если есть)
        if hasattr(self.app, 'game_blocker') and hasattr(self.app.game_blocker, 'block_screen'):
            block_screen = self.app.game_blocker.block_screen
            if block_screen and block_screen.isVisible():
                block_screen.accept()  # Снимет блокировку

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = GameTimerApp()
    window.show()
    sys.exit(app.exec_())
        
    def hide_window(self):
        """Скрывает главное окно"""
        self.root.withdraw()
        
    def quit_app(self):
        """Закрывает приложение"""
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.stop()
        if hasattr(self, 'tray_manager'):
            self.tray_manager.stop()
        if hasattr(self, 'game_blocker'):
            self.game_blocker.stop()
        self.root.quit()
        
    def on_closing(self):
        """Обработчик закрытия приложения"""
        self.hide_window()  # Скрываем окно вместо закрытия

if __name__ == "__main__":
    root = tk.Tk()
    app = GameTimerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
