"""
Клиент к Groq API (OpenAI-совместимый REST).
Использует requests напрямую — без дополнительных зависимостей.
"""

import requests
import config

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = (
    "You are Nika, a friendly voice 3D companion. "
    "Always respond in English — warm, natural, conversational. "
    "You understand Russian and broken English perfectly; still reply in English. "
    "Keep responses short: 1-3 sentences max. "
    "Never use markdown, asterisks, bullet points, hashtags or emojis — plain text only."
)


def ask(user_text: str) -> str:
    """
    Отправить вопрос в LLM, получить строку-ответ.
    Бросает RuntimeError при ошибке API.
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
        "max_tokens": 256,
        "temperature": 0.7,
    }

    resp = requests.post(_GROQ_URL, headers=headers, json=body, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Groq API {resp.status_code}: {resp.text}")

    return resp.json()["choices"][0]["message"]["content"].strip()
