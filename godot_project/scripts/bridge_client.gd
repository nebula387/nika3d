## Подключается к Python-серверу по WebSocket и раздаёт сообщения
## остальным узлам через сигнал speech_state_changed.
##
## Python — сервер, Godot — клиент.
## При обрыве соединения автоматически переподключается каждые 2 секунды.

extends Node

signal speech_state_changed(state: String)

const WS_URL := "ws://127.0.0.1:8765"

var _socket  := WebSocketPeer.new()
var _was_open := false


func _ready() -> void:
	_connect()


func _connect() -> void:
	_socket = WebSocketPeer.new()
	var err := _socket.connect_to_url(WS_URL)
	if err != OK:
		push_error("[Мост] Не удалось подключиться: код %d" % err)


func _process(_delta: float) -> void:
	_socket.poll()

	match _socket.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			if not _was_open:
				_was_open = true
				print("[Мост] Подключено к Python-серверу.")
			_read_packets()

		WebSocketPeer.STATE_CLOSED:
			if _was_open:
				_was_open = false
				print("[Мост] Соединение разорвано, переподключение через 2 с...")
				await get_tree().create_timer(2.0).timeout
				_connect()


func _read_packets() -> void:
	while _socket.get_available_packet_count() > 0:
		var raw := _socket.get_packet().get_string_from_utf8()
		_handle(raw)


func _handle(raw: String) -> void:
	var json := JSON.new()
	if json.parse(raw) != OK:
		push_warning("[Мост] Некорректный JSON: " + raw)
		return

	var msg: Dictionary = json.get_data()
	match msg.get("type", ""):
		"speech_state":
			speech_state_changed.emit(msg.get("state", "idle"))
		_:
			push_warning("[Мост] Неизвестный тип сообщения: " + str(msg))
