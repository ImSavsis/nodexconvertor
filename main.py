# импорты тут у нас
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QFontDatabase, QIcon

from app_window import AppWindow
from theme_engine import ThemeEngine


# точка входа - запускаем всё отсюда
def main():
    # нужно для hidpi и нормального отображения
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("NodexConvertor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ImSavsis")
    app.setOrganizationDomain("github.com/ImSavsis")

    # грузим тему до создания окна
    theme = ThemeEngine()
    app.setStyleSheet(theme.get_stylesheet())

    # иконка приложения если есть
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
