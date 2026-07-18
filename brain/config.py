import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────────
# LLM_PROVIDER: "lmstudio" или "groq"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lmstudio")

# LM Studio (локальный сервер, http://localhost:1234)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
LLM_API_KEY  = os.getenv("LLM_API_KEY",  "lm-studio")   # любая строка для LM Studio
LLM_MODEL    = os.getenv("LLM_MODEL",    "qwen2.5-7b-instruct")

# Groq (облако, запасной вариант — раскомментировать в .env если нужен)
# LLM_PROVIDER=groq
# LLM_BASE_URL=https://api.groq.com/openai/v1
# LLM_API_KEY=gsk_...
# LLM_MODEL=openai/gpt-oss-120b

# ── TTS ───────────────────────────────────────────────────────────────────────
# TTS_PROVIDER: "xtts" | "piper" | "elevenlabs"
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "xtts")

# XTTS-v2 — локальный, EN+RU, клонирование голоса
# XTTS_SPEAKER_WAV: путь к wav-файлу голоса для клонирования (5-30 сек, чистая речь)
# Оставить пустым — будет использоваться встроенный голос Xtts по умолчанию
XTTS_SPEAKER_WAV  = os.getenv("XTTS_SPEAKER_WAV",  "")
XTTS_LANGUAGE     = os.getenv("XTTS_LANGUAGE",      "auto")  # "auto" | "en" | "ru"

# Piper (запасной, уже настроен)
PIPER_VOICE_PATH  = os.getenv("PIPER_VOICE_PATH", "")

# ElevenLabs (облако)
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY",  "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL    = os.getenv("ELEVENLABS_MODEL",    "eleven_multilingual_v2")

# ── ASR ───────────────────────────────────────────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WAKE_WORDS    = ["ника", "nika"]

# ── WebSocket-мост ────────────────────────────────────────────────────────────
BRIDGE_HOST = os.getenv("BRIDGE_HOST", "localhost")
BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "8765"))
