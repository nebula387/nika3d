"""
Точка входа Python-части (brain).

Запуск:
    python main.py

Порядок инициализации:
  1. WebSocket-сервер (фоновый поток) — Godot может подключаться в любой момент
  2. Whisper — загрузка модели ASR
  3. TTS — загрузка голоса (Piper) или None (ElevenLabs)
  4. Основной цикл: слушать → LLM → говорить → действие → повторить
"""

import time

import actions
import asr as asr_module
import bridge
import llm as llm_module
import tts as tts_module


def main() -> None:
    # 1. WebSocket-сервер
    bridge.start_server()
    time.sleep(0.3)

    # 2. Загрузка моделей
    whisper_model = asr_module.load_whisper()
    tts_voice     = tts_module.load_voice()

    print("\n=== Ника готова. Скажи «Ника» чтобы начать. ===\n")

    while True:
        try:
            command = asr_module.listen_for_wake_word(whisper_model)
            if not command:
                continue

            while command:
                print(f"[Команда] {command}")

                reply, action = llm_module.ask(command)

                # Защита: если reply пустой или это сырой JSON — не говорим мусор
                if not reply or reply.strip().startswith("{"):
                    reply = "Sorry, I had a little glitch. Could you say that again?"

                print(f"[Ника] {reply}")
                if action:
                    print(f"[Действие] {action}")

                # Сначала говорим
                bridge.send_speech_state("talking")
                tts_module.speak(tts_voice, reply)
                bridge.send_speech_state("idle")

                # Потом выполняем действие на ПК (после озвучки)
                if action:
                    actions.execute(action)

                command = asr_module.listen_for_followup(whisper_model, timeout_sec=10)

        except KeyboardInterrupt:
            print("\n[main] Завершение по Ctrl+C.")
            break
        except Exception as e:
            print(f"[Ошибка] {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
