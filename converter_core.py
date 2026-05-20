# импорты тут у нас — всё что нужно для конвертации
import os
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal

# аудио конвертация (pydub — это обёртка над ffmpeg)
try:
    from pydub import AudioSegment
    PYDUB_OK = True
except ImportError:
    PYDUB_OK = False

# картинки
try:
    from PIL import Image
    import pillow_heif  # heif/heic поддержка (яблочные фото)
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# pdf через pymupdf — самый надёжный
try:
    import fitz  # это PyMuPDF, не путай с названием импорта
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

# videoконвертация через ffmpeg-python если установлен
try:
    import ffmpeg
    FFMPEG_PY_OK = True
except ImportError:
    FFMPEG_PY_OK = False

# мой универсальный конвертер — для xml, json, csv, yaml, docx, pptx, xlsx и тд
from converter import convert as universal_convert


# все форматы которые мы поддерживаем — сгруппированы по категориям
SUPPORTED_FORMATS = {
    "audio": {
        "extensions": [".flac", ".mp3", ".wav", ".ogg", ".aac", ".m4a", ".wma", ".opus"],
        "targets":    ["mp3", "flac", "wav", "ogg", "aac", "m4a", "opus"],
    },
    "image": {
        "extensions": [".png", ".jpg", ".jpeg", ".ico", ".bmp", ".gif", ".webp",
                       ".tiff", ".tga", ".heic", ".heif"],
        "targets":    ["png", "jpg", "ico", "bmp", "gif", "webp", "tiff"],
    },
    "document": {
        "extensions": [".pdf", ".txt", ".html", ".htm", ".md", ".markdown"],
        "targets":    ["pdf", "txt", "html", "md"],
    },
    "video": {
        "extensions": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".ts",
                       ".wmv", ".mpeg", ".mpg", ".3gp"],
        "targets":    ["mp4", "mkv", "avi", "mov", "webm"],
    },
    # мои новые категории — xml/json/yaml/csv и офисные документы
    "data": {
        "extensions": [".xml", ".json", ".csv", ".yaml", ".yml"],
        "targets":    ["xml", "json", "csv", "yaml", "html"],
    },
    "office": {
        "extensions": [".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls"],
        "targets":    ["pdf", "txt", "html", "md", "csv", "json"],
    },
}


