"""Pure state projection for the Control Center UI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _value(entity: dict[str, Any], default: Any = None) -> Any:
    value = entity.get("state", default)
    return default if value in (None, "unknown", "unavailable") else value


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def project_states(states: list[dict[str, Any]]) -> dict[str, Any]:
    """Project HA entity states into a stable, small frontend document."""
    by_unique: dict[str, dict[str, Any]] = {}
    by_id = {str(item.get("entity_id")): item for item in states}
    for item in states:
        unique = item.get("attributes", {}).get("unique_id")
        if unique:
            by_unique[str(unique)] = item

    def find(suffix: str, fallback_ids: tuple[str, ...] = ()) -> dict[str, Any]:
        for unique, item in by_unique.items():
            if unique.endswith(suffix):
                return item
        for entity_id in fallback_ids:
            if entity_id in by_id:
                return by_id[entity_id]
        return {}

    speed = find("_vehicle_speed_kmh")
    odometer = find(
        "_vehicle_odometer_km", ("sensor.belgee_x50_x50_odometer",)
    )
    remaining_range = find(
        "_vehicle_range_km", ("sensor.belgee_x50_x50_range",)
    )
    ignition = find("_vehicle_ignition", ("sensor.x50_ignition",))
    tracker = find("_vehicle_location", ("device_tracker.x50_gps",))
    fake_gps = find("_navigation_fake_gps_enabled")
    route_length = find("_navigation_route_length_m")
    route_progress = find("_navigation_route_progress_m")
    gateway = find("_gateway_gateway_online")
    relay = find("_relay_relay_online")
    gateway_version = find("_gateway_gateway_version")
    relay_version = find("_relay_relay_version")

    latitude = tracker.get("attributes", {}).get("latitude")
    longitude = tracker.get("attributes", {}).get("longitude")
    updated_values = [
        item.get("last_updated")
        for item in (speed, odometer, remaining_range, tracker, gateway, relay)
        if item.get("last_updated")
    ]
    return {
        "schema": "belgee-x50.control-center.state.v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "available": bool(updated_values),
        "vehicle": {
            "speed_kmh": _number(_value(speed)),
            "odometer_km": _number(_value(odometer)),
            "range_km": _number(_value(remaining_range)),
            "ignition": _value(ignition),
            "latitude": _number(latitude),
            "longitude": _number(longitude),
        },
        "navigation": {
            "fake_gps": _value(fake_gps),
            "route_length_m": _number(_value(route_length)),
            "route_progress_m": _number(_value(route_progress)),
        },
        "components": {
            "home_assistant": {"online": True},
            "gateway": {
                "online": _value(gateway),
                "version": _value(gateway_version),
            },
            "relay": {
                "online": _value(relay),
                "version": _value(relay_version),
            },
            "navigation": {
                "online": bool(fake_gps or route_length or route_progress),
            },
        },
        "last_updated": max(updated_values) if updated_values else None,
        "entity_count": len(states),
    }
