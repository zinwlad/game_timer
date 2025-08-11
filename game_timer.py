"""
Главный модуль приложения Game Timer.
"""
import sys
import logging
import ctypes
import time
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, QtCore, QtGui
from notification_window import NotificationWindow
from countdown_overlay import CountdownOverlay

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

        # Вкладки
        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Вкладка Главная ---
        main_tab = QtWidgets.QWidget()
        main_tab_layout = QtWidgets.QVBoxLayout(main_tab)

        # --- Статистика (сводка) ---
        stats_group = QtWidgets.QGroupBox("Статистика")
        stats_layout = QtWidgets.QVBoxLayout()
        self.stats_today = QtWidgets.QLabel("Сегодня сыграно: 00:00:00")
        self.stats_left = QtWidgets.QLabel("Осталось: 02:00:00")
        self.stats_week = QtWidgets.QLabel("За неделю: 00:00:00")
        stats_layout.addWidget(self.stats_today)
        stats_layout.addWidget(self.stats_left)
        stats_layout.addWidget(self.stats_week)
        stats_group.setLayout(stats_layout)
        main_tab_layout.addWidget(stats_group)

        # --- Заголовок ---
        title = QtWidgets.QLabel("Game Timer")
        title.setFont(QtGui.QFont("Helvetica", 22, QtGui.QFont.Bold))
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_tab_layout.addWidget(title)

        # --- Таймер ---
        self.time_display = QtWidgets.QLabel("00:00:00")
        font = self.time_display.font()
        font.setFamily("Helvetica")
        font.setPointSize(48)
        self.time_display.setFont(font)
        self.time_display.setAlignment(QtCore.Qt.AlignCenter)
        main_tab_layout.addWidget(self.time_display)

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
        main_tab_layout.addWidget(time_group)

        # --- Режим таймера ---
        mode_group = QtWidgets.QGroupBox("Режим таймера")
        mode_layout = QtWidgets.QHBoxLayout()
        self.mode = QtWidgets.QComboBox()
        self.mode.addItems(['Обратный отсчет', 'Прямой отсчет'])
        mode_layout.addWidget(self.mode)
        mode_group.setLayout(mode_layout)
        main_tab_layout.addWidget(mode_group)

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
        main_tab_layout.addWidget(control_group)

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
        main_tab_layout.addWidget(presets_group)

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
        main_tab_layout.addWidget(apps_group)

        # Подключение сигналов к кнопкам
        self.start_button.clicked.connect(self.app.start_timer)
        self.pause_button.clicked.connect(self.app.pause_timer)
        self.reset_button.clicked.connect(self.app.reset_timer)
        self.add_proc_button.clicked.connect(self.add_process)
        self.remove_proc_button.clicked.connect(self.remove_process)

        self.tabs.addTab(main_tab, "Главная")

        # --- Вкладка Статистика игр ---
        stats_tab = QtWidgets.QWidget()
        stats_tab_layout = QtWidgets.QVBoxLayout(stats_tab)
        period_layout = QtWidgets.QHBoxLayout()
        self.btn_today = QtWidgets.QPushButton("Сегодня")
        self.btn_week = QtWidgets.QPushButton("Неделя")
        period_layout.addWidget(self.btn_today)
        period_layout.addWidget(self.btn_week)
        stats_tab_layout.addLayout(period_layout)

        self.games_table = QtWidgets.QTableWidget(0, 4)
        self.games_table.setHorizontalHeaderLabels(["Игра", "Сегодня", "Неделя", "Сессий/Последний запуск"])
        self.games_table.horizontalHeader().setStretchLastSection(True)
        self.games_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        stats_tab_layout.addWidget(self.games_table)

        self.btn_today.clicked.connect(lambda: self.update_per_game_stats(self.process_manager, period='today'))
        self.btn_week.clicked.connect(lambda: self.update_per_game_stats(self.process_manager, period='week'))

        self.tabs.addTab(stats_tab, "Статистика игр")

        # --- Вкладка Достижения ---
        ach_tab = QtWidgets.QScrollArea()
        ach_tab.setWidgetResizable(True)
        ach_container = QtWidgets.QWidget()
        self.ach_layout = QtWidgets.QVBoxLayout(ach_container)
        self.ach_layout.addStretch(1)
        ach_tab.setWidget(ach_container)
        self.tabs.addTab(ach_tab, "Достижения")

    def update_per_game_stats(self, process_manager, period='today'):
        if not process_manager:
            return
        try:
            today = datetime.now().date()
            daily = process_manager.get_usage_by_process(today)
            start_week = today - timedelta(days=6)
            weekly = process_manager.get_usage_by_process_range(start_week, today + timedelta(days=1))
            meta = process_manager.get_last_seen_and_sessions(start_week, today + timedelta(days=1))

            names = sorted(set(list(daily.keys()) + list(weekly.keys())))
            self.games_table.setRowCount(len(names))
            for row, name in enumerate(names):
                t_day = daily.get(name, 0)
                t_week = weekly.get(name, 0)
                info = meta.get(name, {})
                last_seen = info.get('last_seen', '-')
                sessions = info.get('sessions', 0)
                def fmt(sec):
                    return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
                self.games_table.setItem(row, 0, QtWidgets.QTableWidgetItem(name))
                self.games_table.setItem(row, 1, QtWidgets.QTableWidgetItem(fmt(t_day)))
                self.games_table.setItem(row, 2, QtWidgets.QTableWidgetItem(fmt(t_week)))
                self.games_table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{sessions} / {last_seen}"))
        except Exception as e:
            self.logger.error(f"Ошибка обновления пер-игровой статистики: {e}")

    def refresh_achievements(self, achievement_manager):
        try:
            # Очистить предыдущие карточки (кроме stretch)
            while self.ach_layout.count() > 1:
                item = self.ach_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            for ach in achievement_manager.get_all_achievements():
                progress, total = achievement_manager.get_achievement_progress(ach.id)
                card = QtWidgets.QGroupBox(ach.title)
                v = QtWidgets.QVBoxLayout(card)
                v.addWidget(QtWidgets.QLabel(ach.description))
                pb = QtWidgets.QProgressBar()
                pb.setRange(0, max(1, total))
                pb.setValue(progress)
                v.addWidget(pb)
                status = "Получено" if ach.completed else f"Прогресс: {progress}/{total}"
                v.addWidget(QtWidgets.QLabel(status))
                self.ach_layout.insertWidget(self.ach_layout.count()-1, card)
        except Exception as e:
            self.logger.error(f"Ошибка обновления вкладки достижений: {e}")

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
        # Менеджер системного трея (иконка и меню)
        self.tray_manager = TrayManager(self)
        self.activity_monitor = ActivityMonitor(self.settings)
        self.achievement_manager = AchievementManager(self.settings, notification_callback=self.tray_manager.show_message)
        self.daily_limit_seconds = self.settings.get('daily_limit_hours', 2) * 3600
        self.timestamp = time.time()
        # Оверлей обратного отсчета (не мешает кликам)
        self.countdown_overlay = CountdownOverlay()

        # Сброс флага истечения таймера
        self.game_blocker.update_timer_state(False)
        # Флаг ручного запуска таймера
        self.manual_start = False

        # Перерыв (rest/cooldown)
        self.rest_until = None  # type: typing.Optional[datetime]
        try:
            _rest_str = self.settings.get('rest_until', '') or ''
            if _rest_str:
                self.rest_until = datetime.fromisoformat(_rest_str)
        except Exception:
            self.rest_until = None
        self._last_rest_notice_ts = 0.0

        self.setup_connections()
        self.gui_manager.start_process_monitoring(self.process_manager)
        self.update_stats()
        self.check_achievements()

        self.periodic_timer = QtCore.QTimer(self)
        self.periodic_timer.timeout.connect(self.run_periodic_tasks)
        self.periodic_timer.start(self.settings.get('periodic_tasks_interval_ms', 1000))

        self.passive_logging_timer = QtCore.QTimer(self)
        self.passive_logging_timer.timeout.connect(self.log_passive_usage)
        self.passive_logging_timer.start(self.settings.get('passive_logging_interval_ms', 60000))

    def setup_connections(self):
        self._init_hotkeys()

    def run_periodic_tasks(self):
        # 1) Проверка активности
        self.check_activity()
        # 2) Обслуживание перерыва
        self.clear_rest_if_elapsed()
        in_rest = self.is_in_rest()
        # 3) Проверка дневного лимита -> если превышен, устанавливаем перерыв до следующего дня
        try:
            if self.settings.get('block_until_next_day_on_limit', True):
                today_used = self.process_manager.get_daily_usage()
                if today_used >= int(self.daily_limit_seconds or 0):
                    # До полуночи
                    now = datetime.now()
                    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    # Если уже не стоит более длинный перерыв
                    if (not self.rest_until) or (self.rest_until < next_midnight):
                        self.start_rest_until(next_midnight)
        except Exception as e:
            self.logger.error(f"Ошибка проверки дневного лимита: {e}")
        # 4) Если во время перерыва запущены игры — немедленная блокировка + уведомление
        try:
            if in_rest and self.process_manager.is_any_monitored_process_running():
                self._notify_rest()
                self.game_blocker.update_timer_state(True)
                self.game_blocker.start_blocking_sequence()
        except Exception as e:
            self.logger.error(f"Ошибка блокировки во время перерыва: {e}")
        # 5) Обычный мониторинг авто-таймера и достижения
        self._autocountup_monitor()
        self.check_achievements()

    def start_timer(self):
        try:
            # Запрет запуска таймера во время перерыва
            if self.is_in_rest():
                self._notify_rest()
                return
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
            # Запрет запуска таймера во время перерыва
            if self.is_in_rest():
                self._notify_rest()
                return
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
            self.notification_window = NotificationWindow(
                message="Время истекло!\nТы молодец, пора сделать перерыв.",
                on_close_callback=self._on_notification_closed
            )
            self.notification_window.show(duration=0)
            # Достижения: показ уведомления
            try:
                self.achievement_manager.on_notification_shown()
            except Exception:
                pass
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
        try:
            # Запланировать проверку через 10 секунд
            delay = int(self.settings.get('notification_check_delay_ms', 10000))
            try:
                self.post_notification_timer.stop()
            except Exception:
                pass
            self.post_notification_timer = QtCore.QTimer(self)
            self.post_notification_timer.setSingleShot(True)
            self.post_notification_timer.timeout.connect(self._check_game_after_notification)
            self.post_notification_timer.start(delay)
        except Exception as e:
            self.logger.error(f"Ошибка в _on_notification_closed: {e}")

    def _check_game_after_notification(self):
        """Проверяет, завершена ли игра через 10 секунд после уведомления"""
        try:
            any_game_running = self.process_manager.is_any_monitored_process_running()
            if any_game_running:
                self.logger.info("Игра не завершена в течение 10 секунд после уведомления. Запускаем блокировку.")
                self._hide_countdown_overlay()
                self.game_blocker.update_timer_state(True)
                self.game_blocker.start_blocking_sequence()
                # Устанавливаем обязательный перерыв после принудительной блокировки
                if self.settings.get('enforce_cooldown_between_sessions', True):
                    minutes = int(self.settings.get('enforced_rest_minutes', 60) or 60)
                    self.start_rest(minutes)
            else:
                self.logger.info("Игра завершена в течение 10 секунд после уведомления.")
                self._hide_countdown_overlay()
                # Достижения: сделал перерыв вовремя
                try:
                    self.achievement_manager.on_break_taken()
                except Exception:
                    pass
            # Сбрасываем флаг, чтобы следующее истечение снова показало уведомление
            if hasattr(self, 'notification_shown'):
                delattr(self, 'notification_shown')
        except Exception as e:
            self.logger.error(f"Ошибка в _check_game_after_notification: {e}")

    def check_achievements(self):
        """Проверяет ежедневные достижения при запуске."""
        self.achievement_manager.on_daily_check()

    # --- Перерывы (rest/cooldown) ---
    def is_in_rest(self) -> bool:
        try:
            return bool(self.rest_until and datetime.now() < self.rest_until)
        except Exception:
            return False

    def _set_rest_until(self, until_dt: datetime):
        try:
            self.rest_until = until_dt
            self.settings.set('rest_until', until_dt.isoformat())
        except Exception as e:
            self.logger.error(f"Не удалось сохранить rest_until: {e}")

    def start_rest(self, minutes: int):
        try:
            minutes = int(minutes or 0)
            if minutes <= 0:
                return
            self._set_rest_until(datetime.now() + timedelta(minutes=minutes))
            self._notify_rest(initial=True)
        except Exception as e:
            self.logger.error(f"Ошибка запуска перерыва: {e}")

    def start_rest_until(self, until_dt: datetime):
        try:
            self._set_rest_until(until_dt)
            self._notify_rest(initial=True)
        except Exception as e:
            self.logger.error(f"Ошибка установки перерыва до даты: {e}")

    def clear_rest_if_elapsed(self):
        try:
            if self.rest_until and datetime.now() >= self.rest_until:
                self.rest_until = None
                self.settings.set('rest_until', "")
        except Exception as e:
            self.logger.error(f"Ошибка очистки перерыва: {e}")

    def rest_remaining_str(self) -> str:
        try:
            if not self.is_in_rest():
                return "00:00"
            delta = self.rest_until - datetime.now()
            total = int(delta.total_seconds())
            if total < 0:
                total = 0
            h = total // 3600
            m = (total % 3600) // 60
            s = total % 60
            if h > 0:
                return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"
        except Exception:
            return "00:00"

    def _notify_rest(self, initial: bool = False):
        try:
            now_ts = time.time()
            # Не спамим уведомления чаще, чем раз в 15 секунд, если это не первичное уведомление
            if not initial and (now_ts - self._last_rest_notice_ts) < 15:
                return
            self._last_rest_notice_ts = now_ts
            remaining = self.rest_remaining_str()
            self.tray_manager.show_message("Перерыв", f"Сейчас идёт перерыв. Осталось: {remaining}")
        except Exception:
            pass

    def log_passive_usage(self):
        """Пассивный учет времени: каждые N секунд добавляем время для запущенных игр,
        если пользователь не запускал таймер вручную."""
        try:
            if getattr(self, 'manual_start', False):
                return
            # Проверяем, запущены ли отслеживаемые процессы
            active = set(self.process_manager.get_active_processes())
            monitored = set((p or '').strip().lower() for p in (self.process_manager.get_monitored_processes() or []))
            if not active or not monitored:
                return
            running_tracked = active & monitored
            if not running_tracked:
                return
            interval_sec = max(60, int(self.settings.get('passive_logging_interval_ms', 600000) / 1000))
            for proc_name in running_tracked:
                self.process_manager.log_usage(proc_name, interval_sec)
            self.logger.debug(f"Пассивно залогировано {interval_sec} сек для: {', '.join(sorted(running_tracked))}")
            # Обновим статистику на экране
            self.update_stats()
        except Exception as e:
            self.logger.error(f"Ошибка пассивного учёта времени: {e}")

    # --- Overlay helpers ---
    def _show_countdown_overlay(self, seconds: int):
        try:
            secs = int(seconds or 0)
            if secs <= 0:
                return
            self.countdown_overlay.start(secs)
        except Exception as e:
            self.logger.error(f"Не удалось показать оверлей обратного отсчета: {e}")

    def _hide_countdown_overlay(self):
        try:
            self.countdown_overlay.stop()
        except Exception:
            pass

    def update_stats(self):
        try:
            today = self.process_manager.get_daily_usage()
            week = self.process_manager.get_weekly_usage()
            left = max(0, self.daily_limit_seconds - today)
            self.gui_manager.stats_today.setText(f"Сегодня: {today//3600:02d}:{(today%3600)//60:02d}:{today%60:02d}")
            self.gui_manager.stats_left.setText(f"Осталось: {left//3600:02d}:{(left%3600)//60:02d}:{left%60:02d}")
            self.gui_manager.stats_week.setText(f"За неделю: {week//3600:02d}:{(week%3600)//60:02d}:{week%60:02d}")
            # Обновить пер-игровую таблицу и достижения
            self.gui_manager.update_per_game_stats(self.process_manager, period='today')
            self.gui_manager.refresh_achievements(self.achievement_manager)
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")

    def _init_hotkeys(self):
        # Встроенные хоткеи изменения лимита и разблокировки (оставляем)
        self.hotkey_manager.register_limit_hotkeys(self.increase_daily_limit, self.decrease_daily_limit)
        self.hotkey_manager.register_blocker_hotkey(self.game_blocker.unblock)

        # Регистрация хоткеев из настроек
        self.hotkey_manager.register_from_settings(
            self.settings,
            callbacks={
                "start": self.start_timer,
                "pause_resume": self.pause_resume,
                "reset": self.reset_timer,
                "add_5_min": self.add_5_minutes,
            }
        )

    def pause_resume(self):
        """Тоггл паузы/продолжения для хоткея."""
        self.timer_manager.toggle_pause()

    def add_5_minutes(self):
        """Быстро добавляет +5 минут к таймеру (если запущен)."""
        self.timer_manager.add_minutes(5)

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
