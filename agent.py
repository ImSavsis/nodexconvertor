# тут у нас AI агент который всё решает
# он умеет конвертить файлы, собирать exe, ставить зависимости
# с ним разговариваешь как с человеком но он умнее (иногда)

import json  # импорты как обычно
import os
import sys
from pathlib import Path
from typing import Optional

from config import get_ai_config  # берём конфиг с ключами
from converter import convert, list_formats, SUPPORTED_IN, SUPPORTED_OUT
from builder import build_exe, auto_install_deps, scan_imports

# ── инструменты которые агент умеет вызывать ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "convert_file",
            "description": "Конвертирует файл из одного формата в другой. Поддерживает docx, pptx, xlsx, xml, json, csv, yaml, pdf, txt, md, изображения, видео и аудио.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Путь к входному файлу"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Целевой формат (например: pdf, json, mp3, png)"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Путь для результата (необязательно, по умолчанию рядом с исходником)"
                    }
                },
                "required": ["input_path", "output_format"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "build_exe",
            "description": "Собирает Python скрипт в исполняемый файл (exe или linux binary). Автоматически устанавливает зависимости.",
            "parameters": {
                "type": "object",
                "properties": {
                    "python_file": {
                        "type": "string",
                        "description": "Путь к Python файлу"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Папка для результата (необязательно)"
                    },
                    "one_file": {
                        "type": "boolean",
                        "description": "Собрать в один файл (true) или папку (false). По умолчанию true."
                    },
                    "console": {
                        "type": "boolean",
                        "description": "Показывать консоль (true для CLI, false для GUI). По умолчанию true."
                    },
                    "name": {
                        "type": "string",
                        "description": "Имя выходного файла (необязательно)"
                    }
                },
                "required": ["python_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "install_deps",
            "description": "Сканирует Python файл и автоматически устанавливает все зависимости.",
            "parameters": {
                "type": "object",
                "properties": {
                    "python_file": {
                        "type": "string",
                        "description": "Путь к Python файлу для анализа"
                    }
                },
                "required": ["python_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_file_imports",
            "description": "Показывает все импорты в Python файле и какие пакеты нужно установить.",
            "parameters": {
                "type": "object",
                "properties": {
                    "python_file": {
                        "type": "string",
                        "description": "Путь к Python файлу"
                    }
                },
                "required": ["python_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_supported_formats",
            "description": "Показывает все поддерживаемые форматы конвертации.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# ── выполнение инструментов ──

def run_tool(name: str, args: dict) -> str:
    # тут вызываем нужную функцию и возвращаем результат как строку
    try:
        if name == "convert_file":
            src    = args["input_path"]
            fmt    = args["output_format"]
            dst    = args.get("output_path")
            result = convert(src, fmt, dst)
            return f"✓ Готово! Файл сохранён: {result}"

        elif name == "build_exe":
            py_file = args["python_file"]
            result  = build_exe(
                py_file    = py_file,
                output_dir = args.get("output_dir"),
                one_file   = args.get("one_file", True),
                console    = args.get("console", True),
                name       = args.get("name"),
                verbose    = True,
            )
            return f"✓ Собрано! Результат: {result}"

        elif name == "install_deps":
            py_file = args["python_file"]
            result  = auto_install_deps(py_file, verbose=True)
            if result["failed"]:
                return (f"Установлено: {result['installed']}\n"
                        f"Не удалось поставить: {result['failed']}")
            return f"✓ Все зависимости установлены: {result['installed'] or 'всё уже было'}"

        elif name == "scan_file_imports":
            py_file = args["python_file"]
            imports = scan_imports(py_file)
            from builder import get_missing, imports_to_packages
            missing = get_missing(imports)
            pkgs    = imports_to_packages(imports)
            lines   = [f"Импорты в {Path(py_file).name}:"]
            for imp in imports:
                pkg    = pkgs.get(imp, imp)
                status = "✓ стоит" if not any(i == imp for i, _ in missing) else "✗ не стоит"
                lines.append(f"  {imp} ({pkg}) — {status}")
            return "\n".join(lines)

        elif name == "list_supported_formats":
            fmts  = list_formats()
            lines = ["Поддерживаемые форматы:"]
            for src_fmt, dst_fmts in sorted(fmts.items()):
                lines.append(f"  {src_fmt} → {', '.join(dst_fmts)}")
            return "\n".join(lines)

        else:
            return f"Неизвестный инструмент: {name}"

    except Exception as e:
        return f"Ошибка: {e}"


# ── системный промпт для агента ──

SYSTEM_PROMPT = """Ты — Nodex Converter AI, умный ассистент для конвертации файлов и сборки Python приложений.

Ты умеешь:
- Конвертировать файлы между форматами: docx, pptx, xlsx, xml, json, csv, yaml, pdf, txt, markdown, изображения, аудио и видео
- Собирать Python скрипты в исполняемые файлы с помощью PyInstaller
- Автоматически находить и устанавливать зависимости Python
- Сканировать импорты в Python файлах

Если пользователь говорит что-то вроде "конвертируй X в Y" — используй convert_file.
Если говорит "собери/скомпилируй/сделай exe из X" — используй build_exe.
Если говорит "установи зависимости/либы для X" — используй install_deps.

Отвечай коротко и по делу. Сразу вызывай нужный инструмент не спрашивая лишних вопросов.
Говори на русском языке."""


# ── главный цикл агента ──

def chat_loop(model: Optional[str] = None):
    # импортируем openai здесь, он может не стоять
    try:
        from openai import OpenAI
    except ImportError:
        print("pip install openai  ← нужно поставить")
        sys.exit(1)

    cfg    = get_ai_config()
    api_key = cfg["api_key"]
    if not api_key:
        print("AI ключ не найден! Положи .env рядом с run.py")
        sys.exit(1)

    client = OpenAI(
        api_key  = api_key,
        base_url = cfg["base_url"],
    )
    use_model = model or cfg["model"]  # берём модель из конфига

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("╔══════════════════════════════════════╗")
    print("║       Nodex Converter AI             ║")
    print("║  Конвертация файлов + сборка Python  ║")
    print("╚══════════════════════════════════════╝")
    print("Напиши что нужно. 'exit' или Ctrl+C для выхода.\n")

    while True:
        try:
            user_input = input("Ты > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nПока!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "выход", "пока"):
            print("Пока!")
            break

        history.append({"role": "user", "content": user_input})

        # цикл вызова инструментов — агент может вызывать несколько за раз
        while True:
            try:
                resp = client.chat.completions.create(
                    model    = use_model,
                    messages = history,
                    tools    = TOOLS,
                    tool_choice = "auto",
                )
            except Exception as e:
                print(f"AI ошибка: {e}")
                break

            msg = resp.choices[0].message

            # если нет инструментов — просто текст
            if not msg.tool_calls:
                reply = msg.content or ""
                print(f"\nAI > {reply}\n")
                history.append({"role": "assistant", "content": reply})
                break

            # добавляем ответ AI с вызовами инструментов в историю
            history.append(msg)  # type: ignore

            # выполняем каждый вызов
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                print(f"\n⚙  {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")
                result = run_tool(fn_name, fn_args)
                print(result)

                # добавляем результат в историю
                history.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      result,
                })

            # идём на следующий круг — вдруг агент ещё что-то хочет сказать


# ── разовый запрос без интерактива ──

def ask_once(prompt: str, model: Optional[str] = None) -> str:
    # для использования из кода или run.py
    try:
        from openai import OpenAI
    except ImportError:
        return "Ошибка: pip install openai"

    cfg    = get_ai_config()
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    model  = model or cfg["model"]

    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ]

    # один цикл с инструментами
    for _ in range(5):  # максимум 5 итераций чтобы не зависнуть
        resp = client.chat.completions.create(
            model    = model,
            messages = history,
            tools    = TOOLS,
            tool_choice = "auto",
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        history.append(msg)  # type: ignore
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}
            result = run_tool(fn_name, fn_args)
            history.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "Агент завис в цикле инструментов, это странно"
