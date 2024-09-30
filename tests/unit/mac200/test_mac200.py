# tests/test_mac200.py

import time
from assertpy import assert_that
import pytest
from tango import DevState, DevFailed
from ska_tango_testing import context
from ska_tango_testing.integration import TangoEventTracer
from unittest.mock import MagicMock, patch
from ska_control_model import ObsState, ResultCode

from ska_mid_cbf_fhs_vcc.mac.mac_200_device import Mac200

EVENT_TIMEOUT = 30

# @pytest.fixture(scope="module")
# def test_harness():
#     with TangoTestHarness() as harness:
#         yield harness


@pytest.fixture(name="test_context")
def mac200_device():
    """
    Fixture to set up the Mac200 device for testing with a mock Tango database.
    """

    harness = context.ThreadedTestTangoContextManager()
    harness.add_device(device_name="test/mac200/1", 
                       device_class=Mac200, 
                       device_id="mac200_test_device",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0")

    with harness as test_context:
        yield test_context


def test_device_initialization(device_under_test):
    """
    Test that the Mac200 device initializes correctly.
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


def test_configure_command(device_under_test, event_tracer: TangoEventTracer):
    """
    Test the Configure command of the Mac200 device.
    """

    # Define configuration input
    config_json = '{"rx_loopback_enable ": False}'  # Adjust according to expected format

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value


def test_deconfigure_command(device_under_test, event_tracer: TangoEventTracer):
    """
    Test the Deconfigure command of the Mac200 device.
    """

    test_configure_command(device_under_test, event_tracer)

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
    Test the Status command of the Mac200 device.
    """
    # Define input for clear flag
    clear = False  # or True, depending on the test case

    # Invoke the command
    result = device_under_test.command_inout("GetStatus", clear)

    # Extract the result code and message
    result_code, message = result[0][0], result[1][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"


def test_recover_command(device_under_test):
    """
    Test the Recover command of the Mac200 device.
    """

    # Invoke the command
    result = device_under_test.command_inout("Recover")

    # Extract the result code and message
    result_code, message = result[0][0], result[1][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"


# def test_simulation_mode_attribute(mac200_device):
#     """
#     Test reading and writing the simulationMode attribute.
#     """
#     device_name, _ = mac200_device
#     device = DeviceProxy(device_name)

#     # Read the default value
#     sim_mode = device.read_attribute("simulationMode").value
#     assert sim_mode == 0, f"Expected default simulationMode 0, got {sim_mode}"

#     # Write a new value
#     device.write_attribute("simulationMode", 1)  # Assuming 1 corresponds to SimulationMode.TRUE

#     # Read back the new value
#     new_sim_mode = device.read_attribute("simulationMode").value
#     assert new_sim_mode == 1, f"Expected simulationMode 1, got {new_sim_mode}"

# def test_emulation_mode_attribute(mac200_device):
#     """
#     Test reading and writing the emulationMode attribute.
#     """
#     device_name, _ = mac200_device
#     device = DeviceProxy(device_name)

#     # Read the default value
#     emu_mode = device.read_attribute("emulationMode").value
#     assert emu_mode is True, f"Expected default emulationMode True, got {emu_mode}"

#     # Write a new value
#     device.write_attribute("emulationMode", False)

#     # Read back the new value
#     new_emu_mode = device.read_attribute("emulationMode").value
#     assert new_emu_mode is False, f"Expected emulationMode False, got {new_emu_mode}"
