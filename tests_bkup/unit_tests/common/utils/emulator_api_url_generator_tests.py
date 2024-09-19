from __future__ import annotations

import unittest


class EmulatorApiUrlGeneratorTests(unittest.TestCase):
    def __init__(self) -> None:
        self._emulator_test_file_path = "ska-mid-cbf-fhs-vcc/tests/unit_tests/test_resources/0.0.1.json"
        self._config_map_file_path = "ska-mid-cbf-fhs-vcc/tests/unit_tests/test_resources/test_config_map.json"
