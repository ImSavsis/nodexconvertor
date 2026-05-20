# импорты тут у нас
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QFileDialog, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread, QObject


# воркер — запускается в отдельном треде
class ConversionWorker(QObject):
    finished = Signal()

    def __init__(self, core, files, output_dir):
        super().__init__()
        self.core = core
        self.files = files
        self.output_dir = output_dir

    def run(self):
        self.core.convert_batch(self.files, self.output_dir)
        self.finished.emit()


# панель управления конвертацией — выбор формата и запуск
class ConversionPanel(QWidget):
    conversion_started = Signal()
    conversion_finished = Signal()

    def __init__(self, core, parent=None):
        super().__init__(parent)
        self.core = core
        self.loaded_files = []
        self.output_dir = ""
        self._thread = None

        self._build_ui()

    # def строим панель
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # заголовок секции
        section_label = QLabel("настройки конвертации")
        section_label.setObjectName("sectionLabel")
        layout.addWidget(section_label)

        # список загруженных файлов
        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")
        self.file_list.setMaximumHeight(180)
        self.file_list.itemClicked.connect(self._on_file_selected)
        layout.addWidget(self.file_list)

        # кнопки управления списком
        list_controls = QHBoxLayout()
        clear_btn = QPushButton("очистить список")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.clicked.connect(self._clear_files)
        list_controls.addWidget(clear_btn)
        list_controls.addStretch()
        layout.addLayout(list_controls)

        # выбор целевого формата
        format_row = QHBoxLayout()
        format_label = QLabel("конвертировать в:")
        format_label.setObjectName("fieldLabel")
        self.format_combo = QComboBox()
        self.format_combo.setObjectName("formatCombo")
        self.format_combo.setMinimumWidth(120)
        self.format_combo.addItem("-- выбери формат --")
        format_row.addWidget(format_label)
        format_row.addWidget(self.format_combo)
        format_row.addStretch()
        layout.addLayout(format_row)

        # выбор папки для сохранения
        output_row = QHBoxLayout()
        self.output_label = QLabel("папка: не выбрана")
        self.output_label.setObjectName("fieldLabel")
        output_btn = QPushButton("выбрать папку")
        output_btn.setObjectName("secondaryBtn")
        output_btn.clicked.connect(self._pick_output_dir)
        output_row.addWidget(self.output_label, 1)
        output_row.addWidget(output_btn)
        layout.addLayout(output_row)

        layout.addStretch()

        # главная кнопка запуска
        self.convert_btn = QPushButton("конвертировать")
        self.convert_btn.setObjectName("primaryBtn")
        self.convert_btn.setMinimumHeight(44)
        self.convert_btn.clicked.connect(self._start_conversion)
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)

        # кнопка отмены
        self.cancel_btn = QPushButton("отменить")
        self.cancel_btn.setObjectName("dangerBtn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_conversion)
        layout.addWidget(self.cancel_btn)

    # def загружаем файлы из дроп зоны
    def load_files(self, paths: list):
        new_paths = [p for p in paths if p not in self.loaded_files]
        self.loaded_files.extend(new_paths)

        for path in new_paths:
            name = Path(path).name
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.file_list.addItem(item)

        self._refresh_format_options()
        self._check_ready()

    # def при выборе файла в списке обновляем доступные форматы
    def _on_file_selected(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        targets = self.core.get_targets(path)
        self.format_combo.clear()
        self.format_combo.addItem("-- выбери формат --")
        for t in targets:
            self.format_combo.addItem(t)

    # def обновляем общий список форматов по всем файлам
    def _refresh_format_options(self):
        if not self.loaded_files:
            return
        # берём форматы первого файла как базу
        targets = self.core.get_targets(self.loaded_files[0])
        self.format_combo.clear()
        self.format_combo.addItem("-- выбери формат --")
        for t in targets:
            self.format_combo.addItem(t)

    # def выбираем папку для сохранения результата
    def _pick_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "выбери папку для сохранения")
        if folder:
            self.output_dir = folder
            short = Path(folder).name
            self.output_label.setText(f"папка: .../{short}")
            self._check_ready()

    # def очищаем список файлов
    def _clear_files(self):
        self.loaded_files.clear()
        self.file_list.clear()
        self.format_combo.clear()
        self.format_combo.addItem("-- выбери формат --")
        self._check_ready()

    # def проверяем готовность к конвертации
    def _check_ready(self):
        has_files = len(self.loaded_files) > 0
        has_dir = bool(self.output_dir)
        self.convert_btn.setEnabled(has_files and has_dir)

    # def запускаем конвертацию
    def _start_conversion(self):
        fmt = self.format_combo.currentText()
        if fmt.startswith("--"):
            return

        tasks = [{"path": p, "target_format": fmt} for p in self.loaded_files]

        self.convert_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.conversion_started.emit()

        self._thread = QThread()
        self._worker = ConversionWorker(self.core, tasks, self.output_dir)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_conversion_finished)
        self._worker.finished.connect(self._thread.quit)

        self._thread.start()

    # def конвертация завершена
    def _on_conversion_finished(self):
        self.convert_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.conversion_finished.emit()

    # def отменяем конвертацию
    def _cancel_conversion(self):
        self.core.cancel()
