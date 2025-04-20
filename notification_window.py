from PyQt5 import QtWidgets, QtCore
from win32api import GetSystemMetrics
import winsound
import time
import random
from logger import Logger
import os

from PyQt5 import QtWidgets, QtCore, QtGui
import random
import os
from logger import Logger

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
        message_label = QtWidgets.QLabel(msg)
        message_label.setFont(QtGui.QFont("Montserrat", 18))
        message_label.setWordWrap(True)
        message_label.setAlignment(QtCore.Qt.AlignCenter)
        message_label.setStyleSheet("color: #f5f6fa;")
        layout.addWidget(message_label)

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
        screen = QtWidgets.QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        x = geometry.right() - self.width() - 40
        y = geometry.bottom() - self.height() - 40
        self.move(x, y)

    def _animate_show(self):
        self.setWindowOpacity(0)
        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def closeEvent(self, event):
        self.logger.info("Notification closed")
        if self.on_close_callback:
            self.on_close_callback()
        event.accept()

        messages = [
            "Давай сделаем перерыв!\nТвои глазки устали 👀",
            "Время отдохнуть!\nПобегай немного 🏃",
            "Пора размяться!\nПоиграем в игрушки или порисуй? 🎯",
            "Перерыв!\nПора подвигаться 🌟"
        ]
        
        self.message_label = tk.Label(
            self.content_frame,
            text=random.choice(messages),
            font=("Montserrat", 18),
            wraplength=400,
            bg=self.bg_color,
            fg=self.text_color,
            justify=tk.CENTER
        )
        self.message_label.grid(row=1, column=0, pady=(0, 30), sticky="nsew")
        
        # Настраиваем веса для центрирования
        self.content_frame.grid_columnconfigure(0, weight=1)

    def _create_close_button(self):
        """Создание кнопки закрытия"""
        self.close_button = tk.Button(
            self.content_frame,
            text="Хорошо!",
            font=("Montserrat", 14, "bold"),
            command=self.close,
            bg='white',
            fg=self.bg_color,
            relief="flat",
            width=15,
            cursor="hand2"
        )
        self.close_button.grid(row=2, column=0, pady=10, sticky="nsew")
        
        # Настраиваем веса для центрирования
        self.content_frame.grid_columnconfigure(0, weight=1)

    def show(self, duration=15):
        """Показать уведомление"""
        try:
            # Если уже есть активный таймер - отменяем его
            if hasattr(self, 'auto_close_id'):
                self.popup.after_cancel(self.auto_close_id)
                del self.auto_close_id
            
            # Получаем размеры экрана
            screen_width = GetSystemMetrics(0)
            screen_height = GetSystemMetrics(1)
            
            # Размеры окна
            window_width = 450
            window_height = 350
            
            # Позиция в правом нижнем углу с отступом
            x = screen_width - window_width - 20
            y = screen_height - window_height - 40
            
            # Устанавливаем позицию
            self.popup.geometry(f"{window_width}x{window_height}+{x}+{y}")
            self.popup.attributes('-topmost', True)
            
            # Показываем окно
            self.popup.deiconify()
            
            # Воспроизводим звук
            winsound.PlaySound("SystemExclamation", winsound.SND_ASYNC)
            
            # Автозакрытие через duration секунд
            self.auto_close_id = self.popup.after(duration * 1000, self.close)
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {str(e)}")
            raise

    def hide(self):
        """Скрыть окно"""
        self.close()

    def update_message(self, message: str):
        """
        Обновляет текст сообщения
        
        Args:
            message: Новый текст сообщения
        """
        self.message = message
        if hasattr(self, 'message_label'):
            self.message_label.config(text=message)
            
    def update_theme(self, is_dark: bool = False):
        """
        Обновляет тему окна
        
        Args:
            is_dark: True для темной темы, False для светлой
        """
        if is_dark:
            self.bg_color = '#2D2D2D'
            self.text_color = '#E0E0E0'
        else:
            self.bg_color = '#4A90E2'
            self.text_color = 'white'
            
        if hasattr(self, 'popup'):
            self.popup.configure(bg=self.bg_color)
            self.content_frame.configure(bg=self.bg_color)
            self.title_label.configure(bg=self.bg_color, fg=self.text_color)
            self.message_label.configure(bg=self.bg_color, fg=self.text_color)
            self.close_button.configure(bg='white', fg=self.bg_color)
