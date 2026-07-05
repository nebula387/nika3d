## Управляет VRM-персонажем (VRoid Studio → .vrm → Godot через плагин godot-vrm).
##
## Функции:
##   - Авто-моргание каждые 2.5–6 сек
##   - speech_state=talking → рот открывается (синус-волна на blend shape Aa)
##   - speech_state=idle   → нейтральное выражение, рот закрыт
##   - Поддержка emotion=joy/sad/angry (опционально, из будущего этапа LLM)
##
## Подключение:
##   1. Выбрать узел Main → Inspector → Script → этот файл
##   2. BridgeClient должен быть дочерним узлом Main
##   3. VRM-персонаж должен быть дочерним узлом Main (любое имя)
##
## Если blend shapes не находятся — проверь BLEND_SHAPE_* константы ниже
## и подстрой под имена в своей модели (они видны в Godot в ImportPreview).

extends Node

# ── Настройка blend shapes ─────────────────────────────────────────────────
# Стандарт VRM 0.x (VRoid Studio): именно такие имена
# Если модель не отвечает — проверь через скрипт _debug_list_blend_shapes()
const BS_BLINK_L  := "Fcl_EYE_Close_L"   # закрыть левый глаз
const BS_BLINK_R  := "Fcl_EYE_Close_R"   # закрыть правый глаз
const BS_MOUTH_A  := "Fcl_MTH_A"         # рот открыт (звук А)
const BS_JOY      := "Fcl_BRW_Fun"       # подтянуть брови (радость)
const BS_ANGRY    := "Fcl_BRW_Angry"     # сдвинуть брови (злость)

# Запасные имена (более ранние VRoid / другие редакторы):
# BlinkLeft / BlinkRight / Aa / Joy — раскомментировать если основные не работают
# const BS_BLINK_L := "BlinkLeft"
# const BS_BLINK_R := "BlinkRight"
# const BS_MOUTH_A := "Aa"
# const BS_JOY     := "Joy"

# ── Параметры моргания ─────────────────────────────────────────────────────
const BLINK_SPEED := 10.0      # скорость закрытия/открытия глаз (ед/сек)
const BLINK_MIN   := 2.5       # мин. пауза между морганиями (сек)
const BLINK_MAX   := 6.0       # макс. пауза

# ── Параметры рта ──────────────────────────────────────────────────────────
const MOUTH_SPEED  := 7.0      # скорость колебаний рта при разговоре
const MOUTH_MAX    := 0.55     # насколько широко открывается рот (0.0–1.0)

# ── Внутреннее состояние ───────────────────────────────────────────────────
var _bridge:    Node
var _anim:      AnimationPlayer
var _face_mesh: MeshInstance3D  # меш с blend shapes лица

var _talking:        bool  = false
var _blink_timer:    float = 0.0
var _next_blink:     float = 3.0
var _blink_value:    float = 0.0   # 0=открыто, 1=закрыто
var _blink_closing:  bool  = false
var _mouth_phase:    float = 0.0

# Кэш: имя blend shape → индекс (заполняется один раз в _ready)
var _bs_cache: Dictionary = {}


func _ready() -> void:
	randomize()

	# Мост
	_bridge = get_node_or_null("BridgeClient")
	if _bridge == null:
		push_error("[VRM] BridgeClient не найден — добавь дочерний узел BridgeClient")
		return
	_bridge.speech_state_changed.connect(_on_speech_state)
	# Если в будущем добавим emotion-сообщения в bridge_client.gd:
	# if _bridge.has_signal("emotion_changed"):
	#     _bridge.emotion_changed.connect(_on_emotion)

	# AnimationPlayer для тела (Idle, Wave и т.д.)
	_anim = find_child("AnimationPlayer", true, false)

	# Меш лица — ищем MeshInstance с наибольшим числом blend shapes
	_face_mesh = _find_face_mesh()
	if _face_mesh:
		_build_bs_cache()
		print("[VRM] Меш лица: '%s', blend shapes: %d" % [
			_face_mesh.name, _face_mesh.mesh.get_blend_shape_count()])
		_debug_list_blend_shapes()  # выводим все имена чтобы подстроить константы
	else:
		push_warning("[VRM] Меш с blend shapes не найден — мимика недоступна")

	# Запустить Idle-анимацию
	if _anim:
		var idle_name := _pick_animation(_anim, ["Idle", "idle", "IDLE", "Stand", "T-Pose"])
		if idle_name != "":
			_anim.play(idle_name)
			print("[VRM] Анимация: " + idle_name)

	_next_blink = randf_range(BLINK_MIN, BLINK_MAX)
	print("[VRM] Готов.")


