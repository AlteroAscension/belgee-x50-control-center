# Belgee X50 Control Center

Responsive Home Assistant application for Belgee X50 / Geely Coolray.

Open source under the [MIT License](LICENSE).

Version `0.1.0` is the first runnable, read-only Ingress preview. It contains:

- responsive desktop/tablet/phone navigation;
- live vehicle overview;
- Gateway, Relay, Navigation and HA connection state;
- reconnection through a read-only WebSocket;
- compatibility with new Integration IDs and selected legacy entities;
- explicit placeholders for navigation, trips and simulator migration.

Home Assistant devices, entities and automation actions belong to
[Belgee X50 HA Integration](https://github.com/AlteroAscension/belgee-x50-ha-integration).
The current supported simulator remains available in
[x50-simulator-addon](https://github.com/AlteroAscension/x50-simulator-addon).

## Project documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — public product boundaries;
- [ROADMAP.md](ROADMAP.md) — public development milestones.

Detailed storage, security, update and migration designs are reviewed privately
until they become stable public contracts.

## Install the preview

Add this GitHub repository to the Home Assistant app/add-on store as a custom
repository, install **Belgee X50 Control Center** and open its Ingress panel.
The preview requests only `homeassistant_api`; it does not use host networking,
privileged mode or direct Relay/Gateway access.

Local domain tests:

```bash
python -m unittest discover -s belgee-x50/tests -v
python -m compileall -q belgee-x50/app belgee-x50/tests
```

## Safety boundary

The preview is intentionally read-only. Pages that would require persistent
trip storage or vehicle commands are visibly marked as future stages. The
existing simulator remains the supported test tool until its migration tests
pass.
