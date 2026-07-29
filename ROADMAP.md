# Public roadmap

## 1. Product shell

- [x] responsive navigation;
- [x] shared visual language;
- [x] live-capable vehicle overview;
- [x] desktop, tablet and phone breakpoints;
- [ ] visual validation in Home Assistant Ingress on all three sizes.

## 2. Read-only live state

- [x] read-only Home Assistant state adapter;
- [x] overview and device status;
- [x] WebSocket reconnect and compatibility feedback;
- [ ] direct versioned Integration → Control Center event transport;
- [ ] route snapshot replay after backend restart.

## 3. Trips and maps

- separate real-head-unit and simulator sessions;
- route revisions;
- GPS/FakeGPS/correction visualization;
- export and retention controls.

## 4. Simulator

- migrate the verified simulator capabilities;
- AVD connection;
- route and metadata inspection;
- regression tests against the supported legacy add-on.

## 5. Controls and maintenance

- role-aware vehicle controls;
- clear command progress and results;
- diagnostics and supported update workflows.

## 6. Migration and stable release

- import from the current simulator;
- side-by-side validation;
- installation, backup, upgrade and rollback documentation.

Milestones may change while the project remains pre-release.
