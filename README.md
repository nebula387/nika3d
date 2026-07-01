# Nika 3D

Голосовой 3D-компаньон. Python обрабатывает речь и диалог, Godot
рендерит 3D-персонажа и анимации.

## С чего начать

1. Прочитать `CLAUDE.md` — полная архитектура и план по этапам
2. Прочитать `docs/setup-godot.md` — установка Godot перед первым запуском
3. Открыть эту папку как проект в Claude Code
4. Отправить текст из `docs/START_HERE.md` как первое сообщение

## Структура

- `CLAUDE.md` — инструкции для Claude Code (контекст, архитектура, правила)
- `docs/protocol.md` — формат сообщений между Python и Godot
- `docs/setup-godot.md` — установка Godot, импорт модели
- `docs/START_HERE.md` — стартовый промпт для Claude Code
- `brain/` — Python-часть (мозг)
- `godot_project/` — Godot-часть (тело)
