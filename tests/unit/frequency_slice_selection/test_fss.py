# tests/test_fss.py

import time
from assertpy import assert_that
import pytest
from tango import DevState, DevFailed
from ska_tango_testing import context
from ska_tango_testing.integration import TangoEventTracer
from unittest.mock import MagicMock, patch
from ska_control_model import ObsState, ResultCode

from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_device import FrequencySliceSelection

EVENT_TIMEOUT = 30


@pytest.fixture(name="test_context")
def fss_device():
    """
    Fixture to set up the FSS device for testing with a mock Tango database.
    """
    harness = context.ThreadedTestTangoContextManager()
    harness.add_device(device_name="test/fss/1", 
                       device_class=FrequencySliceSelection,
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0",
                       emulator_ip_block_id="fs_selection_26_2_1",
                       emulator_id="vcc-emulator-1")

    with harness as test_context:
        yield test_context


def test_device_initialization(device_under_test):
    """
    Test that the fss device initializes correctly.
    """

    # Check device state
    state = device_under_test.state()
    assert state == DevState.ON, f"Expected state ON, got {state}"

    # # Check device status
    status = device_under_test.status()
    assert status == "ON", f"Expected status 'ON', got '{status}'"


def test_configure_command(device_under_test):
    """
    Test the Configure command of the fss device.
    """

    # Define configuration input
    config_json = '{"band_select": 1, "band_start_channel": [0, 1]}' 

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value
    
    
def test_configure_command_invalid_config(device_under_test):
    """
    Test the Configure command of the fss device.
    """

    # Define configuration input
    config_json = '{"invalid": [{"output": 1, "input":1}]}' 

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    # Extract the result code and message
    result_code = result[0][0]

    # TODO Do we need to set a fault obs_state here? 
    assert result_code == ResultCode.FAILED.value, f"Expected ResultCode.FAILED ({ResultCode.FAILED.value}), got {result_code}"



def test_deconfigure_command(device_under_test):
    """
    Test the Deconfigure command of the fss device.
    """

    test_configure_command(device_under_test)

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value

    # Invoke the command
    result = device_under_test.command_inout("Deconfigure")

    # Extract the result code and message
    result_code = result[0][0]
    
    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
    assert device_under_test.read_attribute("obsState").value is ObsState.IDLE.value
    

def test_status_command(device_under_test):
    """
    Test the Status command of the fss device.
    """
    # Define input for clear flag
    clear = False  # or True, depending on the test case

    # Invoke the command
    result = device_under_test.command_inout("GetStatus", clear)

    # Extract the result code and message
    result_code, message = result[0][0], result[1][0]
    
    expectedStatus = '{"band_select": 1, "band_start_channel": [0, 1]}'

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
    assert message == expectedStatus


def test_recover_command(device_under_test):
    """
    Test the Recover command of the fss device.
    """

    # Invoke the command
    result = device_under_test.command_inout("Recover")

    # Extract the result code and message
    result_code, message = result[0][0], result[1][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
