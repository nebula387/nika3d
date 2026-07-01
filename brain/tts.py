"""
Синтез речи через Piper TTS.

Piper читает .onnx-файл голоса (рядом должен лежать одноимённый .onnx.json).
Синтезированное аудио воспроизводится напрямую через sounddevice.
"""

import io
import re
import wave

import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice

import config


def load_voice() -> PiperVoice:
    print("[TTS] Загрузка голоса Piper...")
    voice = PiperVoice.load(config.PIPER_VOICE_PATH, use_cuda=False)
    print("[TTS] Голос готов.")
    return voice


def _clean(text: str) -> str:
    """Убрать markdown и спецсимволы перед синтезом."""
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#+\s?", "", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def speak(voice: PiperVoice, text: str) -> None:
    """Синтезировать текст и воспроизвести через динамики. Блокирует до окончания."""
    clean = _clean(text)
    if not clean:
        return

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_out:
        wav_out.setnchannels(1)
        wav_out.setsampwidth(2)
        wav_out.setframerate(22050)
        voice.synthesize_wav(clean, wav_out)

    buf.seek(0)
    with wave.open(buf, "rb") as wav_in:
        frames = wav_in.readframes(wav_in.getnframes())
        rate   = wav_in.getframerate()

    audio = np.frombuffer(frames, dtype=np.int16)
    sd.play(audio, rate)
    sd.wait()
