# Belgee X50 Control Center app

Version `0.1.0` is the first runnable, read-only Home Assistant Ingress shell.
It reads entity state through the Supervisor-provided Home Assistant API token,
never connects to Relay/Gateway directly and exposes no vehicle commands.

The overview supports both the new `belgee_x50` integration unique IDs and the
small legacy fallback required for side-by-side migration. Trips, maps and the
simulator are intentionally marked as subsequent stages rather than presenting
non-functional controls.

Endpoints:

- `GET /api/health` — container and HA connectivity;
- `GET /api/state` — compact projected state;
- `GET /api/ws` — live read-only WebSocket updates.
