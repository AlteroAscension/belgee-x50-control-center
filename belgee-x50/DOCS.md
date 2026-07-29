# Belgee X50 Control Center 0.1.0

This experimental preview is read-only. Install the app, start it and use
**Open Web UI** or the **Belgee X50** sidebar item.

The application reads Home Assistant entities through the Supervisor API.
Install the Belgee X50 integration to obtain the full preview state. During the
parallel migration period, odometer, range and GPS can also be read from the
documented legacy entity IDs.

If the header shows **Нет live-данных**, check:

1. the Belgee X50 integration is loaded;
2. Relay has submitted telemetry recently;
3. the app log does not contain an HA API HTTP error.

Vehicle controls, updates, trip persistence and simulator migration are not
enabled in this release.
