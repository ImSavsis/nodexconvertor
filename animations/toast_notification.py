# импорты тут у нас
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QPoint, QSize
)
from PySide6.QtGui import QPainter, QColor, QPainterPath, QFont


# типы уведомлений
NOTIFY_SUCCESS = "success"
NOTIFY_ERROR   = "error"
NOTIFY_INFO    = "info"
NOTIFY_WARNING = "warning"


# def получаем цвет по типу
def _color_for_type(kind: str) -> tuple:
    palette = {
        NOTIFY_SUCCESS: ("#4ade80", "#166534"),
        NOTIFY_ERROR:   ("#f87171", "#7f1d1d"),
        NOTIFY_INFO:    ("#5b5bf6", "#1e1b4b"),
        NOTIFY_WARNING: ("#fbbf24", "#78350f"),
    }
    return palette.get(kind, palette[NOTIFY_INFO])


# всплывающее уведомление — появляется снизу и уходит через 3 сек
class ToastNotification(QWidget):
    def __init__(self, message: str, kind: str = NOTIFY_INFO, parent=None):
        super().__init__(parent)
        self._kind = kind
        self._message = message
        self._opacity = 0.0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._build_ui()
        self._setup_animation()

    # def строим виджет уведомления
    def _build_ui(self):
        self.setFixedSize(QSize(360, 52))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        fg_color, _ = _color_for_type(self._kind)

        # иконка по типу
        icons = {
            NOTIFY_SUCCESS: "✓",
            NOTIFY_ERROR:   "✗",
            NOTIFY_INFO:    "·",
            NOTIFY_WARNING: "!",
        }
        icon_label = QLabel(icons.get(self._kind, "·"))
        icon_label.setStyleSheet(f"color: {fg_color}; font-size: 16px; font-weight: bold;")
        icon_label.setFixedWidth(20)

        msg_label = QLabel(self._message)
        msg_label.setStyleSheet(f"color: #f0f0fa; font-size: 12px; font-family: 'JetBrains Mono', monospace;")
        msg_label.setWordWrap(False)

        layout.addWidget(icon_label)
        layout.addWidget(msg_label, 1)

    # def настраиваем анимацию появления и исчезновения
    def _setup_animation(self):
        # появление
        self.show_anim = QPropertyAnimation(self, b"pos")
        self.show_anim.setDuration(300)
        self.show_anim.setEasingCurve(QEasingCurve.OutCubic)

        # автоисчезновение через 3 секунды
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(3000)
        self._hide_timer.timeout.connect(self._start_hide)

        # скрытие
        self.hide_anim = QPropertyAnimation(self, b"pos")
        self.hide_anim.setDuration(250)
        self.hide_anim.setEasingCurve(QEasingCurve.InCubic)
        self.hide_anim.finished.connect(self.close)

    # def показываем уведомление в правом нижнем углу родителя
    def show_toast(self, parent_widget=None):
        if parent_widget:
            parent_rect = parent_widget.rect()
            parent_pos = parent_widget.mapToGlobal(QPoint(0, 0))
            start_x = parent_pos.x() + parent_rect.width() - self.width() - 20
            end_y = parent_pos.y() + parent_rect.height() - self.height() - 20
            start_y = end_y + 30  # стартуем ниже
        else:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().availableGeometry()
            start_x = screen.right() - self.width() - 20
            end_y = screen.bottom() - self.height() - 20
            start_y = end_y + 30

        self.move(start_x, start_y)
        self.show()

        self.show_anim.setStartValue(QPoint(start_x, start_y))
        self.show_anim.setEndValue(QPoint(start_x, end_y))
        self.show_anim.start()

        self._hide_timer.start()

    # def начинаем анимацию скрытия
    def _start_hide(self):
        start = self.pos()
        end = QPoint(start.x(), start.y() + 20)
        self.hide_anim.setStartValue(start)
        self.hide_anim.setEndValue(end)
        self.hide_anim.start()

    # def рисуем фон уведомления
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        fg_color, bg_color = _color_for_type(self._kind)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        # тёмный фон
        painter.fillPath(path, QColor("#18181f"))

        # левая полоска цвета типа
        accent_path = QPainterPath()
        accent_path.addRoundedRect(0, 8, 3, self.height() - 16, 2, 2)
        painter.fillPath(accent_path, QColor(fg_color))

        # тонкая рамка
        painter.setPen(QColor("#2a2a38"))
        painter.drawPath(path)

        painter.end()


# def удобная фабрика — создаём и сразу показываем
def show_toast(message: str, kind: str = NOTIFY_INFO, parent=None):
    toast = ToastNotification(message, kind, parent)
    toast.show_toast(parent)
    return toast
