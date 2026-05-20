# импорты тут у нас — панель сборки Python в exe
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QCheckBox,
    QLineEdit, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QColor

# моя кнопка с ripple — берём из анимаций
from animations.ripple_button import make_ripple_button
from animations.toast_notification import show_toast, NOTIFY_SUCCESS, NOTIFY_ERROR


# воркер для сборки — запускается в потоке чтобы UI не завис
class BuildWorker(QObject):
    log_line  = Signal(str)  # строка лога для вывода
    finished  = Signal(bool, str)  # (успех, результат)

    def __init__(self, py_file: str, one_file: bool, console: bool,
                 auto_deps: bool, name: str | None, output_dir: str | None):
        super().__init__()
        self.py_file    = py_file
        self.one_file   = one_file
        self.console    = console
        self.auto_deps  = auto_deps
        self.name       = name
        self.output_dir = output_dir

    def run(self):
        # перехватываем print чтобы передавать в UI
        import io, sys, contextlib
        buf = io.StringIO()

        # функция-принт которая шлёт сигнал
        original_print = print

        def ui_print(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            self.log_line.emit(text)
            original_print(*args, **kwargs)

        import builtins
        builtins.print = ui_print

        try:
            from builder import build_exe
            result = build_exe(
                py_file    = self.py_file,
                output_dir = self.output_dir,
                one_file   = self.one_file,
                console    = self.console,
                auto_deps  = self.auto_deps,
                name       = self.name,
                verbose    = True,
            )
            self.finished.emit(True, str(result))
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            builtins.print = original_print  # возвращаем нормальный print


# панель управления сборкой — правая колонка в табе "Сборка EXE"
class BuilderPanel(QWidget):
    build_started  = Signal()
    build_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loaded_files: list[str] = []  # список загруженных py файлов
        self._thread  = None
        self._worker  = None
        self._build_ui()

    # def строим UI панели
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # заголовок секции
        header = QLabel("сборка python → exe")
        header.setObjectName("sectionLabel")
        layout.addWidget(header)

        # список загруженных .py файлов
        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")
        self.file_list.setMaximumHeight(140)
        self.file_list.setToolTip("перетащи .py файлы в зону слева")
        layout.addWidget(self.file_list)

        # кнопка очистки списка
        clear_row = QHBoxLayout()
        btn_clear = make_ripple_button("очистить список", "secondaryBtn")
        btn_clear.clicked.connect(self._clear_files)
        clear_row.addWidget(btn_clear)
        clear_row.addStretch()
        layout.addLayout(clear_row)

        # опции сборки — три чекбокса
        opts_label = QLabel("параметры:")
        opts_label.setObjectName("fieldLabel")
        layout.addWidget(opts_label)

        opts_row = QHBoxLayout()
        self.chk_onefile  = QCheckBox("один файл")
        self.chk_onefile.setChecked(True)
        self.chk_onefile.setToolTip("--onefile: упаковать всё в один бинарник")

        self.chk_console  = QCheckBox("консоль")
        self.chk_console.setChecked(True)
        self.chk_console.setToolTip("--noconsole убирает консольное окно (для GUI приложений)")

        self.chk_autodeps = QCheckBox("авто-зависимости")
        self.chk_autodeps.setChecked(True)
        self.chk_autodeps.setToolTip("сканировать импорты и устанавливать перед сборкой")

        opts_row.addWidget(self.chk_onefile)
        opts_row.addWidget(self.chk_console)
        opts_row.addWidget(self.chk_autodeps)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        # имя выходного файла (необязательно)
        name_row = QHBoxLayout()
        name_lbl = QLabel("имя файла:")
        name_lbl.setObjectName("fieldLabel")
        self.name_input = QLineEdit()
        self.name_input.setObjectName("formatCombo")  # берём стиль от комбо
        self.name_input.setPlaceholderText("my_app  (по умолчанию — имя скрипта)")
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.name_input, 1)
        layout.addLayout(name_row)

        layout.addStretch()

        # главная кнопка сборки
        self.build_btn = make_ripple_button("собрать", "primaryBtn")
        self.build_btn.setMinimumHeight(44)
        self.build_btn.clicked.connect(self._start_build)
        self.build_btn.setEnabled(False)
        layout.addWidget(self.build_btn)

        # кнопка отмены (скрыта пока не идёт сборка)
        self.cancel_btn = make_ripple_button("отменить", "dangerBtn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_build)
        layout.addWidget(self.cancel_btn)

        # лог сборки
        log_label = QLabel("лог сборки")
        log_label.setObjectName("sectionLabel")
        layout.addWidget(log_label)

        self.log = QTextEdit()
        self.log.setObjectName("buildLog")
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("тут будет прогресс сборки...")
        layout.addWidget(self.log, 1)

    # def получаем файлы из дроп зоны — берём только .py
    def load_files(self, paths: list[str]):
        py_files = [p for p in paths if p.lower().endswith(".py")]
        if not py_files:
            return  # не питон — не наше дело
        new = [p for p in py_files if p not in self.loaded_files]
        self.loaded_files.extend(new)
        for path in new:
            item = QListWidgetItem(f"🐍  {Path(path).name}")
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.file_list.addItem(item)
        self._check_ready()

    # def очищаем список
    def _clear_files(self):
        self.loaded_files.clear()
        self.file_list.clear()
        self._check_ready()

    # def проверяем готовность — нужен хотя бы один файл
    def _check_ready(self):
        self.build_btn.setEnabled(len(self.loaded_files) > 0)

    # def запускаем сборку
    def _start_build(self):
        if not self.loaded_files:
            return

        # берём первый файл (или выбранный в списке)
        selected = self.file_list.currentItem()
        if selected:
            py_file = selected.data(Qt.UserRole)
        else:
            py_file = self.loaded_files[0]

        name = self.name_input.text().strip() or None

        # чистим лог и блокируем кнопку
        self.log.clear()
        self._append_log(f"собираю: {Path(py_file).name}")
        self.build_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.build_started.emit()

        # создаём и запускаем воркер в потоке
        self._thread = QThread()
        self._worker = BuildWorker(
            py_file    = py_file,
            one_file   = self.chk_onefile.isChecked(),
            console    = self.chk_console.isChecked(),
            auto_deps  = self.chk_autodeps.isChecked(),
            name       = name,
            output_dir = str(Path(py_file).parent / "dist"),
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._on_done)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    # def сборка завершена
    def _on_done(self, success: bool, result: str):
        self.build_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.build_finished.emit()

        if success:
            self._append_log(f"✓ готово: {result}", color="#4ade80")
            show_toast(f"собрано: {Path(result).name}", "success", self)
        else:
            self._append_log(f"✗ ошибка: {result}", color="#f87171")
            show_toast("ошибка сборки", "error", self)

    # def отмена — просто убиваем поток (немного грубовато но работает)
    def _cancel_build(self):
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait()
        self.build_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self._append_log("отменено")
        self.build_finished.emit()

    # def добавляем строку в лог с цветом
    def _append_log(self, text: str, color: str = "#8888aa"):
        self.log.append(f'<span style="color:{color};font-family:monospace">{text}</span>')
        # прокручиваем вниз
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())
