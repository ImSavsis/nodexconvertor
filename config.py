import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
FFMPEG_DIR = BASE_DIR / "ffmpeg"


def _read_env(path: str) -> dict:
    result = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    result[k.strip()] = v.strip().strip('"').strip("'")
    except (FileNotFoundError, PermissionError):
        pass
    return result


_env = {
    **_read_env(str(BASE_DIR / ".env")),
    **_read_env("/opt/nodeshift-web/backend/.env"),
}

_KEY  = _env.get("DEEPSEEK_API_KEY") or os.getenv("AI_API_KEY", "")
_BASE = "https://api.deepseek.com"
_MOD  = "deepseek-chat"
_MOD_SMART = "deepseek-reasoner"


def get_ai_config() -> dict:
    return {"api_key": _KEY, "base_url": _BASE, "model": _MOD, "model_smart": _MOD_SMART}


def get_ffmpeg() -> str | None:
    local = FFMPEG_DIR / "ffmpeg"
    if local.exists() and os.access(str(local), os.X_OK):
        return str(local)
    return shutil.which("ffmpeg")


def get_libreoffice() -> str | None:
    for name in ("libreoffice", "soffice"):
        found = shutil.which(name)
        if found:
            return found
    return None
