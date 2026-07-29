#!/usr/bin/env python3
"""Async read-only Home Assistant Ingress application."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout, WSMsgType, web

from model import project_states

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
HA_API = os.environ.get("X50_HA_API", "http://supervisor/core/api").rstrip("/")
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
REFRESH_SECONDS = max(1, min(30, int(os.environ.get("X50_REFRESH_SECONDS", "2"))))
LOG = logging.getLogger("belgee_x50.control_center")


class StateSource:
    """Fetch and cache Home Assistant state through the Supervisor API."""

    def __init__(self) -> None:
        self.session: ClientSession | None = None
        self.state: dict[str, Any] = project_states([])
        self.error: str | None = "waiting for Home Assistant"

    async def start(self) -> None:
        self.session = ClientSession(timeout=ClientTimeout(total=8))

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def update(self) -> dict[str, Any]:
        assert self.session
        headers = {"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}
        try:
            async with self.session.get(f"{HA_API}/states", headers=headers) as response:
                if response.status != 200:
                    raise RuntimeError(f"Home Assistant returned HTTP {response.status}")
                payload = await response.json()
                if not isinstance(payload, list):
                    raise RuntimeError("Home Assistant state response is not a list")
            self.state = project_states(payload)
            self.error = None
        except (ClientError, asyncio.TimeoutError, RuntimeError, ValueError) as error:
            self.error = str(error)
            self.state = {**self.state, "available": False}
        return {**self.state, "error": self.error}


async def index(_: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC / "index.html")


async def asset(request: web.Request) -> web.FileResponse:
    filename = request.match_info["filename"]
    if filename not in {"app.js", "styles.css"}:
        raise web.HTTPNotFound()
    return web.FileResponse(STATIC / filename)


async def health(request: web.Request) -> web.Response:
    source: StateSource = request.app["source"]
    return web.json_response(
        {
            "status": "ok",
            "service": "belgee-x50-control-center",
            "version": "0.1.0",
            "ha_connected": source.error is None,
            "mode": "read-only",
        }
    )


async def state(request: web.Request) -> web.Response:
    source: StateSource = request.app["source"]
    return web.json_response(await source.update())


async def websocket(request: web.Request) -> web.WebSocketResponse:
    source: StateSource = request.app["source"]
    socket = web.WebSocketResponse(heartbeat=20)
    await socket.prepare(request)
    previous = ""
    try:
        while not socket.closed:
            payload = await source.update()
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(encoded.encode()).hexdigest()
            if digest != previous:
                await socket.send_str(encoded)
                previous = digest
            try:
                message = await asyncio.wait_for(socket.receive(), REFRESH_SECONDS)
                if message.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                    break
            except asyncio.TimeoutError:
                pass
    finally:
        await socket.close()
    return socket


async def create_app() -> web.Application:
    app = web.Application()
    source = StateSource()
    await source.start()
    app["source"] = source
    app.on_cleanup.append(lambda _: source.close())
    app.router.add_get("/", index)
    app.router.add_get("/index.html", index)
    app.router.add_get("/assets/{filename}", asset)
    app.router.add_get("/api/health", health)
    app.router.add_get("/api/state", state)
    app.router.add_get("/api/ws", websocket)
    return app


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    web.run_app(create_app(), host="0.0.0.0", port=8099, print=None)


if __name__ == "__main__":
    main()
