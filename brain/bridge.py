"""
WebSocket-мост: Python — сервер, Godot подключается как клиент.

Сервер запускается в отдельном daemon-потоке, не блокирует основной цикл.
Из основного кода вызываем send_speech_state() — функция потокобезопасна.

Протокол описан в docs/protocol.md. Этап 1: только speech_state.
"""

import asyncio
import json
import threading
from typing import Optional

import websockets
import websockets.server

import config

# ── внутреннее состояние ──────────────────────────────────────────────────────
_clients: set[websockets.server.ServerConnection] = set()
_loop: Optional[asyncio.AbstractEventLoop] = None


async def _handler(websocket: websockets.server.ServerConnection) -> None:
    addr = websocket.remote_address
    print(f"[Мост] Godot подключился: {addr}")
    _clients.add(websocket)
    try:
        async for _ in websocket:
            pass  # Этап 1: от Godot ничего не ожидаем
    finally:
        _clients.discard(websocket)
        print(f"[Мост] Godot отключился: {addr}")


async def _serve() -> None:
    async with websockets.serve(_handler, config.BRIDGE_HOST, config.BRIDGE_PORT):
        print(f"[Мост] WebSocket сервер ws://{config.BRIDGE_HOST}:{config.BRIDGE_PORT}")
        await asyncio.Future()  # работает бесконечно


def _run_loop() -> None:
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_until_complete(_serve())


def start_server() -> None:
    """Запустить сервер в фоновом daemon-потоке."""
    t = threading.Thread(target=_run_loop, daemon=True, name="bridge-ws")
    t.start()


# ── отправка сообщений из основного потока ────────────────────────────────────

def _send_nowait(payload: str) -> None:
    """Отправить строку всем подключённым клиентам (из основного потока)."""
    if not _loop or not _clients:
        return

    async def _do() -> None:
        dead = set()
        for ws in list(_clients):
            try:
                await ws.send(payload)
            except Exception:
                dead.add(ws)
        _clients.difference_update(dead)

    asyncio.run_coroutine_threadsafe(_do(), _loop)


def send_speech_state(state: str) -> None:
    """
    Отправить состояние речи в Godot.
    state: "talking" | "idle"
    """
    _send_nowait(json.dumps({"type": "speech_state", "state": state}))
