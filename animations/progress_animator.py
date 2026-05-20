# импорты тут у нас
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    Property, Signal, QPoint
)
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush


# анимированный прогресс бар 
class AnimatedProgressBar(QWidget):
    value_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.setMinimumWidth(100)

        self._value = 0           # текущее отображаемое значение 0-100
        self._target = 0          # целевое значение
        self._glow_offset = 0.0   # смещение анимации свечения
        self._is_complete = False

        # таймер для плавного движения и эффекта свечения
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(16)   # ~60fps
        self._render_timer.timeout.connect(self._tick)
        self._render_timer.start()

        # таймер для анимации полосок shimmer
        self._shimmer_pos = 0.0

    # def каждый кадр — обновляем состояние
    def _tick(self):
        # плавно догоняем целевое значение
        diff = self._target - self._value
        if abs(diff) > 0.2:
            self._value += diff * 0.08
        else:
            self._value = float(self._target)

        # крутим shimmer
        self._shimmer_pos = (self._shimmer_pos + 0.012) % 1.0

        self.update()

    # def внешний метод установки значения
    def set_value(self, value: int):
        self._target = max(0, min(100, value))
        if self._target >= 100:
            self._is_complete = True
        self.value_changed.emit(self._target)

    # def сброс в 0
    def reset(self):
        self._value = 0
        self._target = 0
        self._is_complete = False
        self.update()

    # def рисуем бар вручную
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h // 2

        # фон трека
        painter.setBrush(QColor("#1e1e28"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        if self._value <= 0:
            return

        fill_w = int((self._value / 100.0) * w)
        fill_w = max(fill_w, h)  # минимум круглый конец

        # основной градиент заполнения
        if self._is_complete:
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0, QColor("#4ade80"))
            grad.setColorAt(1, QColor("#22c55e"))
        else:
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0, QColor("#3b3bf5"))
            grad.setColorAt(0.6, QColor("#5b5bf6"))
            grad.setColorAt(1, QColor("#7c7cf8"))

        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(0, 0, fill_w, h, radius, radius)

        # shimmer эффект поверх заполнения
        if not self._is_complete and fill_w > 10:
            shimmer_x = int(self._shimmer_pos * (fill_w + 40)) - 20
            shimmer_grad = QLinearGradient(shimmer_x - 20, 0, shimmer_x + 20, 0)
            shimmer_grad.setColorAt(0, QColor(255, 255, 255, 0))
            shimmer_grad.setColorAt(0.5, QColor(255, 255, 255, 35))
            shimmer_grad.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(QBrush(shimmer_grad))
            # обрезаем shimmer по границе заполнения
            painter.setClipRect(0, 0, fill_w, h)
            painter.drawRoundedRect(0, 0, fill_w, h, radius, radius)
            painter.setClipping(False)

        # свечение на правом конце бара
        if not self._is_complete and fill_w > h:
            glow_color = QColor(91, 91, 246, 80)
            glow_grad = QLinearGradient(fill_w - 20, 0, fill_w + 2, 0)
            glow_grad.setColorAt(0, QColor(91, 91, 246, 0))
            glow_grad.setColorAt(1, glow_color)
            painter.setBrush(QBrush(glow_grad))
            painter.drawRoundedRect(fill_w - 20, 0, 22, h, radius, radius)

        painter.end()
