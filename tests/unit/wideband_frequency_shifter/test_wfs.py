# tests/test_packet validation.py

import time
from assertpy import assert_that
import pytest
from tango import DevState, DevFailed
from ska_tango_testing import context
from ska_tango_testing.integration import TangoEventTracer
from unittest.mock import MagicMock, patch
from ska_control_model import ObsState, ResultCode

from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_device import WidebandFrequencyShifter

EVENT_TIMEOUT = 30


@pytest.fixture(name="test_context")
def pv_device():
    """
    Fixture to set up the packet validation device for testing with a mock Tango database.
    """
    harness = context.ThreadedTestTangoContextManager()
    harness.add_device(
        device_name="test/wfs/1",
        device_class=WidebandFrequencyShifter,
        device_id="1",
        device_version_num="1.0",
        device_gitlab_hash="abc123",
        emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
        bitstream_path="../resources",
        bitstream_id="agilex-vcc",
        bitstream_version="0.0.1",
        simulation_mode="1",
        emulation_mode="0",
        emulator_ip_block_id="wideband_frequency_shifter",
        emulator_id="vcc-emulator-1",
    )

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


def test_configure_command(device_under_test):
    """
    Test the Configure command of the wideband frequency shifter device.
    """

    config_json = '{"shift_frequency": 110.0}'

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value


def test_deconfigure_command(device_under_test):
    """
    Test the Deconfigure command of the wideband frequency shifter device.
    """

    test_configure_command(device_under_test)

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value

    # Invoke the command
    result = device_under_test.command_inout("Deconfigure")

    # Extract the result code and message
    result_code, message = result[0][0], result[1][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
    assert device_under_test.read_attribute("obsState").value is ObsState.IDLE.value


def test_status_command(device_under_test):
    """
    Test the Status command of the packet validation device.
    """
    # Define input for clear flag
    clear = False  # or True, depending on the test case

    # Invoke the command
    result = device_under_test.command_inout("getstatus", clear)

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


def test_go_to_idle(device_under_test):
    test_configure_command(device_under_test)

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value

    result = device_under_test.command_inout("GoToIdle")
    result_code = result[0][0]

    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
    assert device_under_test.read_attribute("obsState").value is ObsState.IDLE.value
