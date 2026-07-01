"""
Распознавание речи через Whisper + VAD по пиковой амплитуде.

Схема по аналогии со старым проектом (nika.py):
  1. Слушаем фиксированными 2-секундными чанками через sd.rec()
  2. Если пиковая громкость ниже порога — пропускаем (тишина)
  3. Транскрибируем чанк; ищем слово активации
  4. На активации — отдельная запись команды через record_until_silence()
  5. Транскрибируем команду и возвращаем как текст запроса

language=None — авто-определение языка (лучше справляется с "Ника" на русском
и "Nika" на английском, чем жёстко заданный язык).
"""

import numpy as np
import sounddevice as sd
import whisper

import config

# ── параметры ──────────────────────────────────────────────────────────────────
SAMPLE_RATE       = 16_000  # Hz; Whisper ожидает именно 16 кГц
WAKE_CHUNK_SEC    = 2.0     # длина чанка прослушивания для wake word
SILENCE_THRESHOLD = 0.02    # пиковая амплитуда ниже этого = тишина
SILENCE_SECONDS   = 1.5     # пауза, после которой команда считается завершённой
CHUNK_DURATION    = 0.5     # размер одного блока при записи команды (сек)

# Расширенный список: учитываем ошибки транскрипции Whisper на русском/английском
WAKE_VARIANTS = [
    "ника", "нике", "нека", "никa",   # кириллица + опечатки
    "nika", "nica", "nike", "nika,",   # латиница
]


def load_whisper() -> whisper.Whisper:
    print("[ASR] Загрузка Whisper...")
    model = whisper.load_model(config.WHISPER_MODEL)
    print(f"[ASR] Whisper '{config.WHISPER_MODEL}' готов.")
    return model


def _record_until_silence() -> np.ndarray | None:
    """
    Запись команды: пишем чанками, останавливаемся после SILENCE_SECONDS тишины.
    Возвращает float32 массив или None если речи не было вообще.
    """
    chunk_size   = int(SAMPLE_RATE * CHUNK_DURATION)
    max_silent   = int(SILENCE_SECONDS / CHUNK_DURATION)

    chunks       = []
    silent_count = 0
    has_speech   = False

    while True:
        chunk = sd.rec(chunk_size, samplerate=SAMPLE_RATE,
                       channels=1, dtype="float32")
        sd.wait()

        peak = float(np.max(np.abs(chunk)))

        if peak > SILENCE_THRESHOLD:
            chunks.append(chunk)
            silent_count = 0
            has_speech = True
        else:
            if has_speech:
                chunks.append(chunk)
                silent_count += 1
                if silent_count >= max_silent:
                    break

    if not chunks:
        return None
    return np.concatenate(chunks).flatten()


def listen_for_followup(model: whisper.Whisper, timeout_sec: float = 10.0) -> str | None:
    """
    Ждёт продолжение разговора без слова активации.
    Возвращает текст вопроса или None если за timeout_sec не было речи.
    """
    chunk_size = int(SAMPLE_RATE * CHUNK_DURATION)
    max_chunks = int(timeout_sec / CHUNK_DURATION)

    print(f"[ASR] Жду продолжение ({timeout_sec:.0f} сек)...")

    for _ in range(max_chunks):
        chunk = sd.rec(chunk_size, samplerate=SAMPLE_RATE,
                       channels=1, dtype="float32")
        sd.wait()

        if float(np.max(np.abs(chunk))) > SILENCE_THRESHOLD:
            audio = _record_until_silence()
            if audio is None:
                continue
            result = model.transcribe(audio, language=None, fp16=False)
            text = result["text"].strip()
            if text:
                print(f"[ASR] продолжение: «{text.lower()}»")
                return text

    print("[ASR] Таймаут — возврат в режим ожидания слова активации.")
    return None


def listen_for_wake_word(model: whisper.Whisper) -> str:
    """
    Блокирует выполнение до обнаружения слова активации.
    Возвращает команду пользователя (текст запроса к LLM).
    """
    wake_chunk_size = int(SAMPLE_RATE * WAKE_CHUNK_SEC)
    print("[ASR] Жду слово активации ('Ника')...")

    while True:
        # Запись фиксированного чанка для поиска wake word
        chunk = sd.rec(wake_chunk_size, samplerate=SAMPLE_RATE,
                       channels=1, dtype="float32")
        sd.wait()

        # Пропустить тишину без транскрипции (экономит время)
        if float(np.max(np.abs(chunk))) < SILENCE_THRESHOLD:
            continue

        result = model.transcribe(chunk.flatten(), language=None, fp16=False)
        text = result["text"].strip().lower()

        if not text:
            continue

        print(f"[ASR] услышал: «{text}»")

        if any(w in text for w in WAKE_VARIANTS):
            print("[ASR] Слово активации! Жду вопрос...")

            # Короткий сигнал-подтверждение (100 мс тишины)
            sd.play(np.zeros(1600, dtype=np.int16), SAMPLE_RATE)
            sd.wait()

            audio = _record_until_silence()
            if audio is None:
                continue

            result2 = model.transcribe(audio, language=None, fp16=False)
            command = result2["text"].strip()
            if command:
                return command
