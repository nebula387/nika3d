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
import web

# ── Промпт для обычного разговора ─────────────────────────────────────────────
# Язык жёстко английский (2026-07-18, решение пользователя) — ASR теперь тоже
# только English, определение языка больше не нужно ни на входе, ни на выходе.
_CONV_PROMPT = (
    "You are Nika, a friendly voice 3D companion. "
    "Reply ONLY in English, even if the user's speech-to-text input looks garbled "
    "or has typos — do your best to understand hesitant, imperfect English. "
    "Do not switch language, do not add translations or notes about language. "
    "Use ONLY Latin letters — NEVER Cyrillic, Chinese, Japanese, Korean, or any "
    "other script, even by accident. "
    "Be warm, natural, conversational. "
    "Keep responses short: 1-3 sentences max. "
    "Never use markdown, asterisks, bullet points, hashtags, emojis, or "
    "parenthetical remarks — output ONLY the plain-text reply itself, nothing else."
)

# ── Промпт для команд управления ПК ───────────────────────────────────────────
_ACTION_PROMPT = """\
You are a PC assistant. Return ONLY valid JSON, no other text, no markdown:
{"reply": "one-sentence confirmation in English", "action": {...}}
Use ONLY Latin letters in "reply" — NEVER Cyrillic, Chinese, Japanese, Korean, or any other script.

Available actions:
{"type":"open_url","url":"https://..."}
{"type":"open_app","app":"windows_app_name"}
{"type":"search_web","query":"search terms"}
{"type":"type_text","text":"text to type","delay":2}

YouTube search: {"type":"open_url","url":"https://www.youtube.com/results?search_query=query+words"}

Examples:
"open YouTube" → {"reply":"Opening YouTube!","action":{"type":"open_url","url":"https://youtube.com"}}
"find cats on youtube" → {"reply":"Searching for cats!","action":{"type":"open_url","url":"https://www.youtube.com/results?search_query=cats"}}
"open Notepad" → {"reply":"Opening Notepad!","action":{"type":"open_app","app":"notepad"}}
"type Hello world" → {"reply":"Typing that in 2 seconds, click where you want it!","action":{"type":"type_text","text":"Hello world","delay":2}}\
"""

# Слова → режим действия
_ACTION_KEYWORDS = [
    "open ", "launch ", "start ", "run ",
    "search ", "find ", "look up", "look for",
    "type ", "write ", "enter ", "input ",
    "go to ", "navigate ", "browse ",
]

# ── Промпт для ответа на основе найденных в интернете данных ─────────────────
_WEB_PROMPT = (
    "You are Nika, a friendly voice 3D companion. You were given real, "
    "up-to-date data found online — use ONLY that data to answer, do not add "
    "facts you're not sure of. Answer the user's question in 1-2 short "
    "sentences, natural and conversational, in English. "
    "Never use markdown, asterisks, emojis, or mention 'according to the data' "
    "— just answer directly, as if you already knew it."
)

# Слова → режим веб-запроса (проверяются ДО _ACTION_KEYWORDS)
_WEATHER_KEYWORDS = [
    "weather", "forecast", "temperature outside",
    "is it raining", "is it snowing", "how hot", "how cold",
]
_FX_KEYWORDS = [
    "exchange rate", "currency rate", "conversion rate",
    "how much is a dollar", "how much is a euro", "how much is the dollar",
    "how much is the euro", "convert dollars", "convert euros",
]
_NEWS_KEYWORDS = ["news", "headlines", "what's happening", "latest news"]
_ONLINE_SEARCH_KEYWORDS = [
    "search online", "search the internet", "search on the internet",
    "check online", "check the internet", "look up online",
    "find online", "find on the internet", "google that", "google it",
    "search google",
]


def _is_web_query(text: str) -> bool:
    lower = text.lower()
    return any(
        kw in lower
        for kw in _WEATHER_KEYWORDS + _FX_KEYWORDS + _NEWS_KEYWORDS + _ONLINE_SEARCH_KEYWORDS
    )


def _extract_city(text: str) -> str:
    """Ищем "in <город>" в конце фразы. Если не нашли — город по умолчанию."""
    match = re.search(r"\bin\s+([a-zA-Z][a-zA-Z\s]*)\s*$", text.strip().rstrip("?."))
    if match:
        return match.group(1).strip()
    return config.WEATHER_CITY


def _extract_currency_pair(text: str) -> tuple[str, str]:
    """Ищем две упомянутые валюты в тексте, иначе пара по умолчанию из .env."""
    lower = text.lower()
    found = []
    for word, code in web.CURRENCY_WORDS.items():
        if word in lower and code not in found:
            found.append(code)
    if len(found) >= 2:
        return found[0], found[1]
    if len(found) == 1:
        # Одна валюта названа — считаем её целью, база по умолчанию из .env
        base = config.DEFAULT_FX_BASE
        return (base, found[0]) if found[0] != base else (found[0], config.DEFAULT_FX_TARGET)
    return config.DEFAULT_FX_BASE, config.DEFAULT_FX_TARGET


# ── Память сессии ──────────────────────────────────────────────────────────────
# Живёт, пока работает процесс main.py — при перезапуске обнуляется.
# Используется только в обычном разговоре (_ask_conversation): там от истории
# больше всего пользы (местоимения, "а что насчёт...") и меньше риска, что
# история собьёт модель с формата — в отличие от строгого JSON в _ask_action.
_history: list[dict] = []

_FORGET_PHRASES = [
    "forget everything", "forget what we talked about", "clear your memory",
    "clear the conversation", "start a new conversation", "let's start over",
    "reset the conversation", "forget our conversation",
]


