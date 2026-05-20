# импорты тут у нас
from PySide6.QtCore import QObject


# тема приложения — все стили живут тут
class ThemeEngine(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = self._dark_palette()

    # def цветовая палитра тёмной темы
    def _dark_palette(self) -> dict:
        return {
            "bg_deep":      "#0a0a0f",
            "bg_surface":   "#111118",
            "bg_panel":     "#18181f",
            "bg_elevated":  "#1e1e28",
            "bg_input":     "#13131a",

            "border":       "#2a2a38",
            "border_focus": "#5b5bf6",
            "border_hover": "#3a3a50",

            "accent":       "#5b5bf6",
            "accent_hover": "#7070f8",
            "accent_dim":   "#2a2a7a",

            "success":      "#4ade80",
            "danger":       "#f87171",
            "warning":      "#fbbf24",

            "text_primary":   "#f0f0fa",
            "text_secondary": "#8888aa",
            "text_muted":     "#55556a",
            "text_accent":    "#8888ff",
        }

    # def главный метод — возвращаем весь qss
    def get_stylesheet(self) -> str:
        p = self._palette
        return f"""
/* ---- база ---- */
QWidget {{
    background-color: {p['bg_deep']};
    color: {p['text_primary']};
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    border: none;
    outline: none;
}}

QMainWindow {{
    background-color: {p['bg_deep']};
}}

/* ---- шапка ---- */
#appHeader {{
    background-color: {p['bg_surface']};
    border-bottom: 1px solid {p['border']};
}}

#appTitle {{
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 2px;
    color: {p['text_primary']};
}}

#appSubtitle {{
    font-size: 11px;
    color: {p['text_muted']};
    margin-left: 10px;
    letter-spacing: 1px;
}}

#githubLink {{
    background: transparent;
    color: {p['text_accent']};
    font-size: 11px;
    letter-spacing: 0.5px;
    border: 1px solid {p['border']};
    padding: 4px 12px;
    border-radius: 4px;
}}
#githubLink:hover {{
    border-color: {p['accent']};
    color: {p['accent_hover']};
}}

/* ---- дроп зона ---- */
#dropZone {{
    background-color: {p['bg_panel']};
    border: 2px dashed {p['border']};
    border-radius: 12px;
}}
#dropZone:hover {{
    border-color: {p['border_hover']};
    background-color: {p['bg_elevated']};
}}
#dropZone[hovering="true"] {{
    border-color: {p['accent']};
    background-color: {p['accent_dim']};
}}

#dropIcon {{
    font-size: 48px;
    color: {p['text_muted']};
}}
#dropMainLabel {{
    font-size: 16px;
    font-weight: 600;
    color: {p['text_secondary']};
    letter-spacing: 1px;
}}
#dropSubLabel {{
    font-size: 11px;
    color: {p['text_muted']};
    letter-spacing: 0.5px;
    line-height: 1.6;
}}
#dropHintLabel {{
    font-size: 11px;
    color: {p['accent']};
    letter-spacing: 0.5px;
}}

/* ---- секции ---- */
#sectionLabel {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    color: {p['text_muted']};
    text-transform: uppercase;
    padding-bottom: 4px;
    border-bottom: 1px solid {p['border']};
}}

#fieldLabel {{
    font-size: 12px;
    color: {p['text_secondary']};
}}

/* ---- список файлов ---- */
#fileList, #logList {{
    background-color: {p['bg_input']};
    border: 1px solid {p['border']};
    border-radius: 6px;
    padding: 4px;
    color: {p['text_primary']};
}}
#fileList::item, #logList::item {{
    padding: 5px 8px;
    border-radius: 4px;
}}
#fileList::item:selected {{
    background-color: {p['accent_dim']};
    color: {p['text_primary']};
}}
#fileList::item:hover {{
    background-color: {p['bg_elevated']};
}}

/* ---- комбо выбора формата ---- */
#formatCombo {{
    background-color: {p['bg_input']};
    border: 1px solid {p['border']};
    border-radius: 6px;
    padding: 6px 12px;
    color: {p['text_primary']};
    min-height: 30px;
}}
#formatCombo:focus {{
    border-color: {p['border_focus']};
}}
#formatCombo QAbstractItemView {{
    background-color: {p['bg_elevated']};
    border: 1px solid {p['border']};
    selection-background-color: {p['accent_dim']};
}}

/* ---- кнопки ---- */
#primaryBtn {{
    background-color: {p['accent']};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
#primaryBtn:hover {{
    background-color: {p['accent_hover']};
}}
#primaryBtn:pressed {{
    background-color: {p['accent_dim']};
}}
#primaryBtn:disabled {{
    background-color: {p['bg_elevated']};
    color: {p['text_muted']};
}}

#secondaryBtn {{
    background-color: transparent;
    color: {p['text_secondary']};
    border: 1px solid {p['border']};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
}}
#secondaryBtn:hover {{
    border-color: {p['border_hover']};
    color: {p['text_primary']};
}}

#dangerBtn {{
    background-color: transparent;
    color: {p['danger']};
    border: 1px solid {p['danger']};
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 12px;
}}
#dangerBtn:hover {{
    background-color: rgba(248, 113, 113, 0.1);
}}

/* ---- прогресс трекер ---- */
#progressTracker {{
    background-color: {p['bg_panel']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    padding: 16px;
}}

#mainProgressBar {{
    background-color: {p['bg_elevated']};
    border: none;
    border-radius: 4px;
}}
#mainProgressBar::chunk {{
    background-color: {p['accent']};
    border-radius: 4px;
}}

#countLabel {{
    font-size: 12px;
    color: {p['text_secondary']};
    font-family: 'JetBrains Mono', monospace;
}}
#percentLabel {{
    font-size: 12px;
    color: {p['accent']};
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
}}

#statusLabel {{
    font-size: 12px;
    color: {p['text_muted']};
    padding: 6px 10px;
    background-color: {p['bg_input']};
    border-radius: 5px;
    border-left: 3px solid {p['border']};
}}
#statusLabel[done="true"] {{
    color: {p['success']};
    border-left-color: {p['success']};
}}
#statusLabel[error="true"] {{
    color: {p['danger']};
    border-left-color: {p['danger']};
}}

/* ---- скроллбары ---- */
QScrollBar:vertical {{
    background: {p['bg_surface']};
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p['border']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p['border_focus']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ---- статус бар ---- */
QStatusBar {{
    background-color: {p['bg_surface']};
    color: {p['text_muted']};
    font-size: 11px;
    letter-spacing: 0.5px;
    border-top: 1px solid {p['border']};
    padding: 0 12px;
}}

/* ---- тултипы ---- */
QToolTip {{
    background-color: {p['bg_elevated']};
    color: {p['text_primary']};
    border: 1px solid {p['border']};
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
}}

/* ---- табы правой колонки ---- */
#rightTabs::pane {{
    border: none;
    background: transparent;
}}
#rightTabs QTabBar::tab {{
    background: transparent;
    color: {p['text_muted']};
    padding: 8px 16px;
    border-radius: 6px;
    margin: 2px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
#rightTabs QTabBar::tab:selected {{
    background: {p['accent']};
    color: #ffffff;
}}
#rightTabs QTabBar::tab:hover:!selected {{
    background: {p['bg_elevated']};
    color: {p['text_primary']};
}}

/* ---- лог сборки ---- */
#buildLog, #chatHistory {{
    background-color: {p['bg_input']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 10px;
    color: {p['text_secondary']};
    font-size: 12px;
    line-height: 1.6;
}}

/* ---- чекбоксы в билдере ---- */
QCheckBox {{
    color: {p['text_secondary']};
    spacing: 8px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid {p['border']};
    background: transparent;
}}
QCheckBox::indicator:checked {{
    background: {p['accent']};
    border-color: {p['accent']};
}}

/* ---- input поле AI агента ---- */
QLineEdit {{
    background-color: {p['bg_input']};
    border: 1px solid {p['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {p['text_primary']};
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {p['border_focus']};
}}
        """
