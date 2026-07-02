# Замена аватара: Quaternius FBX → VRoid VRM

Это руководство заменяет раздел 3–5 из `setup-godot.md`.
Цель — поставить персонажа с мимикой: моргание, движение рта, выражения лица.

> **Текущий статус:** Этап 1.5 — идёт замена аватара на VRM.

---

## Часть 1: Получить VRM-персонажа

Есть два пути — выбирай:

### Вариант А — Скачать готового (быстро, ~10 мин)

1. Перейти на <https://hub.vroid.com>
2. Нужен **бесплатный аккаунт Pixiv** (или войти через Google/Twitter)
3. В поиске выбрать фильтр: **Body type: Female/Male**, **License: Allow**
4. Выбрать любую понравившуюся модель → нажать **Download VRM**
5. Файл сохранится как `ИмяМодели.vrm`

> Хороший тестовый вариант — модель "AvatarSample_A" (официальный пример от VRoid):
> <https://hub.vroid.com/en/characters/2843975701063145241/models/5644550250047163651>

### Вариант Б — Создать свою (30 мин–несколько часов)

1. Скачать **VRoid Studio** с <https://vroid.com/en/studio>
   (или в Steam: бесплатно)
2. Установить и запустить
3. Нажать **+ Новый персонаж** → выбрать пол
4. Настроить внешность: форма лица, глаза, волосы, одежда
   (всё интуитивно, ползунки)
5. Нажать **Экспорт** → **Экспортировать как VRM** → сохранить файл

---

## Часть 2: Установить плагин godot-vrm в Godot

### 2.1 Скачать плагин через AssetLib

1. В редакторе Godot открыть вкладку **AssetLib** (вверху, рядом с 2D/3D/Script)
2. В строке поиска написать **vrm**
3. Найти **"VRM"** от **V-Sekai** → нажать **Download**
4. В диалоге нажать **Install**
5. Дождаться установки

**Если в AssetLib не находит** — установить вручную:
1. Перейти на <https://github.com/V-Sekai/godot-vrm>
2. Нажать **Code → Download ZIP**
3. Распаковать → скопировать папку `addons/vrm/` в `C:\Godot\nika-3d\addons\vrm\`

### 2.2 Включить плагин

1. Project → **Project Settings** → вкладка **Plugins**
2. Найти **VRM** → переключить статус на **Enable**
3. Godot перезапустится / обновится

---

## Часть 3: Добавить VRM в сцену Godot

### 3.1 Скопировать файл

Скопировать свой `.vrm` файл в:
```
C:\Godot\nika-3d\assets\character_vrm\ИмяПерсонажа.vrm
```

Папку `character_vrm\` создать если её нет.

### 3.2 Импорт в Godot

1. В FileSystem (снизу слева) нажать правой кнопкой → **Rescan**
2. Найти `.vrm` файл — он появится с иконкой сцены
3. Двойной клик → Godot автоматически импортирует VRM в сцену
   (займёт 5–30 секунд первый раз)
4. Перетащить `.vrm` из FileSystem в 3D-вьюпорт
   — появится 3D-персонаж

### 3.3 Дерево сцены после добавления VRM

```
Main  [Node3D]
  Camera3D
  DirectionalLight3D
  BridgeClient  [Node, bridge_client.gd]
  ИмяПерсонажа  [VRMTopLevel — это корень VRM-сцены]
    Skeleton3D
    Body          [MeshInstance3D]
    Face          [MeshInstance3D ← здесь blend shapes лица]
    Hair          [MeshInstance3D]
    AnimationPlayer
    SpringBoneSimulator3D
```

### 3.4 Удалить старый FBX-персонаж

1. В дереве сцены найти узел `Casual` (старый FBX)
2. Правая кнопка → **Delete**

---

## Часть 4: Подключить новый скрипт

### 4.1 Скопировать скрипт в Godot-проект

Скопировать файл:
```
nika3d/godot_project/scripts/character_controller_vrm.gd
```
в:
```
C:\Godot\nika-3d\assets\scripts\character_controller_vrm.gd
```

### 4.2 Заменить скрипт на Main

1. В дереве сцены выбрать узел **Main**
2. Inspector → поле **Script** → нажать на иконку папки рядом
3. Выбрать `assets/scripts/character_controller_vrm.gd`
4. Старый `character_controller.gd` снимается автоматически

---

## Часть 5: Найти правильные имена blend shapes

Разные VRM-модели могут использовать разные имена для blend shapes.
VRoid Studio использует стандартные имена `Fcl_*`, но не всегда.

### 5.1 Включить отладочный вывод

В скрипте `character_controller_vrm.gd` найти строку:
```gdscript
# _debug_list_blend_shapes()  # раскомментировать если нужно увидеть имена
```
Убрать `#` в начале строки (раскомментировать).

### 5.2 Запустить и посмотреть Output

Нажать **Play (▶)**. В Output появится список:
```
[VRM] Меш лица: 'Face', blend shapes: 58
[VRM] Все blend shapes в 'Face':
  [0] Fcl_EYE_Close_L
  [1] Fcl_EYE_Close_R
  [2] Fcl_MTH_A
  ...
```

### 5.3 Подстроить константы в скрипте

В начале `character_controller_vrm.gd` найти:
```gdscript
const BS_BLINK_L := "Fcl_EYE_Close_L"
const BS_BLINK_R := "Fcl_EYE_Close_R"
const BS_MOUTH_A := "Fcl_MTH_A"
const BS_JOY     := "Fcl_BRW_Fun"
```

Заменить значения на имена из вывода Output.
Типичные альтернативы:

| Что ищем | VRoid Studio | Другие модели |
|----------|-------------|---------------|
| Моргание лево | `Fcl_EYE_Close_L` | `BlinkLeft`, `Blink_L` |
| Моргание право | `Fcl_EYE_Close_R` | `BlinkRight`, `Blink_R` |
| Рот А | `Fcl_MTH_A` | `Aa`, `A`, `mouth_a` |
| Радость | `Fcl_BRW_Fun` | `Joy`, `happy` |

### 5.4 Закомментировать снова

После настройки вернуть `#` перед `_debug_list_blend_shapes()`.

---

## Часть 6: Проверка

### 6.1 Только Godot

Нажать **Play (▶)**. В Output:
```
[VRM] Меш лица: 'Face', blend shapes: 58
[VRM] Анимация: Idle
[VRM] Готов.
```
Персонаж должен периодически моргать.

### 6.2 С Python (полный пайплайн)

1. Запустить `python main.py` в папке `brain/`
2. Запустить Godot (Play ▶)
3. Сказать "Ника" → задать вопрос
4. Во время ответа: рот персонажа должен двигаться
5. После ответа: рот закрыт, персонаж моргает

---

## Следующие шаги

- **Рот:** сейчас синтетическое движение (синусоида). Для реальной синхронизации
  с речью → Этап 2: Rhubarb Lip Sync
- **Эмоции:** LLM будет возвращать тег эмоции → Этап 3: `{"type": "emotion", "name": "joy"}`
- **Голос:** заменить Piper на Kokoro TTS или ElevenLabs для лучшего качества
