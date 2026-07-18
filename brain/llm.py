"""
LLM-клиент (совместим с OpenAI API).

Провайдеры:
  lmstudio — локальный сервер LM Studio (localhost:1234)
  groq     — облако Groq

Два режима:
  - Разговор: plain text, оригинальный промпт
  - Действие: JSON reply+action, когда в команде есть ключевые слова
"""

import json
import re

import requests

import config

# ── Промпт для обычного разговора ─────────────────────────────────────────────
_CONV_PROMPT = (
    "You are Nika, a friendly voice 3D companion. "
    "Detect the language the user writes in and ALWAYS reply in THAT SAME language "
    "(Russian if they write Russian, English if English). "
    "Be warm, natural, conversational. "
    "Keep responses short: 1-3 sentences max. "
    "Never use markdown, asterisks, bullet points, hashtags or emojis — plain text only."
)

# ── Промпт для команд управления ПК ───────────────────────────────────────────
_ACTION_PROMPT = """\
You are a PC assistant. Return ONLY valid JSON, no other text, no markdown:
{"reply": "one-sentence confirmation in the user's language", "action": {...}}

Available actions:
{"type":"open_url","url":"https://..."}
{"type":"open_app","app":"windows_app_name"}
{"type":"search_web","query":"search terms"}
{"type":"type_text","text":"text to type","delay":2}

YouTube search: {"type":"open_url","url":"https://www.youtube.com/results?search_query=query+words"}

Examples:
"open YouTube" → {"reply":"Opening YouTube!","action":{"type":"open_url","url":"https://youtube.com"}}
"найди котов на ютубе" → {"reply":"Ищу котов!","action":{"type":"open_url","url":"https://www.youtube.com/results?search_query=коты"}}
"open Notepad" → {"reply":"Opening Notepad!","action":{"type":"open_app","app":"notepad"}}
"напечатай Привет мир" → {"reply":"Напечатаю через 2 секунды, кликни в нужное поле!","action":{"type":"type_text","text":"Привет мир","delay":2}}\
"""

# Слова → режим действия
_ACTION_KEYWORDS = [
    "open ", "launch ", "start ", "run ",
    "search ", "find ", "look up", "look for",
    "type ", "write ", "enter ", "input ",
    "go to ", "navigate ", "browse ",
    # Русские
    "открой ", "запусти ", "открыть ", "запустить ",
    "найди ", "поищи ", "найти ", "поиск ",
    "напечатай ", "введи ", "напиши ",
    "перейди ", "зайди ",
]


def ask(user_text: str) -> tuple[str, dict | None]:
    """Возвращает (текст_ответа, action_или_None)."""
    if _is_action(user_text):
        return _ask_action(user_text)
    return _ask_conversation(user_text), None


# ── Обычный разговор ───────────────────────────────────────────────────────────

def _ask_conversation(user_text: str) -> str:
    raw = _call(_CONV_PROMPT, user_text, max_tokens=256)
    print(f"[LLM] беседа: «{raw[:100]}»")
    return raw


# ── Команда действия ───────────────────────────────────────────────────────────

def _ask_action(user_text: str) -> tuple[str, dict | None]:
    raw = _call(_ACTION_PROMPT, user_text, max_tokens=200)
    print(f"[LLM] действие raw: {raw[:120]}")

    text = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    text = re.sub(r"\n?```$", "", text)

    try:
        data   = json.loads(text)
        reply  = str(data.get("reply", "Готово!")).strip()
        action = data.get("action") or None
        if action and not isinstance(action, dict):
            action = None
        print(f"[LLM] reply=«{reply}» action={action}")
        return reply, action
    except (json.JSONDecodeError, AttributeError):
        print("[LLM] не JSON, использую как текст")
        return raw, None


# ── Определение: действие или разговор? ───────────────────────────────────────

def _is_action(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _ACTION_KEYWORDS)


# ── HTTP-вызов ────────────────────────────────────────────────────────────────

def _call(system_prompt: str, user_text: str, max_tokens: int = 256) -> str:
    url = f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model":       config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_text},
        ],
        "max_tokens":  max_tokens,
        "temperature": 0.7,
    }
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"LLM API {resp.status_code}: {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"].strip()
