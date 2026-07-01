# Установка Godot и настройка сцены с нуля

Это ручные шаги вне кода. Claude Code должен сверяться с этим файлом
и обновлять его, если в процессе работы конкретные шаги или версии изменились.

> **Текущий статус:** Этап 1 выполнен. Проект работает — персонаж переключает
> анимации по голосовым командам через WebSocket.

## 1. Установка Godot

1. Перейти на https://godotengine.org/download
2. Скачать **последнюю стабильную Godot 4.x, версия Standard** (НЕ .NET-версию
   — она требует .NET SDK, нам не нужна, мы работаем на GDScript)
3. Распаковать архив, например в `C:\Godot\`
4. Запустить `Godot_v4.x-stable_win64.exe` — откроется Project Manager

## 2. Создание проекта

1. В Project Manager → **New Project**
2. Указать путь: например `C:\Godot\nika-3d`
3. Renderer: **Forward Mobile** (для Intel Arc A580 — Mobile легче чем Forward+)
4. Нажать **Create & Edit**

   > Фактический рабочий проект находится в `C:\Godot\nika-3d\`
   > (не в `nika3d/godot_project/` — папка в репозитории содержит
   > шаблоны скриптов, а живой проект создаётся отдельно).

## 3. Получение 3D-модели персонажа (Quaternius)

Mixamo (mixamo.com) может быть недоступен. Используем **Quaternius** — бесплатный
пак моделей с CC0 лицензией, не требует аккаунта.

1. Перейти на <https://quaternius.com> → раздел **Animated Characters**
2. Скачать пак **Ultimate Animated Characters Pack** или аналогичный
   с надписью **"animated"** / **"animation"** в названии.

   > **Важно:** Паки с "Characters" в названии (без animation) содержат
   > только статичные mesh-файлы без анимаций — они не подходят.
   > Нужен пак с анимациями в самих FBX-файлах.

3. Распаковать архив. Найти папку `Individual Characters/FBX/`
4. Выбрать любой персонаж, например `Casual.fbx`

   Этот файл содержит готовый риггед-персонаж со встроенными анимациями:
   - `CharacterArmature|Idle` — стоит спокойно
   - `CharacterArmature|Wave` — машет рукой (используем как "говорит")
   - и ещё 20+ других анимаций

## 4. Структура папок в Godot-проекте

```
C:\Godot\nika-3d\
  project.godot
  bridge_client.gd          ← скрипт WebSocket клиента (у корня проекта)
  icon.svg
  main.tscn                 ← главная сцена
  assets\
    scripts\
      character_controller.gd   ← скрипт управления анимациями
    character_final\
      Casual.fbx                ← 3D-персонаж с анимациями
```

## 5. Импорт персонажа и настройка сцены

### 5.1 Копирование файлов

1. Создать папку `C:\Godot\nika-3d\assets\character_final\`
2. Скопировать туда `Casual.fbx`
3. Открыть Godot — в FileSystem (снизу) правая кнопка → **Rescan** или
   просто подождать — файл появится автоматически

   > **Важно:** Если скачал другие варианты паков (с .blend файлами)
   > и они вызывают ошибки/краш — создай в той папке файл `.gdignore`
   > (пустой файл с таким именем). Godot пропустит всё содержимое папки.
   > После этого удали папку `.godot/` в корне проекта и перезапусти Godot.

### 5.2 Добавление персонажа в сцену

1. В FileSystem найти `Casual.fbx`
2. Перетащить его в 3D-вьюпорт — появится персонаж
3. В Scene-дереве появится узел `Casual` со скелетом внутри

### 5.3 Узлы сцены (дерево Main)

```
Main  [Node3D, скрипт: character_controller.gd]
  Camera3D
  DirectionalLight3D
  BridgeClient  [Node, скрипт: bridge_client.gd]
  Casual        [Node3D, импортированный FBX-персонаж]
    Skeleton3D
      ...кости...
    AnimationPlayer   ← находится здесь (Godot 4 импортирует FBX так)
```

### 5.4 Подключение скриптов

**bridge_client.gd:**
1. Скопировать содержимое `nika3d/godot_project/scripts/bridge_client.gd`
   в файл `C:\Godot\nika-3d\bridge_client.gd`
2. В FileSystem нажать на `bridge_client.gd` → он должен открыться в редакторе
3. Выбрать узел `BridgeClient` в Scene → Inspector → Script → выбрать `bridge_client.gd`

**character_controller.gd:**
1. Скопировать содержимое `nika3d/godot_project/scripts/character_controller.gd`
   в `C:\Godot\nika-3d\assets\scripts\character_controller.gd`
2. Выбрать узел `Main` → Inspector → Script → выбрать `character_controller.gd`
3. **Inspector ничего настраивать не нужно** — AnimationPlayer и BridgeClient
   ищутся автоматически в коде через `find_child()` и `get_node_or_null()`.

   > Причина: FBX-сцена импортируется Godot как read-only, поэтому
   > перетащить AnimationPlayer в Inspector через GUI нельзя.
   > Скрипт находит его сам через `find_child("AnimationPlayer", true, false)`.

## 6. Проверка без Python (только Godot)

1. Нажать **Play (▶)** вверху Godot
2. В Output (снизу) должно появиться:
   ```
   [Персонаж] Готов. Idle запущен.
   ```
3. Персонаж стоит в Idle-позе — значит анимации работают

## 7. Полная проверка (Python + Godot вместе)

1. Запустить Python: `cd C:\AI_projects\Avatar_3D\nika3d\brain && python main.py`
2. Запустить Godot (Play ▶)
3. В Godot Output должно появиться:
   ```
   [Мост] Подключено к Python-серверу.
   ```
4. Сказать "Ника" → задать вопрос → персонаж должен переключиться
   в анимацию Wave (условный "говорит") пока Piper читает ответ,
   затем вернуться в Idle

## 8. Перенос проекта на другой ПК

Можно перенести проект целиком:
- Скопировать папку `C:\Godot\nika-3d\` (Godot-проект)
- Скопировать папку `C:\AI_projects\Avatar_3D\nika3d\brain\` (Python-мозг)
- На новом ПК установить Godot и Python зависимости (`pip install -r requirements.txt`)
- Обновить пути в `.env` (PIPER_VOICE_PATH и другие)
- Открыть проект в Godot через Project Manager → Import → указать `project.godot`
