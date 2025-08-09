from PyQt5 import QtWidgets, QtCore, QtGui
from win32api import GetSystemMetrics
import winsound
import time
import random
from logger import Logger
import os

"""
Файл: notification_window.py

Модуль для отображения всплывающих уведомлений пользователю в приложении Game Timer.
"""

class NotificationWindow(QtWidgets.QDialog):
    def __init__(self, title="Уведомление", message="", on_close_callback=None):
        super().__init__()
        self.on_close_callback = on_close_callback
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.logger = Logger("NotificationWindow", "logs/notifications.log")

        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Основной контейнер с тенью
        shadow_widget = QtWidgets.QWidget(self)
        shadow_widget.setObjectName("shadow_widget")
        shadow_widget.setStyleSheet("""
            QWidget#shadow_widget {
                background-color: #4A90E2;
                border-radius: 20px;
            }
        """)
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        shadow_widget.setGraphicsEffect(shadow)

        layout = QtWidgets.QVBoxLayout(shadow_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        # Заголовок
        title_label = QtWidgets.QLabel("ЕГОР!")
        title_label.setFont(QtGui.QFont("Montserrat", 32, QtGui.QFont.Bold))
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)

        # Сообщение
        messages = [
            "Давай сделаем перерыв!\nТвои глазки устали 👀",
            "Время отдохнуть!\nПобегай немного 🏃",
            "Пора размяться!\nПоиграем в игрушки или порисуй? 🎯",
            "Перерыв!\nПора подвигаться 🌟"
        ]
        msg = message if message else random.choice(messages)
        self.message_label = QtWidgets.QLabel(msg)
        self.message_label.setFont(QtGui.QFont("Montserrat", 18))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(QtCore.Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #f5f6fa;")
        layout.addWidget(self.message_label)

        # Кнопка закрытия
        close_btn = QtWidgets.QPushButton("Закрыть")
        close_btn.setFont(QtGui.QFont("Montserrat", 14))
        close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #357ABD;
                color: white;
                border-radius: 12px;
                padding: 10px 36px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #285a8c;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)

        # Основной layout окна
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(shadow_widget)
        self.setLayout(outer_layout)
        self.resize(500, 250)
        self.setModal(True)

        # Размещение в правом нижнем углу
        self._move_to_bottom_right()
        # Анимация появления
        self._animate_show()

    def _move_to_bottom_right(self):
        screen_geo = QtWidgets.QApplication.desktop().availableGeometry()
        self.move(screen_geo.width() - self.width() - 20, screen_geo.height() - self.height() - 20)

    def _animate_show(self):
        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def closeEvent(self, event):
        if self.on_close_callback:
            self.on_close_callback()
        super().closeEvent(event)

    def show(self, duration=15):
        """Показать уведомление"""
        super().show()
        winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
        if duration > 0:
            QtCore.QTimer.singleShot(duration * 1000, self.accept)

    def update_message(self, message: str):
        """
        Обновляет текст сообщения
        
        Args:
            message: Новый текст сообщения
        """
        self.message_label.setText(message)
            
    def update_theme(self, is_dark: bool = False):
        """
        Обновляет тему окна
        
        Args:
            is_dark: True для темной темы, False для светлой
        """
        # Эта функция больше не нужна, так как стили задаются через QSS
        # Но оставим ее для совместимости, если будет вызываться
        self.logger.info(f"Theme update called with is_dark={is_dark}. No visual change will occur.")
