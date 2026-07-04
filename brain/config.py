import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_API_KEY  = os.getenv("LLM_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

PIPER_VOICE_PATH = os.getenv("PIPER_VOICE_PATH", "")

# ── TTS-провайдер ──────────────────────────────────────────────────────────
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "piper")  # "elevenlabs" или "piper"

# ElevenLabs (если TTS_PROVIDER=elevenlabs)
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL    = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

BRIDGE_HOST = os.getenv("BRIDGE_HOST", "localhost")
BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "8765"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Слова активации в нижнем регистре (сравниваются с транскриптом тоже в lowercase)
WAKE_WORDS = ["ника", "nika"]
