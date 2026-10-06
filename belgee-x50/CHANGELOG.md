# Changelog

## 0.2.1

- Recover retained HA trajectory snapshots after startup and every WebSocket reconnect, subscribing before HTTP backfill.
- Keep completed and newer snapshots when delayed events or backfill arrive out of order; duplicate saves leave files unchanged.
- Continue event delivery with older Integration versions that lack the snapshot-list API.

## 0.1.0

- first runnable Home Assistant Ingress application;
- asynchronous read-only HA state backend;
- responsive overview and component diagnostics;
- live WebSocket updates with reconnect;
- legacy entity fallback for the side-by-side migration period.
