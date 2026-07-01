## Управляет анимациями персонажа на основе команд от BridgeClient.
## AnimationPlayer и BridgeClient ищутся автоматически — ничего
## перетаскивать в Inspector не нужно.
##
## Подключить скрипт: выбрать узел Main → Inspector → Script → Load → этот файл.
## BridgeClient должен быть дочерним узлом Main с именем "BridgeClient".
## AnimationPlayer ищется рекурсивно внутри FBX-сцены.

extends Node3D

const ANIM_IDLE    := "CharacterArmature|Idle"
const ANIM_TALKING := "CharacterArmature|Wave"

var _anim: AnimationPlayer
var _bridge: Node


func _ready() -> void:
	# BridgeClient — прямой потомок того же узла (Main)
	_bridge = get_node_or_null("BridgeClient")
	if _bridge == null:
		push_error("[Персонаж] BridgeClient не найден — убедись что он дочерний узел Main")
		return
	_bridge.speech_state_changed.connect(_on_speech_state)

	# AnimationPlayer — внутри импортированной FBX-сцены, ищем рекурсивно
	_anim = find_child("AnimationPlayer", true, false)
	if _anim == null:
		push_error("[Персонаж] AnimationPlayer не найден в сцене")
		return

	_play(ANIM_IDLE)
	print("[Персонаж] Готов. Idle запущен.")


func _on_speech_state(state: String) -> void:
	match state:
		"talking": _play(ANIM_TALKING)
		"idle":    _play(ANIM_IDLE)
		_: push_warning("[Персонаж] Неизвестное состояние: " + state)


func _play(anim_name: String) -> void:
	if _anim == null:
		return
	if not _anim.has_animation(anim_name):
		push_warning("[Персонаж] Анимация не найдена: '%s'" % anim_name)
		return
	if _anim.current_animation != anim_name:
		_anim.play(anim_name)
