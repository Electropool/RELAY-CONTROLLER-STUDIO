"""
test_all.py
================================================================================
Comprehensive test suite verifying core business logic, validation rules,
JSON serialization, firmware configuration rewriting, board detection,
and settings persistence for Relay Controller Studio.
================================================================================
"""

import os
import sys
import unittest
from pathlib import Path

# Add src/ to python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.models import RelayConfiguration, RelayObject, BoardInfo
from core.validation_manager import ValidationManager
from core.firmware_manager import FirmwareCatalog, FirmwareConfigurator
from core.board_detector import BoardDetector
from core.settings_manager import SettingsManager, AppSettings
from core.constants import BOARD_ARDUINO, BOARD_ESP32


class TestRelayModels(unittest.TestCase):
    def test_relay_object_defaults_and_serialization(self):
        r = RelayObject(relay_number=0, enabled=True, start_time=5, stop_time=15)
        self.assertEqual(r.display_name, "Relay1")
        data = r.to_dict()
        self.assertEqual(data["relay_number"], 0)
        self.assertEqual(data["enabled"], True)
        self.assertEqual(data["start_time"], 5)
        self.assertEqual(data["stop_time"], 15)

        r2 = RelayObject.from_dict(data)
        self.assertEqual(r2.relay_number, 0)
        self.assertEqual(r2.enabled, True)
        self.assertEqual(r2.start_time, 5)
        self.assertEqual(r2.stop_time, 15)

    def test_relay_configuration_json_roundtrip(self):
        config = RelayConfiguration.create_default(BOARD_ARDUINO, 4)
        config.loop_time = 120
        config.display_brightness = 10
        config.relay_active_low = False
        config.countdown_enable = True
        config.relay_list[0].start_time = 10
        config.relay_list[0].stop_time = 50

        json_str = config.to_json()
        loaded = RelayConfiguration.from_json(json_str)

        self.assertEqual(loaded.board_type, BOARD_ARDUINO)
        self.assertEqual(loaded.firmware_type, 4)
        self.assertEqual(loaded.loop_time, 120)
        self.assertEqual(loaded.display_brightness, 10)
        self.assertEqual(loaded.relay_active_low, False)
        self.assertEqual(loaded.countdown_enable, True)
        self.assertEqual(len(loaded.relay_list), 4)
        self.assertEqual(loaded.relay_list[0].start_time, 10)
        self.assertEqual(loaded.relay_list[0].stop_time, 50)


class TestValidationManager(unittest.TestCase):
    def setUp(self):
        self.validator = ValidationManager()

    def test_valid_configuration(self):
        config = RelayConfiguration.create_default(BOARD_ARDUINO, 2)
        config.loop_time = 60
        config.relay_list[0].start_time = 5
        config.relay_list[0].stop_time = 25
        config.relay_list[1].start_time = 30
        config.relay_list[1].stop_time = 55

        res = self.validator.validate(config)
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.errors), 0)

    def test_disabled_relay_0_0_is_valid(self):
        config = RelayConfiguration.create_default(BOARD_ARDUINO, 2)
        config.relay_list[0].start_time = 0
        config.relay_list[0].stop_time = 0
        config.relay_list[0].enabled = False

        res = self.validator.validate(config)
        self.assertTrue(res.is_valid)

    def test_invalid_loop_time(self):
        config = RelayConfiguration.create_default(BOARD_ARDUINO, 2)
        config.loop_time = 0
        res = self.validator.validate(config)
        self.assertFalse(res.is_valid)
        self.assertTrue(any(e.field == "loop_time" for e in res.errors))

    def test_start_greater_than_stop(self):
        config = RelayConfiguration.create_default(BOARD_ARDUINO, 2)
        config.loop_time = 60
        config.relay_list[0].start_time = 40
        config.relay_list[0].stop_time = 10

        res = self.validator.validate(config)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("relay_0_start" in e.field for e in res.errors))

    def test_stop_exceeds_loop_time(self):
        config = RelayConfiguration.create_default(BOARD_ARDUINO, 2)
        config.loop_time = 30
        config.relay_list[0].start_time = 5
        config.relay_list[0].stop_time = 45

        res = self.validator.validate(config)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("relay_0_stop" in e.field for e in res.errors))


class TestFirmwareManager(unittest.TestCase):
    def test_firmware_catalog_discovery(self):
        catalog = FirmwareCatalog()
        uno_counts = catalog.available_channel_counts(BOARD_ARDUINO)
        self.assertIn(2, uno_counts)
        self.assertIn(4, uno_counts)
        self.assertIn(8, uno_counts)
        self.assertIn(16, uno_counts)

        sketch_path = catalog.sketch_path(BOARD_ARDUINO, 2)
        self.assertTrue(sketch_path.name.endswith(".ino"))

    def test_firmware_configurator_apply(self):
        catalog = FirmwareCatalog()
        configurator = FirmwareConfigurator(catalog)
        config = RelayConfiguration.create_default(BOARD_ARDUINO, 2)
        config.loop_time = 45

        success = configurator.apply_profile(config)
        self.assertTrue(success)

        read_back = configurator.read_current_config(BOARD_ARDUINO, 2)
        self.assertEqual(read_back.loop_time, 45)


class TestBoardDetector(unittest.TestCase):
    def test_board_detector_interface(self):
        detector = BoardDetector()
        info = detector.detect(BOARD_ARDUINO)
        self.assertIsInstance(info, BoardInfo)
        self.assertIn(info.board_type, (BOARD_ARDUINO, BOARD_ESP32))


class TestSettingsManager(unittest.TestCase):
    def test_settings_manager_defaults(self):
        sm = SettingsManager()
        self.assertEqual(sm.settings.theme, "dark")
        self.assertGreater(sm.settings.window_width, 0)


if __name__ == "__main__":
    unittest.main()
