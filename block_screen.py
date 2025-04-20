from PyQt5 import QtWidgets, QtCore, QtGui
import sys
from countdown_window import CountdownWindow
from settings_manager import SettingsManager

class BlockScreen(QtWidgets.QDialog):
    def __init__(self, settings, countdown_seconds=10, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Блокировка игры")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.setModal(True)
        self.setStyleSheet("background-color: black;")

        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(self.settings.get("block_screen_message", "Время игры истекло! Пожалуйста, сделайте перерыв."), self)
        label.setStyleSheet("color: white; font-size: 32px; padding: 40px;")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)

        # Запуск CountdownWindow перед показом блокировки
        self.countdown = CountdownWindow(countdown_seconds)
        self.countdown.exec_()
        # После отсчета показываем блокировку
        self.showFullScreen()

    def keyPressEvent(self, event):
        # Разблокировка по Ctrl+Alt+Q
        if event.key() == QtCore.Qt.Key_Q and \
           event.modifiers() & QtCore.Qt.ControlModifier and \
           event.modifiers() & QtCore.Qt.AltModifier:
            self.accept()  # Закроет окно блокировки
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        # Блокируем закрытие окна
        event.ignore()

    def close(self):
        """Закрывает окно блокировки"""
        try:
            self.destroy()
        except:
            pass