# ядро конвертации — сигналы для общения с UI живут тут
class ConverterCore(QObject):
    progress_updated = Signal(int, int)   # текущий номер, всего файлов
    conversion_done  = Signal(bool, str)  # (успех, сообщение)
    status_message   = Signal(str)

    def __init__(self):
        super().__init__()
        self._cancel_flag = False

    # def определяем к какой категории относится файл
    def detect_category(self, filepath: str) -> str | None:
        ext = Path(filepath).suffix.lower()
        for category, data in SUPPORTED_FORMATS.items():
            if ext in data["extensions"]:
                return category
        return None

    # def возвращаем список форматов в которые можно конвертировать файл
    def get_targets(self, filepath: str) -> list[str]:
        category = self.detect_category(filepath)
        if not category:
            return []
        ext = Path(filepath).suffix.lower().lstrip(".")
        targets = SUPPORTED_FORMATS[category]["targets"]
        # исключаем текущий формат из списка
        return [t for t in targets if t != ext]

    # def запускаем конвертацию пачки файлов в отдельном потоке
    def convert_batch(self, files: list[dict], output_dir: str):
        self._cancel_flag = False
        thread = threading.Thread(
            target=self._run_batch,
            args=(files, output_dir),
            daemon=True
        )
        thread.start()

    # def основной цикл — перебираем файлы
    def _run_batch(self, files: list[dict], output_dir: str):
        total  = len(files)
        errors = []

        for i, task in enumerate(files):
            if self._cancel_flag:
                self.status_message.emit("конвертация отменена")
                self.conversion_done.emit(False, "отменено пользователем")
                return

            src        = task["path"]
            target_fmt = task["target_format"]
            self.status_message.emit(f"конвертирую {Path(src).name} → {target_fmt}")

            try:
                self._convert_single(src, target_fmt, output_dir)
            except Exception as e:
                errors.append(f"{Path(src).name}: {e}")

            self.progress_updated.emit(i + 1, total)

        if errors:
            self.conversion_done.emit(False, "готово с ошибками:\n" + "\n".join(errors))
        else:
            self.conversion_done.emit(True, f"всё готово — {total} файлов конвертировано")

    # def конвертируем один файл — роутим по категории
    def _convert_single(self, src: str, target_fmt: str, output_dir: str):
        category = self.detect_category(src)
        stem     = Path(src).stem
        out_path = os.path.join(output_dir, f"{stem}.{target_fmt}")

        if category == "audio":
            self._convert_audio(src, out_path, target_fmt)
        elif category == "image":
            self._convert_image(src, out_path, target_fmt)
        elif category == "document":
            self._convert_document(src, out_path, target_fmt)
        elif category == "video":
            self._convert_video(src, out_path, target_fmt)
        elif category in ("data", "office"):
            # делегируем в мой универсальный конвертер
            universal_convert(src, target_fmt, out_path)
        else:
            raise ValueError(f"неизвестная категория для {src}")

    # def аудио — pydub умеет большинство форматов
    def _convert_audio(self, src: str, out_path: str, fmt: str):
        if not PYDUB_OK:
            raise RuntimeError("pip install pydub  (и нужен ffmpeg в PATH)")
        audio = AudioSegment.from_file(src)
        params = {}
        if fmt == "mp3":
            params["bitrate"] = "320k"  # максимальное качество mp3
        audio.export(out_path, format=fmt, **params)

    # def картинки — pillow умеет всё
    def _convert_image(self, src: str, out_path: str, fmt: str):
        if not PILLOW_OK:
            raise RuntimeError("pip install Pillow pillow-heif")
        img = Image.open(src)

        # ico — особый случай, нужны разные размеры
        if fmt == "ico":
            sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
            img.save(out_path, format="ICO", sizes=sizes)
            return

        # jpg не умеет прозрачность — кладём на белый фон
        if fmt in ("jpg", "jpeg") and img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg

        save_params = {}
        if fmt == "webp":
            save_params["quality"] = 95  # webp с хорошим качеством
            save_params["method"]  = 6

        img.save(out_path, format=fmt.upper(), **save_params)

    # def pdf и другие документы
    def _convert_document(self, src: str, out_path: str, fmt: str):
        src_ext = Path(src).suffix.lower()

        # pdf → картинка через pymupdf
        if src_ext == ".pdf" and fmt in ("png", "jpg"):
            if not FITZ_OK:
                raise RuntimeError("pip install PyMuPDF")
            doc = fitz.open(src)
            for page_num, page in enumerate(doc):
                mat = fitz.Matrix(2, 2)  # x2 чтобы было чёткое
                pix = page.get_pixmap(matrix=mat)
                page_out = out_path.replace(f".{fmt}", f"_p{page_num + 1}.{fmt}")
                pix.save(page_out)
            return

        # всё остальное — в мой универсальный конвертер
        universal_convert(src, fmt, out_path)

    # def видео через ffmpeg-python
    def _convert_video(self, src: str, out_path: str, fmt: str):
        if FFMPEG_PY_OK:
            # используем ffmpeg-python если стоит
            (ffmpeg
             .input(src)
             .output(out_path)
             .overwrite_output()
             .run(quiet=True))
        else:
            # иначе через системный ffmpeg напрямую
            from config import get_ffmpeg
            ff = get_ffmpeg()
            if not ff:
                raise RuntimeError("ffmpeg не найден — положи в ./ffmpeg/ffmpeg")
            import subprocess
            result = subprocess.run(
                [ff, "-y", "-i", src, out_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg: {result.stderr[-400:]}")

    # def отмена текущей конвертации
    def cancel(self):
        self._cancel_flag = True
