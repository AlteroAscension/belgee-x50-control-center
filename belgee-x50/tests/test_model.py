from __future__ import annotations

import sys
from pathlib import Path
import unittest

APP = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP))
from model import project_states


def entity(entity_id, state, unique_id=None, **attributes):
    if unique_id:
        attributes["unique_id"] = unique_id
    return {
        "entity_id": entity_id,
        "state": str(state),
        "attributes": attributes,
        "last_updated": "2026-07-29T12:00:00+00:00",
    }


class StateProjectionTest(unittest.TestCase):
    def test_projects_new_integration_entities(self):
        result = project_states([
            entity("sensor.any", 53.4, "car_vehicle_speed_kmh"),
            entity("sensor.any2", 26175.4, "car_vehicle_odometer_km"),
            entity("sensor.any3", 412, "car_vehicle_range_km"),
            entity("binary_sensor.any", "on", "car_navigation_fake_gps_enabled"),
            entity(
                "device_tracker.any", "home", "car_vehicle_location",
                latitude=55.7, longitude=37.5
            ),
        ])
        self.assertTrue(result["available"])
        self.assertEqual(53.4, result["vehicle"]["speed_kmh"])
        self.assertEqual(55.7, result["vehicle"]["latitude"])
        self.assertEqual("on", result["navigation"]["fake_gps"])

    def test_legacy_fallback_keeps_parallel_period_visible(self):
        result = project_states([
            entity("sensor.belgee_x50_x50_odometer", 26000),
            entity("sensor.belgee_x50_x50_range", 300),
            entity("device_tracker.x50_gps", "not_home", latitude=55.0, longitude=37.0),
        ])
        self.assertEqual(26000, result["vehicle"]["odometer_km"])
        self.assertEqual(300, result["vehicle"]["range_km"])

    def test_empty_state_is_explicitly_offline(self):
        result = project_states([])
        self.assertFalse(result["available"])
        self.assertEqual(0, result["entity_count"])


if __name__ == "__main__":
    unittest.main()
