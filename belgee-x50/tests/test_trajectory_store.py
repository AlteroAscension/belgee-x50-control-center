from pathlib import Path
import asyncio
import sys
import tempfile
import unittest

from aiohttp import ClientSession, web

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from trajectory_store import TrajectoryStore


def snapshot(at, complete=False):
    return {"snapshot_id": "fixture-trip", "complete": complete, "observed_at_ms": at,
            "trajectory": {"points": [{"x_m": at, "y_m": 0}]}}


class StoreTest(unittest.IsolatedAsyncioTestCase):
    async def test_actual_listener_backfills_after_reconnect(self):
        with tempfile.TemporaryDirectory() as directory:
            recovered=asyncio.Event(); connections=0; subscription_ready=False; first_socket=None
            async def socket(request):
                nonlocal connections, subscription_ready, first_socket
                ws=web.WebSocketResponse(); await ws.prepare(request)
                await ws.send_json({"type": "auth_required"})
                self.assertEqual("fixture-token", (await ws.receive_json())["access_token"])
                await ws.send_json({"type": "auth_ok"})
                self.assertEqual("subscribe_events", (await ws.receive_json())["type"])
                connections+=1; subscription_ready=True
                if connections==1: first_socket=ws
                await ws.send_json({"id": 1, "type": "result", "success": True})
                async for _ in ws: pass
                return ws
            async def listing(request):
                self.assertTrue(subscription_ready)
                return web.json_response({"trajectories": [{"snapshot_id": "fixture-trip",
                    "complete": True, "observed_at_ms": connections*100}]})
            async def detail(request):
                result=web.json_response(snapshot(connections*100, True))
                if connections==1:
                    asyncio.get_running_loop().call_later(.05, lambda: asyncio.create_task(first_socket.close()))
                else:
                    asyncio.get_running_loop().call_later(.05, recovered.set)
                return result
            app=web.Application(); app.router.add_get("/api/websocket", socket)
            app.router.add_get("/api/belgee_x50/trajectories", listing)
            app.router.add_get("/api/belgee_x50/trajectories/{id}", detail)
            runner=web.AppRunner(app); await runner.setup()
            site=web.TCPSite(runner, "127.0.0.1", 0); await site.start()
            api=f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}/api"
            store=TrajectoryStore(api, "fixture-token", Path(directory))
            try:
                await store.start(); await asyncio.wait_for(recovered.wait(), 9)
                self.assertEqual(200, store.get("fixture-trip")["observed_at_ms"])
                self.assertEqual(2, connections)
            finally:
                await store.close(); await runner.cleanup()

    async def test_reordered_archive_and_reconnect_backfill(self):
        with tempfile.TemporaryDirectory() as directory:
            store = TrajectoryStore("unused", "fixture-token", Path(directory))
            self.assertTrue(store.save(snapshot(200)))
            self.assertFalse(store.save(snapshot(100)))
            self.assertTrue(store.save(snapshot(150, True)))
            self.assertFalse(store.save(snapshot(500)))
            self.assertFalse(store.save(snapshot(150, True)))
            self.assertEqual(150, store.get("fixture-trip")["observed_at_ms"])
            calls=[]
            async def listing(request):
                self.assertEqual("Bearer fixture-token", request.headers["Authorization"])
                calls.append("list")
                return web.json_response({"trajectories": [{"snapshot_id": "fixture-trip",
                    "complete": True, "observed_at_ms": 300}]})
            async def detail(request):
                calls.append("detail")
                return web.json_response(snapshot(300, True))
            app=web.Application()
            app.router.add_get("/api/belgee_x50/trajectories", listing)
            app.router.add_get("/api/belgee_x50/trajectories/{id}", detail)
            runner=web.AppRunner(app); await runner.setup()
            site=web.TCPSite(runner, "127.0.0.1", 0); await site.start()
            store.ha_api=f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}/api"
            try:
                async with ClientSession() as session:
                    await store.sync_retained(session)
                    await store.sync_retained(session)
                self.assertEqual(["list", "detail", "list"], calls)
                self.assertEqual(300, store.get("fixture-trip")["observed_at_ms"])
            finally: await runner.cleanup()
