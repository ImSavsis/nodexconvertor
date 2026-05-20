# тут у нас сборщик питона в exe (или линукс бинарь)
# он умеет: сканировать импорты, скачивать зависимости, собирать через pyinstaller
# если что-то не ставится — пробуем другую версию, мы не сдаёмся

import ast  # для разбора питон кода
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── маппинг "import X" → "pip install Y" ──
# потому что не всегда совпадают, питон так устроен, я не виноват

IMPORT_TO_PKG: dict[str, Optional[str]] = {
    # data science
    "numpy":        "numpy",
    "np":           "numpy",      # import numpy as np
    "pandas":       "pandas",
    "pd":           "pandas",
    "matplotlib":   "matplotlib",
    "scipy":        "scipy",
    "sklearn":      "scikit-learn",
    "cv2":          "opencv-python",
    "PIL":          "Pillow",
    "skimage":      "scikit-image",
    "seaborn":      "seaborn",
    "plotly":       "plotly",
    # веб и апи
    "flask":        "Flask",
    "fastapi":      "fastapi",
    "uvicorn":      "uvicorn",
    "django":       "Django",
    "aiohttp":      "aiohttp",
    "httpx":        "httpx",
    "requests":     "requests",
    "bs4":          "beautifulsoup4",
    "selenium":     "selenium",
    "playwright":   "playwright",
    "starlette":    "starlette",
    "tornado":      "tornado",
    "sanic":        "sanic",
    # базы данных
    "sqlalchemy":   "SQLAlchemy",
    "alembic":      "alembic",
    "pymongo":      "pymongo",
    "redis":        "redis",
    "psycopg2":     "psycopg2-binary",
    "pymysql":      "PyMySQL",
    "motor":        "motor",
    "peewee":       "peewee",
    "tortoise":     "tortoise-orm",
    "aiosqlite":    "aiosqlite",
    # auth/security
    "jwt":          "PyJWT",
    "bcrypt":       "bcrypt",
    "cryptography": "cryptography",
    "passlib":      "passlib",
    "Crypto":       "pycryptodome",
    "nacl":         "PyNaCl",
    # файлы и документы
    "docx":         "python-docx",
    "pptx":         "python-pptx",
    "openpyxl":     "openpyxl",
    "xlrd":         "xlrd",
    "lxml":         "lxml",
    "yaml":         "PyYAML",
    "toml":         "tomli",
    "reportlab":    "reportlab",
    "pdfplumber":   "pdfplumber",
    "pypdf":        "pypdf",
    "PyPDF2":       "PyPDF2",
    "fitz":         "PyMuPDF",
    "markdown":     "Markdown",
    "docx2pdf":     "docx2pdf",
    "py7zr":        "py7zr",
    "rarfile":      "rarfile",
    "zipfile36":    "zipfile36",
    # ai и ml
    "openai":       "openai",
    "anthropic":    "anthropic",
    "transformers": "transformers",
    "torch":        "torch",
    "tensorflow":   "tensorflow",
    "keras":        "keras",
    "langchain":    "langchain",
    "groq":         "groq",
    "ollama":       "ollama",
    # телеграм и боты
    "telegram":     "python-telegram-bot",
    "telebot":      "pyTelegramBotAPI",
    "aiogram":      "aiogram",
    "vk_api":       "vk_api",
    "discord":      "discord.py",
    "slack_sdk":    "slack-sdk",
    # утилиты
    "dotenv":       "python-dotenv",
    "click":        "click",
    "typer":        "typer",
    "rich":         "rich",
    "tqdm":         "tqdm",
    "loguru":       "loguru",
    "pydantic":     "pydantic",
    "paramiko":     "paramiko",
    "fabric":       "fabric",
    "celery":       "celery",
    "kombu":        "kombu",
    "schedule":     "schedule",
    "apscheduler":  "APScheduler",
    "psutil":       "psutil",
    "colorama":     "colorama",
    "prettytable":  "prettytable",
    "tabulate":     "tabulate",
    "arrow":        "arrow",
    "dateutil":     "python-dateutil",
    "pytz":         "pytz",
    "qrcode":       "qrcode",
    "barcode":      "python-barcode",
    "chardet":      "chardet",
    "magic":        "python-magic",
    "boto3":        "boto3",
    "botocore":     "botocore",
    # gui
    "PyQt5":        "PyQt5",
    "PyQt6":        "PyQt6",
    "PySide6":      "PySide6",
    "pygame":       "pygame",
    "pyglet":       "pyglet",
    "wx":           "wxPython",
    "customtkinter":"customtkinter",
    "dearpygui":    "dearpygui",
    # другое
    "pyserial":     "pyserial",
    "serial":       "pyserial",
    "usb":          "pyusb",
    "bluetooth":    "PyBluez",
    "cv":           "opencv-python",
    "pynput":       "pynput",
    "pyautogui":    "PyAutoGUI",
    "keyboard":     "keyboard",
    "mouse":        "mouse",
    "pystray":      "pystray",
    "playsound":    "playsound",
    "pygame":       "pygame",
    "pydub":        "pydub",
    "soundfile":    "soundfile",
    "librosa":      "librosa",
    "nmap":         "python-nmap",
    "scapy":        "scapy",
    "imaplib":      None,  # stdlib
    "smtplib":      None,  # stdlib
    "tkinter":      None,  # stdlib
    "sqlite3":      None,  # stdlib
    "winreg":       None,  # только windows, stdlib
    # None = встроенный, не надо ставить
}

# stdlib модули — их устанавливать не надо
STDLIB = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else set()


