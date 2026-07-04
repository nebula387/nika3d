"""
Синтез речи. Провайдер выбирается через TTS_PROVIDER в .env:
  - "elevenlabs" — облачный API, живой голос, ~0.5с задержка (рекомендуется)
  - "piper"      — локально, без интернета, базовое качество (запасной вариант)
"""

import io
import re
import wave

import numpy as np
import sounddevice as sd

import config


# ── Очистка текста перед синтезом ─────────────────────────────────────────

def _clean(text: str) -> str:
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#+\s?", "", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Загрузка (только для Piper) ────────────────────────────────────────────

def load_voice():
    """
    Возвращает объект голоса Piper или None для облачных провайдеров.
    main.py передаёт результат в speak() — это сохраняет совместимость.
    """
    if config.TTS_PROVIDER == "piper":
        from piper.voice import PiperVoice
        print("[TTS] Загрузка голоса Piper...")
        voice = PiperVoice.load(config.PIPER_VOICE_PATH, use_cuda=False)
        print("[TTS] Голос готов.")
        return voice

    print(f"[TTS] Провайдер: {config.TTS_PROVIDER} (предзагрузка не требуется).")
    return None


# ── Основная функция синтеза ───────────────────────────────────────────────

def speak(voice, text: str) -> None:
    """Синтезировать text и воспроизвести. Блокирует до окончания воспроизведения."""
    clean = _clean(text)
    if not clean:
        return

    if config.TTS_PROVIDER == "elevenlabs":
        _speak_elevenlabs(clean)
    else:
        _speak_piper(voice, clean)


# ── ElevenLabs ─────────────────────────────────────────────────────────────

def _speak_elevenlabs(text: str) -> None:
    import requests

    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech"
        f"/{config.ELEVENLABS_VOICE_ID}"
        f"?output_format=pcm_22050"
    )
    headers = {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "text": text,
        "model_id": config.ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    print(f"[TTS] ElevenLabs синтез: «{text[:60]}{'...' if len(text) > 60 else ''}»")
    resp = requests.post(url, headers=headers, json=body, timeout=15)

    if resp.status_code != 200:
        print(f"[TTS] Ошибка ElevenLabs {resp.status_code}: {resp.text[:200]}")
        return

    # output_format=pcm_22050 → сырые int16-сэмплы, mono, 22050 Hz
    audio = np.frombuffer(resp.content, dtype=np.int16)
    sd.play(audio, samplerate=22050)
    sd.wait()


# ── Piper (локальный запасной вариант) ─────────────────────────────────────

def _speak_piper(voice, text: str) -> None:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_out:
        wav_out.setnchannels(1)
        wav_out.setsampwidth(2)
        wav_out.setframerate(22050)
        voice.synthesize_wav(text, wav_out)

    buf.seek(0)
    with wave.open(buf, "rb") as wav_in:
        frames = wav_in.readframes(wav_in.getnframes())
        rate   = wav_in.getframerate()

    audio = np.frombuffer(frames, dtype=np.int16)
    sd.play(audio, rate)
    sd.wait()
