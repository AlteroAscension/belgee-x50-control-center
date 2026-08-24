# Belgee X50 Control Center agent guide

Home Assistant add-on/Ingress application for the responsive Belgee X50
dashboard: trips, MapKit maps, simulator, diagnostics and update orchestration.
It consumes the compact event contract from the native HA Integration; it does
not own secure pairing, vehicle command policy or direct head-unit transport.

Read `README.md`, `ARCHITECTURE.md`, `ROADMAP.md` and `docs/`. Cross-project
contracts live in `../belgee-x50-ha-integration/`; the supported existing stack
is `../home-assistant/` plus `../x50-simulator-addon/`. Treat both stacks as
parallel until a documented migration changes ownership.

Keep Ingress layouts responsive and test the add-on locally using the commands
defined by its repository manifest. Do not put HA credentials, trip data or
device endpoints into frontend bundles, logs or fixtures.
