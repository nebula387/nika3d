"""
Точка входа Python-части (brain).

Запуск:
    python main.py

Порядок инициализации:
  1. WebSocket-сервер (фоновый поток) — Godot может подключаться в любой момент
  2. Whisper — загрузка модели ASR
  3. Piper  — загрузка голоса TTS
  4. Основной цикл: слушать → LLM → говорить → повторить
"""

import time

import asr as asr_module
import bridge
import llm as llm_module
import tts as tts_module


def main() -> None:
    # 1. Запустить WebSocket-сервер до загрузки тяжёлых моделей,
    #    чтобы Godot мог подключиться пока грузится Whisper.
    bridge.start_server()
    time.sleep(0.3)  # дать серверу время занять порт

    # 2. Загрузка моделей
    whisper_model = asr_module.load_whisper()
    piper_voice   = tts_module.load_voice()

    print("\n=== Ника готова. Скажи «Ника» чтобы начать. ===\n")

    while True:
        try:
            # Ждём слово активации
            command = asr_module.listen_for_wake_word(whisper_model)
            if not command:
                continue

            # Режим разговора: отвечаем и ждём продолжения
            while command:
                print(f"[Команда] {command}")

                response = llm_module.ask(command)
                print(f"[Ника] {response}")

                bridge.send_speech_state("talking")
                tts_module.speak(piper_voice, response)
                bridge.send_speech_state("idle")

                # Ждём следующий вопрос без слова активации (10 сек)
                command = asr_module.listen_for_followup(whisper_model, timeout_sec=10)

            # command = None → таймаут, возвращаемся в ожидание активации

        except KeyboardInterrupt:
            print("\n[main] Завершение по Ctrl+C.")
            break
        except Exception as e:
            print(f"[Ошибка] {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
