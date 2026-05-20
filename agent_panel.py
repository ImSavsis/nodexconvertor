# импорты тут у нас — панель AI агента
# он отвечает на вопросы и умеет конвертить файлы сам
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QTextCursor

from animations.ripple_button import make_ripple_button
from animations.toast_notification import show_toast


# воркер для запроса к AI — в потоке чтобы не фризить UI
class AgentWorker(QObject):
    done = Signal(str, bool)  # (ответ, это_ошибка)

    def __init__(self, message: str, file_context: list[str] | None = None):
        super().__init__()
        self.message      = message
        self.file_context = file_context or []

    def run(self):
        try:
            from agent import ask_once
            # если есть файлы — добавляем их в контекст
            prompt = self.message
            if self.file_context:
                files_info = "\n".join(
                    f"- {Path(f).name} ({Path(f).suffix})" for f in self.file_context
                )
                prompt = f"{self.message}\n\nЗагруженные файлы:\n{files_info}"
            result = ask_once(prompt)
            self.done.emit(result, False)
        except Exception as e:
            self.done.emit(str(e), True)


# панель AI агента — чат с агентом который умеет конвертировать файлы
class AgentPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._current_files: list[str] = []  # файлы из дроп зоны для контекста
        self._build_ui()

    # def строим UI
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # заголовок
        header = QLabel("ai агент")
        header.setObjectName("sectionLabel")
        layout.addWidget(header)

        # подсказки что можно спрашивать
        hint = QLabel(
            "можно попросить конвертировать файлы, объяснить что делать или просто поговорить"
        )
        hint.setObjectName("fieldLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # история чата
        self.chat_history = QTextEdit()
        self.chat_history.setObjectName("chatHistory")
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText(
            "примеры запросов:\n\n"
            "• конвертируй загруженный файл в pdf\n"
            "• какие форматы поддерживает конвертер?\n"
            "• как собрать питон скрипт в exe?\n"
            "• объясни чем отличается flac от mp3"
        )
        layout.addWidget(self.chat_history, 1)

        # поле ввода и кнопка отправки
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("formatCombo")  # берём стиль от комбо
        self.input_field.setPlaceholderText("напиши что нужно...")
        self.input_field.setMinimumHeight(40)
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = make_ripple_button("отправить", "primaryBtn")
        self.send_btn.setMinimumHeight(40)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_frame)

        # кнопка очистки истории
        btn_clear = make_ripple_button("очистить чат", "secondaryBtn")
        btn_clear.clicked.connect(self._clear_chat)
        layout.addWidget(btn_clear)

    # def получаем файлы из дроп зоны — сохраняем для контекста AI
    def load_files(self, paths: list[str]):
        self._current_files = paths
        if paths:
            names = ", ".join(Path(p).name for p in paths[:3])
            if len(paths) > 3:
                names += f" и ещё {len(paths) - 3}"
            self._add_message("система", f"загружены файлы: {names}", "#55556a")

    # def отправляем сообщение AI
    def _send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.send_btn.setEnabled(False)

        # показываем сообщение пользователя
        self._add_message("ты", text, "#8888ff")
        self._add_message("агент", "думает...", "#55556a")

        # запускаем в потоке
        self._thread = QThread()
        self._worker = AgentWorker(
            message      = text,
            file_context = self._current_files,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_response)
        self._worker.done.connect(self._thread.quit)
        self._thread.start()

    # def получили ответ от AI
    def _on_response(self, text: str, is_error: bool):
        self.send_btn.setEnabled(True)

        # убираем "думает..."
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # убираем \n от блока

        # добавляем настоящий ответ
        color = "#f87171" if is_error else "#f0f0fa"
        self._add_message("агент", text, color)

        if is_error:
            show_toast("ошибка AI", "error", self)

    # def добавляем сообщение в историю
    def _add_message(self, sender: str, text: str, color: str):
        # форматируем красиво
        escaped = text.replace("<", "&lt;").replace(">", "&gt;")
        html = (
            f'<div style="margin-bottom:12px">'
            f'<span style="color:{color};font-weight:600;font-size:11px;'
            f'letter-spacing:1px;text-transform:uppercase">{sender}</span>'
            f'<br>'
            f'<span style="color:#c0c0d0;font-size:13px;line-height:1.6">{escaped}</span>'
            f'</div>'
        )
        self.chat_history.append(html)
        # прокручиваем вниз
        sb = self.chat_history.verticalScrollBar()
        sb.setValue(sb.maximum())

    # def очищаем историю чата
    def _clear_chat(self):
        self.chat_history.clear()
        self._current_files = []
