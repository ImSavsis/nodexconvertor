# импорты тут у нас
from PySide6.QtWidgets import QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QRect, Property
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QLinearGradient,
    QRadialGradient, QMouseEvent
)


# кнопка с анимацией ripple эффекта при клике — как в material design
class RippleButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)

        # параметры ripple
        self._ripple_pos = QPoint(0, 0)
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self._ripple_active = False

        # анимация расширения круга
        self._radius_anim = QPropertyAnimation(self, b"ripple_radius")
        self._radius_anim.setDuration(400)
        self._radius_anim.setEasingCurve(QEasingCurve.OutQuad)

        # анимация угасания прозрачности
        self._opacity_anim = QPropertyAnimation(self, b"ripple_opacity")
        self._opacity_anim.setDuration(400)
        self._opacity_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._opacity_anim.finished.connect(self._on_ripple_done)

        # анимация масштаба кнопки при нажатии
        self._scale = 1.0
        self._scale_anim = QPropertyAnimation(self, b"button_scale")
        self._scale_anim.setDuration(120)
        self._scale_anim.setEasingCurve(QEasingCurve.OutBack)

    # def свойство для анимации ripple radius
    def get_ripple_radius(self):
        return self._ripple_radius

    def set_ripple_radius(self, val):
        self._ripple_radius = val
        self.update()

    ripple_radius = Property(float, get_ripple_radius, set_ripple_radius)

    # def свойство для анимации прозрачности ripple
    def get_ripple_opacity(self):
        return self._ripple_opacity

    def set_ripple_opacity(self, val):
        self._ripple_opacity = val
        self.update()

    ripple_opacity = Property(float, get_ripple_opacity, set_ripple_opacity)

    # def свойство масштаба кнопки
    def get_button_scale(self):
        return self._scale

    def set_button_scale(self, val):
        self._scale = val
        self.update()

    button_scale = Property(float, get_button_scale, set_button_scale)

    # def запускаем ripple при клике
    def mousePressEvent(self, event: QMouseEvent):
        self._ripple_pos = event.position().toPoint()
        max_dist = max(
            self._ripple_pos.x(), self.width() - self._ripple_pos.x(),
            self._ripple_pos.y(), self.height() - self._ripple_pos.y()
        )

        self._ripple_active = True
        self._ripple_radius = 0
        self._ripple_opacity = 0.3

        self._radius_anim.setStartValue(0.0)
        self._radius_anim.setEndValue(float(max_dist * 1.5))
        self._radius_anim.start()

        self._opacity_anim.setStartValue(0.3)
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.start()

        # лёгкое вжатие кнопки
        self._scale_anim.setStartValue(1.0)
        self._scale_anim.setEndValue(0.97)
        self._scale_anim.finished.connect(self._bounce_back)
        self._scale_anim.start()

        super().mousePressEvent(event)

    # def отскок обратно после нажатия
    def _bounce_back(self):
        self._scale_anim.finished.disconnect()
        self._scale_anim.setStartValue(0.97)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()

    # def ripple закончил анимацию
    def _on_ripple_done(self):
        self._ripple_active = False
        self.update()

    # def рисуем ripple поверх стандартной отрисовки
    def paintEvent(self, event):
        super().paintEvent(event)

        if not self._ripple_active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRect(self.rect())

        color = QColor(255, 255, 255, int(self._ripple_opacity * 255))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            self._ripple_pos,
            int(self._ripple_radius),
            int(self._ripple_radius)
        )
        painter.end()


# def фабрика — создаём кнопку с ripple и нужным object name
def make_ripple_button(text: str, object_name: str, parent=None) -> RippleButton:
    btn = RippleButton(text, parent)
    btn.setObjectName(object_name)
    return btn
