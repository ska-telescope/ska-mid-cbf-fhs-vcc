from __future__ import annotations

import gc
import json
import os
from typing import Iterator
from unittest.mock import Mock

import pytest
from ska_control_model import AdminMode, ObsState, ResultCode, SimulationMode
from ska_tango_testing import context
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup
from tango import DevState

from ska_mid_cbf_fhs_vcc.mac.mac_200_device import Mac200



# Disable garbage collection to prevent tests hanging
gc.disable()

class MacDeviceTest:
    @pytest.fixture(name="test_context")
    def mac_test_context(
        self: MacDeviceTest, initial_mocks: dict[str, Mock]
    ) -> Iterator[context.ThreadedTestTangoContextManager._TangoContext]:
        harness = context.ThreadedTestTangoContextManager()
        harness.add_device(
            device_name="mid_csp_cbf/mac/001",
            device_class=Mac200,
            DeviceID="1",
        )
        for name, mock in initial_mocks.items():
            harness.add_mock_device(device_name=name, device_mock=mock)

        with harness as test_context:
            yield test_context