func _process(delta: float) -> void:
	_tick_blink(delta)
	if _talking:
		_tick_mouth(delta)


# ── Обработчики состояний ──────────────────────────────────────────────────

func _on_speech_state(state: String) -> void:
	match state:
		"talking":
			_talking = true
			_set_bs(BS_JOY, 0.25)
		"idle":
			_talking = false
			_mouth_phase = 0.0
			_set_bs(BS_MOUTH_A, 0.0)
			_set_bs(BS_JOY,     0.0)
		_:
			push_warning("[VRM] Неизвестное состояние: " + state)


# Для будущего этапа: LLM шлёт {"type": "emotion", "name": "joy"}
func _on_emotion(emotion: String) -> void:
	_set_bs(BS_JOY,   0.0)
	_set_bs(BS_ANGRY, 0.0)
	match emotion:
		"joy":     _set_bs(BS_JOY,   0.8)
		"angry":   _set_bs(BS_ANGRY, 0.8)


# ── Моргание ───────────────────────────────────────────────────────────────

func _tick_blink(delta: float) -> void:
	if not _blink_closing:
		_blink_timer += delta
		if _blink_timer >= _next_blink:
			_blink_closing = true
			_blink_timer = 0.0
	else:
		# Закрыть глаза
		_blink_value = min(_blink_value + delta * BLINK_SPEED, 1.0)
		_set_bs(BS_BLINK_L, _blink_value)
		_set_bs(BS_BLINK_R, _blink_value)
		if _blink_value >= 1.0:
			# Открыть глаза
			_blink_value = 0.0
			_set_bs(BS_BLINK_L, 0.0)
			_set_bs(BS_BLINK_R, 0.0)
			_blink_closing = false
			_next_blink = randf_range(BLINK_MIN, BLINK_MAX)


# ── Рот при разговоре ──────────────────────────────────────────────────────

func _tick_mouth(delta: float) -> void:
	_mouth_phase += delta * MOUTH_SPEED
	var w := (sin(_mouth_phase) * 0.5 + 0.5) * MOUTH_MAX
	_set_bs(BS_MOUTH_A, w)


# ── Вспомогательные ───────────────────────────────────────────────────────

func _build_bs_cache() -> void:
	_bs_cache.clear()
	if _face_mesh == null or _face_mesh.mesh == null:
		return
	var count: int = _face_mesh.mesh.get_blend_shape_count()
	for i in count:
		var bs_name: String = _face_mesh.mesh.get_blend_shape_name(i)
		_bs_cache[bs_name] = i


func _set_bs(bs_name: String, value: float) -> void:
	if _face_mesh == null or not _bs_cache.has(bs_name):
		return
	_face_mesh.set_blend_shape_value(_bs_cache[bs_name], value)


func _find_face_mesh() -> MeshInstance3D:
	var best: MeshInstance3D
	var best_count: int = 0
	for node in find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = node as MeshInstance3D
		if mi and mi.mesh:
			var n: int = mi.mesh.get_blend_shape_count()
			if n > best_count:
				best_count = n
				best = mi
	return best


func _pick_animation(anim: AnimationPlayer, names: Array) -> String:
	for anim_name in names:
		if anim.has_animation(anim_name):
			return anim_name
	var list: Array = anim.get_animation_list()
	return list[0] if list.size() > 0 else ""


func _debug_list_blend_shapes() -> void:
	if _face_mesh == null:
		return
	print("[VRM] Все blend shapes в '%s':" % _face_mesh.name)
	for bs_name in _bs_cache:
		print("  [%d] %s" % [_bs_cache[bs_name], bs_name])
