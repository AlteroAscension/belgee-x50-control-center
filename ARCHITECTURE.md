# Public architecture

Control Center will provide the full-screen Home Assistant interface and own
long-lived application data that does not belong in entity attributes:

- trips and route revisions;
- maps and navigation diagnostics;
- simulation sessions;
- refueling records;
- user-facing support and maintenance workflows.

```text
Belgee X50 HA Integration
          ↓
Control Center backend
          ↓
Responsive Home Assistant UI
```

The backend owns persistent writes. The browser never connects directly to
Gateway, Relay or Navigation. Home Assistant entities and automation actions
remain available independently of the Control Center page.

The interface is planned for desktop, tablet and phone use. Authentication is
provided through the supported Home Assistant application environment.

Security-sensitive implementation and update details are intentionally
excluded from the public pre-release architecture.