def _remember(user_text: str, reply: str) -> None:
    _history.append({"role": "user", "content": user_text})
    _history.append({"role": "assistant", "content": reply})
    max_messages = config.MAX_HISTORY_TURNS * 2
    if len(_history) > max_messages:
        del _history[: len(_history) - max_messages]


def reset_history() -> None:
    _history.clear()


def ask(user_text: str) -> tuple[str, dict | None]:
    """Возвращает (текст_ответа, action_или_None)."""
    lower = user_text.lower()
    if any(p in lower for p in _FORGET_PHRASES):
        reset_history()
        print("[LLM] память разговора очищена")
        return "Okay, I've cleared our conversation. What's up?", None

    if _is_web_query(user_text):
        reply = _ask_web(user_text)
        _remember(user_text, reply)
        return reply, None

    if _is_action(user_text):
        reply, action = _ask_action(user_text)
        _remember(user_text, reply)
        return reply, action

    reply = _ask_conversation(user_text)
    _remember(user_text, reply)
    return reply, None


# Диапазоны CJK-символов (китайский/японский/корейский) — маленькие локальные
# модели (qwen, gemma) иногда подмешивают их в ответ вопреки промпту.
# Вырезаем как страховку перед озвучкой.
_CJK_RE = re.compile(
    "["
    "　-〿"   # символы и пунктуация CJK (полноширинные , . ! ? и т.п.)
    "぀-ヿ"   # хирагана + катакана
    "㐀-䶿"   # CJK расширение A
    "一-鿿"   # основные иероглифы CJK
    "가-힯"   # хангыль (корейский)
    "豈-﫿"   # совместимость CJK
    "＀-￯"   # полноширинные формы (：，。！ и т.п.)
    "]+"
)


def _strip_cjk(text: str) -> str:
    cleaned = _CJK_RE.sub("", text)
    return re.sub(r"\s+", " ", cleaned).strip()


# ── Веб-запрос (погода / курс / новости / поиск) ──────────────────────────────

def _ask_web(user_text: str) -> str:
    lower = user_text.lower()

    if any(kw in lower for kw in _WEATHER_KEYWORDS):
        city = _extract_city(user_text)
        print(f"[LLM] погода: город={city}")
        info = web.get_weather(city)
        return _strip_cjk(info)  # уже готовая фраза, LLM не нужен

    if any(kw in lower for kw in _FX_KEYWORDS):
        base, target = _extract_currency_pair(user_text)
        print(f"[LLM] курс валют: {base}->{target}")
        info = web.get_exchange_rate(base, target)
        return _strip_cjk(info)  # уже готовая фраза, LLM не нужен

    if any(kw in lower for kw in _NEWS_KEYWORDS):
        print("[LLM] новости")
        info = web.news_search(user_text)
    else:
        print(f"[LLM] веб-поиск: «{user_text}»")
        info = web.web_search(user_text)

    print(f"[LLM] найдено: {info[:150]}")
    raw = _call(_WEB_PROMPT, f"User asked: {user_text}\n\nData found online:\n{info}",
                max_tokens=200)
    return _strip_cjk(raw)


# ── Обычный разговор ───────────────────────────────────────────────────────────

def _ask_conversation(user_text: str) -> str:
    raw = _call(_CONV_PROMPT, user_text, max_tokens=256, history=_history)
    reply = _strip_cjk(raw)
    print(f"[LLM] беседа: «{reply[:100]}»")
    return reply


# ── Команда действия ───────────────────────────────────────────────────────────

def _ask_action(user_text: str) -> tuple[str, dict | None]:
    raw = _call(_ACTION_PROMPT, user_text, max_tokens=200)
    print(f"[LLM] действие raw: {raw[:120]}")

    text = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    text = re.sub(r"\n?```$", "", text)

    try:
        data   = json.loads(text)
        reply  = _strip_cjk(str(data.get("reply", "Done!")))
        action = data.get("action") or None
        if action and not isinstance(action, dict):
            action = None
        print(f"[LLM] reply=«{reply}» action={action}")
        return reply, action
    except (json.JSONDecodeError, AttributeError):
        print("[LLM] не JSON, использую как текст")
        return _strip_cjk(raw), None


# ── Определение: действие или разговор? ───────────────────────────────────────

def _is_action(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _ACTION_KEYWORDS)


# ── Автоопределение модели (LLM_MODEL=auto) ───────────────────────────────────
# LM Studio отдаёт по /v1/models ВСЕ скачанные модели, а не только загруженную.
# Расширенный /api/v0/models показывает поле "state": "loaded"/"not-loaded" —
# по нему и находим модель, которая сейчас реально в памяти.

def _resolve_model() -> str:
    if config.LLM_PROVIDER != "lmstudio" or config.LLM_MODEL.lower() != "auto":
        return config.LLM_MODEL

    root = re.sub(r"/v1/?$", "", config.LLM_BASE_URL.rstrip("/"))
    try:
        resp = requests.get(f"{root}/api/v0/models", timeout=5)
        resp.raise_for_status()
        for m in resp.json().get("data", []):
            if m.get("state") == "loaded" and m.get("type") in ("llm", "vlm"):
                return m["id"]
    except Exception as e:
        print(f"[LLM] Не удалось определить модель автоматически: {e}")

    raise RuntimeError(
        "LLM_MODEL=auto, но в LM Studio не загружена ни одна модель. "
        "Загрузите модель в LM Studio (кнопка Load) и попробуйте снова."
    )


# ── HTTP-вызов ────────────────────────────────────────────────────────────────

def _call(system_prompt: str, user_text: str, max_tokens: int = 256,
          history: list[dict] | None = None) -> str:
    url = f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    body = {
        "model":       _resolve_model(),
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": 0.7,
    }
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"LLM API {resp.status_code}: {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"].strip()
