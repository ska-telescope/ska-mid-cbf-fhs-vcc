# tests/test_packet validation.py

import time
from assertpy import assert_that
import pytest
from tango import DevState, DevFailed
from ska_tango_testing import context
from ska_tango_testing.integration import TangoEventTracer
from unittest.mock import MagicMock, patch
from ska_control_model import ObsState, ResultCode

from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_device import PacketValidation

EVENT_TIMEOUT = 30


@pytest.fixture(name="test_context")
def pv_device():
    """
    Fixture to set up the packet validation device for testing with a mock Tango database.
    """
    harness = context.ThreadedTestTangoContextManager()
    harness.add_device(device_name="test/packet_validation/1", 
                       device_class=PacketValidation, 
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0",
                       emulator_ipblock_id="packet_validation",
                       emulator_id="vcc-emulator-1")

    with harness as test_context:
        yield test_context


def test_device_initialization(device_under_test):
    """
    Test that the packet validation device initializes correctly.
    """

    # Check device state
    state = device_under_test.state()
    assert state == DevState.ON, f"Expected state ON, got {state}"

    # # Check device status
    status = device_under_test.status()
    assert status == "ON", f"Expected status 'ON', got '{status}'"



def test_start_command(device_under_test, event_tracer: TangoEventTracer):
    """
    Test the Start command of the Mac200 device.
    """

    # Invoke the command
    result = device_under_test.command_inout("Start")

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.QUEUED.value, f"Expected ResultCode.QUEUED ({ResultCode.QUEUED.value}), got {result_code}"

    assert_that(event_tracer).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
        device_name=device_under_test,
        attribute_name="longRunningCommandResult",
        attribute_value=(
            f"{result[1][0]}",
            f'[{ResultCode.OK.value}, "Start Called Successfully"]',
        ),
    )
    obs_state = device_under_test.read_attribute("obsState").value
    assert obs_state is ObsState.SCANNING.value


def test_stop_command(device_under_test, event_tracer: TangoEventTracer):
    """
    Test the Stop command of the Mac200 device.
    """
    result = device_under_test.command_inout("Stop")

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.QUEUED.value, f"Expected ResultCode.QUEUED ({ResultCode.QUEUED.value}), got {result_code}"

    assert_that(event_tracer).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
        device_name=device_under_test,
        attribute_name="longRunningCommandResult",
        attribute_value=(
            f"{result[1][0]}",
            f'[{ResultCode.OK.value}, "Stop Called Successfully"]',
        ),
    )

    obs_state = device_under_test.read_attribute("obsState").value
    assert obs_state is ObsState.READY.value


def test_status_command(device_under_test):
    """
    Test the Status command of the packet validation device.
    """
    # Define input for clear flag
    clear = False  # or True, depending on the test case

    # Invoke the command
    result = device_under_test.command_inout("GetStatus", clear)

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"


def test_recover_command(device_under_test):
    """
    Test the Recover command of the packet validation device.
    """

    # Invoke the command
    result = device_under_test.command_inout("Recover")

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"