## Орбитальная камера — вращается вокруг персонажа во время игры.
##
## Подключить: выбрать узел Camera3D → Inspector → Script → этот файл.
## В Inspector назначить target (перетащить узел персонажа).
##
## Управление в игровом режиме:
##   ПКМ + тащить мышь  — вращение вокруг персонажа
##   Колёсико вверх/вниз — приблизить / отдалить

extends Camera3D

## Узел персонажа (перетащить VRM-узел в Inspector)
@export var target: Node3D

## Начальное расстояние от персонажа (метры)
@export var distance: float = 2.0

## Точка прицела — высота над корнем персонажа (голова/грудь)
@export var look_height: float = 1.3

## Чувствительность вращения мышью
@export var sensitivity: float = 0.25

## Скорость зума колёсиком
@export var zoom_speed: float = 0.3

@export var min_distance: float = 0.5
@export var max_distance: float = 6.0

var _yaw:      float = 0.0    # горизонтальный угол
var _pitch:    float = -10.0  # вертикальный угол (отрицательный = немного сверху)
var _dragging: bool  = false


func _ready() -> void:
	# Если target не назначен в Inspector — найти первый VRMTopLevel или Node3D
	if target == null:
		target = get_parent().find_child("*", "Node3D", true, false)
	_update()


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		match event.button_index:
			MOUSE_BUTTON_RIGHT:
				_dragging = event.pressed
			MOUSE_BUTTON_WHEEL_UP:
				distance = clamp(distance - zoom_speed, min_distance, max_distance)
				_update()
			MOUSE_BUTTON_WHEEL_DOWN:
				distance = clamp(distance + zoom_speed, min_distance, max_distance)
				_update()

	elif event is InputEventMouseMotion and _dragging:
		_yaw   -= event.relative.x * sensitivity
		_pitch  = clamp(_pitch - event.relative.y * sensitivity, -75.0, 75.0)
		_update()


func _update() -> void:
	var pivot := Vector3.ZERO
	if target:
		pivot = target.global_position + Vector3(0.0, look_height, 0.0)

	var yaw_r   := deg_to_rad(_yaw)
	var pitch_r := deg_to_rad(_pitch)

	var offset := Vector3(
		cos(pitch_r) * sin(yaw_r),
		sin(pitch_r),
		cos(pitch_r) * cos(yaw_r)
	) * distance

	global_position = pivot + offset
	look_at(pivot, Vector3.UP)