def scan_imports(py_file: str | Path) -> list[str]:
    # читаем питон файл и вытаскиваем все импорты через ast
    py_file = Path(py_file)
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError as e:
        print(f"⚠  Синтаксическая ошибка в {py_file}: {e}")
        return []

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # берём первую часть: "import os.path" → "os"
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    # убираем стандартные модули и пустые
    result = []
    for imp in sorted(imports):
        if imp and imp not in STDLIB:
            result.append(imp)
    return result


def imports_to_packages(imports: list[str]) -> dict[str, str]:
    # превращаем список импортов в список pip-пакетов
    pkgs = {}
    for imp in imports:
        if imp in IMPORT_TO_PKG:
            pkg = IMPORT_TO_PKG[imp]
            if pkg is None:
                continue  # встроенный модуль
            pkgs[imp] = pkg
        else:
            # импорт неизвестный — пробуем его как есть (часто совпадает)
            pkgs[imp] = imp
    return pkgs


def get_missing(imports: list[str]) -> list[tuple[str, str]]:
    # проверяем что не установлено
    missing = []
    pkgs    = imports_to_packages(imports)
    for imp, pkg in pkgs.items():
        if importlib.util.find_spec(imp) is None:
            missing.append((imp, pkg))
    return missing


def install_packages(packages: list[str], verbose: bool = True) -> dict[str, bool]:
    # устанавливаем пакеты, если не идёт — пробуем другую версию
    results = {}
    for pkg in packages:
        if verbose:
            print(f"📥  Ставлю {pkg}...")

        # сначала пробуем latest
        ok = _pip_install(pkg)
        if ok:
            results[pkg] = True
            if verbose:
                print(f"✓  {pkg} — ок")
            continue

        # не вышло — пробуем без version constraints
        pkg_name = pkg.split(">=")[0].split("<=")[0].split("==")[0].strip()
        if pkg_name != pkg:
            ok = _pip_install(pkg_name)
            if ok:
                results[pkg] = True
                if verbose:
                    print(f"✓  {pkg_name} (без версии) — ок")
                continue

        # совсем не идёт
        results[pkg] = False
        if verbose:
            print(f"✗  {pkg} — не удалось поставить")

    return results


def _pip_install(pkg: str) -> bool:
    # запускаем pip install тихо, возвращаем True если успешно
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
        capture_output=True
    )
    return result.returncode == 0


def auto_install_deps(py_file: str | Path, verbose: bool = True) -> dict:
    # главная функция: сканируем → находим что не стоит → ставим
    py_file = Path(py_file)
    if verbose:
        print(f"🔍  Сканирую импорты в {py_file.name}...")

    imports = scan_imports(py_file)
    if verbose:
        print(f"   Найдено импортов: {len(imports)}")

    missing = get_missing(imports)
    if not missing:
        if verbose:
            print("✓  Все зависимости уже стоят")
        return {"installed": [], "failed": [], "already_ok": imports}

    if verbose:
        print(f"   Не установлено: {[p for _, p in missing]}")

    pkgs_to_install = [pkg for _, pkg in missing]
    results         = install_packages(pkgs_to_install, verbose=verbose)

    installed = [p for p, ok in results.items() if ok]
    failed    = [p for p, ok in results.items() if not ok]
    return {"installed": installed, "failed": failed, "already_ok": imports}


def build_exe(
    py_file: str | Path,
    output_dir: Optional[str | Path] = None,
    one_file:   bool = True,
    console:    bool = True,
    name:       Optional[str] = None,
    icon:       Optional[str] = None,
    extra_args: Optional[list[str]] = None,
    auto_deps:  bool = True,
    verbose:    bool = True,
) -> Path:
    # вот тут мы собираем питон в исполняемый файл
    py_file = Path(py_file)
    if not py_file.exists():
        raise FileNotFoundError(f"Файл не найден: {py_file}")

    if output_dir is None:
        output_dir = py_file.parent / "dist"
    output_dir = Path(output_dir)

    # сначала ставим зависимости если надо
    if auto_deps:
        if verbose:
            print("📦  Проверяю зависимости...")
        auto_install_deps(py_file, verbose=verbose)

    # проверяем что pyinstaller есть
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--version"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        if verbose:
            print("📥  PyInstaller не найден, ставлю...")
        _pip_install("pyinstaller")

    # собираем команду
    cmd = [sys.executable, "-m", "PyInstaller"]

    if one_file:
        cmd.append("--onefile")  # один файл, удобнее
    else:
        cmd.append("--onedir")   # папка с зависимостями

    if not console:
        cmd.append("--noconsole")  # без консоли для GUI приложений

    if name:
        cmd += ["--name", name]
    else:
        cmd += ["--name", py_file.stem]  # имя файла без расширения

    if icon:
        cmd += ["--icon", icon]

    cmd += ["--distpath", str(output_dir)]
    cmd += ["--workpath", str(output_dir / "build")]
    cmd += ["--specpath", str(output_dir)]

    if extra_args:
        cmd.extend(extra_args)  # дополнительные аргументы

    cmd.append(str(py_file))  # наконец сам файл

    if verbose:
        print(f"🔨  Запускаю PyInstaller...")
        print(f"   Команда: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=not verbose, text=True)

    if result.returncode != 0:
        err = result.stderr if result.stderr else "неизвестная ошибка"
        raise RuntimeError(f"PyInstaller упал:\n{err[-1000:]}")

    # ищем результат
    exe_name = (name or py_file.stem)
    # на линуксе — без расширения, на винде — .exe
    exe_path = output_dir / exe_name
    if not exe_path.exists():
        exe_path = output_dir / f"{exe_name}.exe"
    if not exe_path.exists():
        # ищем в dist папке
        found = list(output_dir.glob(f"{exe_name}*"))
        if found:
            exe_path = found[0]
        else:
            exe_path = output_dir  # возвращаем папку если не нашли конкретный файл

    if verbose:
        print(f"✓  Готово: {exe_path}")

    return exe_path
