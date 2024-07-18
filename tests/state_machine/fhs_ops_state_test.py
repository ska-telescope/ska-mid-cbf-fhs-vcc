from __future__ import annotations

from typing import Iterator
from unittest.mock import Mock
import pytest

import logging

from ska_control_model import AdminMode, ObsState, ResultCode
from ska_tango_testing import context
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup
from tango import DevState

from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine, FhsObsStateModel
from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice

class FhsObsStateTest():
    
    @pytest.fixture(name="test_context")
    def fsp_corr_test_context(
        self: FhsObsStateTest, initial_mocks: dict[str, Mock]
    ) -> Iterator[context.ThreadedTestTangoContextManager._TangoContext]:
        harness = context.ThreadedTestTangoContextManager()
        harness.add_device(
            device_name="fhs01/fhs-base/01",
            device_class=FhsBaseDevice,
            DeviceID="1",
            instance_name="test"
        )
        for name, mock in initial_mocks.items():
            harness.add_mock_device(device_name=name, device_mock=mock)

        with harness as test_context:
            yield test_context
        
def test_State(
        self: FhsObsStateTest, device_under_test: context.DeviceProxy
    ) -> None:
        """
        Test State

        :param device_under_test: fixture that provides a
            :py:class:`CbfDeviceProxy` to the device under test, in a
            :py:class:`tango.test_context.DeviceTestContext`.
        """
        assert device_under_test.State() == DevState.DISABLE