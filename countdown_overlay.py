from PyQt5 import QtWidgets, QtCore, QtGui

class CountdownOverlay(QtWidgets.QWidget):
    """
    Полупрозрачный оверлей с крупным обратным отсчетом.
    Не перехватывает клики (сквозной), всегда поверх всех окон.
    """
    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Без рамки, поверх всех окон, прозрачный фон, не фокусируемый
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool  # не отображать в таскбаре
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Прозрачен для ввода (клики проходят сквозь)
        if hasattr(QtCore.Qt, 'WindowTransparentForInput'):
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            self.setWindowFlag(QtCore.Qt.WindowTransparentForInput, True)
        else:
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        self._seconds_left = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        # Контент: большой текст с тенью
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.label = QtWidgets.QLabel("")
        font = QtGui.QFont("Montserrat", 72, QtGui.QFont.Black)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("color: white;")

        # Тень под текст
        effect = QtWidgets.QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(24)
        effect.setColor(QtGui.QColor(0, 0, 0, 200))
        effect.setOffset(2, 6)
        self.label.setGraphicsEffect(effect)
        layout.addWidget(self.label)

        # На весь экран (на активном дисплее)
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.availableGeometry())

    def start(self, seconds: int):
        self._seconds_left = max(0, int(seconds or 0))
        self._update_text()
        self.show()
        if self._seconds_left > 0:
            self._timer.start(1000)
        else:
            self._finish()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()
        self.hide()
        self.closed.emit()

    def _on_tick(self):
        if self._seconds_left > 0:
            self._seconds_left -= 1
            self._update_text()
        if self._seconds_left <= 0:
            self._finish()

    def _finish(self):
        if self._timer.isActive():
            self._timer.stop()
        self.hide()
        self.closed.emit()

    def _update_text(self):
        if self._seconds_left > 0:
            self.label.setText(f"{self._seconds_left}")
        else:
            self.label.setText("")
