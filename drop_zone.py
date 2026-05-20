# импорты тут у нас
import os
from pathlib import Path
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal, QMimeData, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent


# зона для дропа файлов — поддерживает drag and drop
class DropZone(QFrame):
    files_dropped = Signal(list)   # список путей к файлам

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(280, 400)

        self._is_hovering = False
        self._build_ui()

    # def строим внутренний лейаут зоны
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        # иконка дропа — большой текстовый символ
        self.icon_label = QLabel("⬇")
        self.icon_label.setObjectName("dropIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.main_label = QLabel("перетащи файлы сюда")
        self.main_label.setObjectName("dropMainLabel")
        self.main_label.setAlignment(Qt.AlignCenter)

        self.sub_label = QLabel(
            "audio  ·  image  ·  video  ·  document\n"
            "flac  mp3  wav  png  ico  jpg  webp  pdf  mp4  mkv  ..."
        )
        self.sub_label.setObjectName("dropSubLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setWordWrap(True)

        self.hint_label = QLabel("или нажми чтобы выбрать")
        self.hint_label.setObjectName("dropHintLabel")
        self.hint_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.main_label)
        layout.addWidget(self.sub_label)
        layout.addSpacing(8)
        layout.addWidget(self.hint_label)

    # def обрабатываем вход дрога — подсвечиваем зону
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_hover(True)

    # def убираем подсветку при выходе
    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self._set_hover(False)

    # def файлы брошены — собираем пути и эмитим сигнал
    def dropEvent(self, event: QDropEvent):
        self._set_hover(False)
        urls = event.mimeData().urls()
        paths = []

        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                paths.append(path)
            elif os.path.isdir(path):
                # если кинули папку — собираем все файлы из неё
                for root, _, files in os.walk(path):
                    for f in files:
                        paths.append(os.path.join(root, f))

        if paths:
            self.files_dropped.emit(paths)

        event.acceptProposedAction()

    # def клик по зоне — открываем диалог выбора файлов
    def mousePressEvent(self, event):
        from PySide6.QtWidgets import QFileDialog
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "выбери файлы для конвертации",
            "",
            "все файлы (*.*)"
        )
        if paths:
            self.files_dropped.emit(paths)

    # def переключаем визуальное состояние наведения
    def _set_hover(self, state: bool):
        if self._is_hovering == state:
            return
        self._is_hovering = state
        self.setProperty("hovering", state)
        # перезапускаем стиль чтобы сработал селектор
        self.style().unpolish(self)
        self.style().polish(self)
