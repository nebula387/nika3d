"""
XTTS-v2 — локальный TTS с поддержкой русского, английского и клонирования голоса.

Первый запуск: автоматически скачивает модель (~2 GB) в ~/.local/share/tts/
Последующие запуски: загружает из кэша (~3-5 секунд).

Скорость синтеза на CPU (Intel Arc A580 без CUDA):
  - Короткая фраза (5-10 слов): ~2-4 сек
  - Длинная фраза (20+ слов): ~5-10 сек

Для клонирования голоса:
  - Запиши wav-файл 5-30 секунд (чистая речь, без фоновых шумов)
  - Укажи путь в config.XTTS_SPEAKER_WAV
"""

import re
import numpy as np
import sounddevice as sd

_model = None  # ленивая загрузка


def load() -> None:
    """Загрузить модель XTTS-v2 (вызывается один раз при старте)."""
    global _model
    if _model is not None:
        return

    print("[XTTS] Загрузка модели XTTS-v2 (первый раз ~2 GB скачается)...")
    try:
        from TTS.api import TTS
        # use_gpu=False — CPU режим (Intel Arc без CUDA)
        _model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
        print("[XTTS] Модель загружена.")
    except ImportError:
        raise RuntimeError(
            "Пакет TTS не установлен. Выполни: pip install TTS"
        )


def speak(text: str, speaker_wav: str = "", language: str = "auto") -> None:
    """
    Синтезировать и воспроизвести текст.

    text        — текст для озвучки
    speaker_wav — путь к wav-файлу голоса для клонирования (пустая строка = стандартный)
    language    — "auto" | "en" | "ru"
    """
    if _model is None:
        load()

    clean = _clean(text)
    if not clean:
        return

    lang = _detect_lang(clean) if language == "auto" else language
    print(f"[XTTS] Синтез [{lang}]: «{clean[:60]}»")

    try:
        if speaker_wav:
            # Клонирование голоса из wav-файла
            wav = _model.tts(text=clean, speaker_wav=speaker_wav, language=lang)
        else:
            # Стандартный голос модели
            # Для XTTS нужен speaker — используем встроенные
            speakers = _model.speakers
            speaker  = speakers[0] if speakers else None
            wav = _model.tts(text=clean, speaker=speaker, language=lang)

        audio = np.array(wav, dtype=np.float32)
        sd.play(audio, samplerate=24000)
        sd.wait()

    except Exception as e:
        print(f"[XTTS] Ошибка синтеза: {e}")


# ── Вспомогательные ───────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Убрать markdown и спецсимволы перед синтезом."""
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`_~]", "", text)
    return text.strip()


def _detect_lang(text: str) -> str:
    """Простое определение языка по кириллице."""
    cyrillic = sum(1 for c in text if "Ѐ" <= c <= "ӿ")
    return "ru" if cyrillic / max(len(text), 1) > 0.3 else "en"
