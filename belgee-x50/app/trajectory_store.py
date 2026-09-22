"""Durable, read-only archive of trajectory events emitted by the HA integration."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import re
from typing import Any

from aiohttp import ClientSession, ClientTimeout, WSMsgType


class TrajectoryStore:
    """Persist completed trips and replace snapshots of the active trip."""

    _ID = re.compile(r"^[A-Za-z0-9_.-]{1,160}$")

    def __init__(self, ha_api: str, token: str, root: Path = Path("/data/trajectories")) -> None:
        self.ha_api, self.token, self.root = ha_api, token, root
        self.task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.task = asyncio.create_task(self._listen(), name="x50-trajectory-events")

    async def close(self) -> None:
        if self.task:
            self.task.cancel()
            try: await self.task
            except asyncio.CancelledError: pass

    def list(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            try:
                payload = json.loads(path.read_text("utf-8")); trajectory = payload["trajectory"]
                result.append({"id": payload["snapshot_id"], "complete": bool(payload.get("complete")),
                    "observed_at_ms": payload.get("observed_at_ms"), "started_at_ms": trajectory.get("started_at_ms"),
                    "ended_at_ms": trajectory.get("ended_at_ms"), "point_count": len(trajectory.get("points", [])),
                    "segment_count": trajectory.get("segment_count", 1), "distance_m": trajectory.get("distance_m", 0)})
            except (OSError, ValueError, KeyError, TypeError): pass
        return result

    def get(self, trajectory_id: str) -> dict[str, Any] | None:
        if not self._ID.fullmatch(trajectory_id): return None
        try: return json.loads((self.root / f"{trajectory_id}.json").read_text("utf-8"))
        except (OSError, ValueError): return None

    def save(self, event: dict[str, Any]) -> None:
        trajectory_id, trajectory = str(event.get("snapshot_id") or ""), event.get("trajectory")
        if not self._ID.fullmatch(trajectory_id) or not isinstance(trajectory, dict): return
        if not isinstance(trajectory.get("points"), list) or len(trajectory["points"]) > 10_000: return
        path = self.root / f"{trajectory_id}.json"; temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(event, ensure_ascii=False, separators=(",", ":")), "utf-8")
        os.replace(temp, path)

    async def _listen(self) -> None:
        url = self.ha_api.replace("http://", "ws://", 1).replace("https://", "wss://", 1)
        if url.endswith("/api"): url += "/websocket"
        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.ws_connect(url, heartbeat=20) as ws:
                        await ws.receive_json(); await ws.send_json({"type": "auth", "access_token": self.token})
                        if (await ws.receive_json()).get("type") != "auth_ok": raise RuntimeError("HA websocket auth failed")
                        await ws.send_json({"id": 1, "type": "subscribe_events", "event_type": "belgee_x50_trajectory_snapshot"})
                        async for message in ws:
                            if message.type != WSMsgType.TEXT: break
                            payload = json.loads(message.data); event = payload.get("event", {})
                            if payload.get("type") == "event" and isinstance(event.get("data"), dict): self.save(event["data"])
            except asyncio.CancelledError: raise
            except Exception: await asyncio.sleep(5)
