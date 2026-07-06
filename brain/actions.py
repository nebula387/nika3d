"""
Выполнение действий на ПК по команде от LLM.

Поддерживаемые типы:
  open_url   — открыть URL в браузере по умолчанию
  open_app   — запустить программу через Windows (start)
  type_text  — напечатать текст в активном окне (через буфер обмена)
  search_web — поиск Google в браузере
"""

import subprocess
import time
import webbrowser

import pyperclip
import pyautogui


def execute(action: dict) -> None:
    """Выполнить action-словарь из ответа LLM."""
    action_type = action.get("type", "")

    if action_type == "open_url":
        _open_url(action.get("url", ""))

    elif action_type == "open_app":
        _open_app(action.get("app", ""))

    elif action_type == "type_text":
        delay = float(action.get("delay", 2.0))
        _type_text(action.get("text", ""), delay)

    elif action_type == "search_web":
        query = action.get("query", "")
        _open_url(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    else:
        print(f"[Действие] Неизвестный тип: {action_type}")


# ── Реализация ─────────────────────────────────────────────────────────────

def _open_url(url: str) -> None:
    if not url:
        return
    print(f"[Действие] Открываю URL: {url}")
    webbrowser.open(url)


def _open_app(app: str) -> None:
    if not app:
        return
    print(f"[Действие] Запускаю программу: {app}")
    # Windows: start "" "имя" находит программу по имени через PATH и реестр
    subprocess.Popen(["start", "", app], shell=True)


def _type_text(text: str, delay: float) -> None:
    if not text:
        return
    print(f"[Действие] Печатаю через {delay:.0f} сек: «{text}»")
    time.sleep(delay)  # даём время кликнуть в нужное поле
    # Через буфер обмена — работает с любыми символами (кириллица, спецсимволы)
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
