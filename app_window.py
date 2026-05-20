# импорты тут у нас
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QDesktopServices

# свои модули
from converter_core import ConverterCore
from drop_zone import DropZone
from conversion_panel import ConversionPanel
from progress_tracker import ProgressTracker
from builder_panel import BuilderPanel  # новое — сборка exe
from agent_panel import AgentPanel       # новое — AI агент


# главное окно — собирает всё приложение воедино
class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NodexConvertor")
        self.setMinimumSize(QSize(1000, 660))
        self.resize(1200, 760)

        # ядро конвертации — оригинальное + мои форматы внутри
        self.core = ConverterCore()

        self._build_ui()
        self._connect_signals()

    # def собираем весь интерфейс
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # шапка с заголовком
        header = self._make_header()
        root_layout.addWidget(header)

        # основная область
        body = QHBoxLayout()
        body.setContentsMargins(20, 20, 20, 20)
        body.setSpacing(16)

        # левая колонка — дроп зона (неизменна)
        self.drop_zone = DropZone()
        body.addWidget(self.drop_zone, 2)

        # правая колонка — теперь это таб виджет с тремя секциями
        self.right_tabs = QTabWidget()
        self.right_tabs.setObjectName("rightTabs")

        # вкладка 1: конвертация (оригинальная панель)
        conv_container = QWidget()
        conv_layout    = QVBoxLayout(conv_container)
        conv_layout.setContentsMargins(0, 8, 0, 0)
        conv_layout.setSpacing(12)

        self.conversion_panel = ConversionPanel(self.core)
        conv_layout.addWidget(self.conversion_panel, 3)

        self.progress_tracker = ProgressTracker()
        conv_layout.addWidget(self.progress_tracker, 2)

        self.right_tabs.addTab(conv_container, "⚡  конвертация")

        # вкладка 2: сборка в exe
        self.builder_panel = BuilderPanel()
        self.right_tabs.addTab(self.builder_panel, "🔨  сборка exe")

        # вкладка 3: AI агент
        self.agent_panel = AgentPanel()
        self.right_tabs.addTab(self.agent_panel, "🤖  ai агент")

        body.addWidget(self.right_tabs, 3)
        root_layout.addLayout(body)

        # статус бар внизу
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("готов к конвертации")
        self.setStatusBar(self.status_bar)

    # def шапка с брендингом и ссылкой на гитхаб
    def _make_header(self):
        header = QFrame()
        header.setObjectName("appHeader")
        header.setFixedHeight(56)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("NodexConvertor")
        title.setObjectName("appTitle")

        subtitle = QLabel("universal file converter · exe builder · ai agent")
        subtitle.setObjectName("appSubtitle")

        github_btn = QPushButton("github.com/ImSavsis")
        github_btn.setObjectName("githubLink")
        github_btn.setCursor(Qt.PointingHandCursor)
        github_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/ImSavsis"))
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(github_btn)

        return header

    # def подключаем сигналы между компонентами
    def _connect_signals(self):
        # файлы из дроп зоны — роутим в нужную панель в зависимости от активной вкладки
        self.drop_zone.files_dropped.connect(self._on_files_dropped)

        # прогресс и статус из ядра конвертации
        self.core.progress_updated.connect(self.progress_tracker.update_progress)
        self.core.conversion_done.connect(self.progress_tracker.on_done)
        self.core.status_message.connect(self.status_bar.showMessage)

        # блокируем дроп зону во время конвертации
        self.conversion_panel.conversion_started.connect(
            lambda: self.drop_zone.setEnabled(False)
        )
        self.conversion_panel.conversion_finished.connect(
            lambda: self.drop_zone.setEnabled(True)
        )

        # блокируем зону во время сборки
        self.builder_panel.build_started.connect(
            lambda: self.drop_zone.setEnabled(False)
        )
        self.builder_panel.build_finished.connect(
            lambda: self.drop_zone.setEnabled(True)
        )

        # статус из билдера
        self.builder_panel.build_started.connect(
            lambda: self.status_bar.showMessage("идёт сборка...")
        )
        self.builder_panel.build_finished.connect(
            lambda: self.status_bar.showMessage("сборка завершена")
        )

    # def файлы дропнули — смотрим какая вкладка активна и передаём туда
    def _on_files_dropped(self, paths: list[str]):
        active = self.right_tabs.currentIndex()

        if active == 0:
            # вкладка конвертации — в conversion_panel
            self.conversion_panel.load_files(paths)
        elif active == 1:
            # вкладка сборки — в builder_panel (только .py)
            self.builder_panel.load_files(paths)
        elif active == 2:
            # вкладка AI — в agent_panel (для контекста)
            self.agent_panel.load_files(paths)

        # обновляем статус
        count = len(paths)
        self.status_bar.showMessage(
            f"загружено {count} файл{'ов' if count > 4 else 'а' if count > 1 else ''}"
        )
