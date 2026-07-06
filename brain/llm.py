"""
Клиент к Groq API (OpenAI-совместимый REST).

Возвращает tuple (reply: str, action: dict | None).
  reply  — текст для озвучки
  action — словарь действия или None если просто разговор
"""

import json
import re

import requests

import config

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = """\
You are Nika, a friendly voice 3D companion and PC assistant.

ALWAYS respond with valid JSON only — no extra text, no markdown fences:
{"reply": "...", "action": null}

reply rules:
- English only, 1-3 sentences, warm and natural
- No markdown, no asterisks, no emojis
- You understand Russian perfectly; always reply in English

action — set to null for normal conversation.
For PC control commands use one of these:

Open a website:
{"type":"open_url","url":"https://..."}

Open an installed program (use Windows app name):
{"type":"open_app","app":"chrome"}

Search on Google:
{"type":"search_web","query":"search terms"}

Search on YouTube:
{"type":"open_url","url":"https://www.youtube.com/results?search_query=search+terms"}

Type text (user must click the target field first):
{"type":"type_text","text":"text to type","delay":2}

Examples:
"open YouTube" → {"reply":"Opening YouTube!","action":{"type":"open_url","url":"https://youtube.com"}}
"search cats on YouTube" → {"reply":"Searching for cats on YouTube!","action":{"type":"open_url","url":"https://www.youtube.com/results?search_query=cats"}}
"open Notepad" → {"reply":"Sure, opening Notepad!","action":{"type":"open_app","app":"notepad"}}
"open Chrome" → {"reply":"Opening Chrome!","action":{"type":"open_app","app":"chrome"}}
"type Hello World" → {"reply":"I'll type that in 2 seconds, please click where you want it!","action":{"type":"type_text","text":"Hello World","delay":2}}
"search Python tutorials" → {"reply":"Searching for Python tutorials!","action":{"type":"search_web","query":"Python tutorials"}}
"how are you" → {"reply":"I'm doing great, thanks for asking!","action":null}\
"""


def ask(user_text: str) -> tuple[str, dict | None]:
    """
    Отправить вопрос в LLM.
    Возвращает (текст_ответа, action_или_None).
    """
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_text},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    resp = requests.post(_GROQ_URL, headers=headers, json=body, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Groq API {resp.status_code}: {resp.text}")

    raw = resp.json()["choices"][0]["message"]["content"].strip()
    return _parse(raw)


def _parse(raw: str) -> tuple[str, dict | None]:
    """Распарсить JSON-ответ LLM. При ошибке вернуть raw как reply без action."""
    # Убрать markdown-обёртки ```json ... ``` если LLM всё же добавил
    text = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    text = re.sub(r"\n?```$", "", text)

    try:
        data = json.loads(text)
        reply  = str(data.get("reply", raw)).strip()
        action = data.get("action") or None
        if action and not isinstance(action, dict):
            action = None
        return reply, action
    except (json.JSONDecodeError, AttributeError):
        # LLM не вернул JSON — вся строка идёт как reply
        print(f"[LLM] Не JSON, использую как текст: {raw[:80]}")
        return raw, None
