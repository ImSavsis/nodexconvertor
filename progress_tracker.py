# импорты тут у нас
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QScrollArea, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QColor


# виджет отслеживания прогресса конвертации
class ProgressTracker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("progressTracker")
        self._total = 0
        self._current = 0
        self._build_ui()

    # def строим виджет прогресса
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QLabel("прогресс")
        header.setObjectName("sectionLabel")
        layout.addWidget(header)

        # прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("mainProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        # строка с числом файлов
        count_row = QHBoxLayout()
        self.count_label = QLabel("0 / 0")
        self.count_label.setObjectName("countLabel")
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("percentLabel")
        count_row.addWidget(self.count_label)
        count_row.addStretch()
        count_row.addWidget(self.percent_label)
        layout.addLayout(count_row)

        # статус сообщение
        self.status_label = QLabel("ожидание")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # лог завершённых файлов
        log_label = QLabel("обработанные файлы")
        log_label.setObjectName("fieldLabel")
        layout.addWidget(log_label)

        self.log_list = QListWidget()
        self.log_list.setObjectName("logList")
        layout.addWidget(self.log_list)

    # def обновляем прогресс из сигнала ядра
    def update_progress(self, current: int, total: int):
        self._current = current
        self._total = total

        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(pct)
            self.count_label.setText(f"{current} / {total}")
            self.percent_label.setText(f"{pct}%")

            # добавляем в лог
            item = QListWidgetItem(f"✓  файл {current}")
            item.setForeground(QColor("#4ade80"))
            self.log_list.addItem(item)
            self.log_list.scrollToBottom()

    # def реагируем на завершение конвертации
    def on_done(self, success: bool, message: str):
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(message)
            self.status_label.setProperty("done", True)
        else:
            self.status_label.setText(message)
            self.status_label.setProperty("error", True)

        self.style().unpolish(self.status_label)
        self.style().polish(self.status_label)

    # def сбрасываем всё в начальное состояние
    def reset(self):
        self._current = 0
        self._total = 0
        self.progress_bar.setValue(0)
        self.count_label.setText("0 / 0")
        self.percent_label.setText("0%")
        self.status_label.setText("ожидание")
        self.log_list.clear()
