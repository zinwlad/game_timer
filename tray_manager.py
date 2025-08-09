import logging
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
import os

class TrayManager:
    """
    Управляет иконкой приложения в системном трее с использованием PyQt5.
    """
    def __init__(self, app_window):
        """
        Инициализация менеджера трея.
        :param app_window: Экземпляр главного окна приложения (GameTimerApp).
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app = app_window.app
        self.main_window = app_window

        self.tray_icon = QSystemTrayIcon(self.get_icon(), self.main_window)
        self.tray_icon.setToolTip("Game Timer")

        menu = QMenu()
        show_action = QAction("Показать", self.main_window)
        quit_action = QAction("Выход", self.main_window)

        show_action.triggered.connect(self.main_window.show_main_window)
        quit_action.triggered.connect(self.main_window.quit_app)

        menu.addAction(show_action)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.logger.info("Tray Manager initialized.")

    def get_icon(self, icon_name="icon.png"):
        """Загружает иконку из файла.
        Порядок поиска: timer.ico -> Icon_game_timer.png -> icon.png -> стандартная.
        """
        base_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(base_dir, 'timer.ico'),
            os.path.join(base_dir, 'Icon_game_timer.png'),
            os.path.join(base_dir, icon_name),
        ]
        for path in candidates:
            if os.path.exists(path):
                return QIcon(path)
        self.logger.warning("No tray icon found (timer.ico/Icon_game_timer.png/icon.png). Using default icon.")
        default_icon = self.main_window.style().standardIcon(self.main_window.style().SP_ComputerIcon)
        return default_icon

    def on_tray_icon_activated(self, reason):
        """Обрабатывает клики по иконке в трее."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.show_main_window()

    def set_icon(self, icon_name):
        """Меняет иконку в трее."""
        self.tray_icon.setIcon(self.get_icon(icon_name))

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, msecs=5000):
        """Показывает уведомление из трея."""
        self.tray_icon.showMessage(title, message, icon, msecs)
