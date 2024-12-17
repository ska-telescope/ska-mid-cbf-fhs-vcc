# tests/test_packet validation.py

from contextlib import nullcontext as does_not_raise
import time
from unittest import mock
from assertpy import assert_that
import pytest
from tango import DevState
from ska_tango_testing import context
from ska_tango_testing.integration import TangoEventTracer
from ska_control_model import HealthState, ObsState, ResultCode

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_device import WidebandInputBuffer
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_component_manager import convert_dish_id_uint16_t_to_mnemonic

EVENT_TIMEOUT = 30


@pytest.fixture(name="test_context", scope="module")
def pv_device():
    """
    Fixture to set up the packet validation device for testing with a mock Tango database.
    """
    harness = context.ThreadedTestTangoContextManager()
    harness.add_device(
        device_name="test/wib/1",
        device_class=WidebandInputBuffer,
        device_id="1",
        device_version_num="1.0",
        device_gitlab_hash="abc123",
        emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
        bitstream_path="../resources",
        bitstream_id="agilex-vcc",
        bitstream_version="0.0.1",
        simulation_mode="1",
        emulation_mode="0",
        emulator_ip_block_id="wideband_input_buffer",
        emulator_id="vcc-emulator-1",
        health_monitor_poll_interval="1",
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

    # Define configuration input
    config_json = '{"expected_sample_rate": 3960000000, "noise_diode_transition_holdoff_seconds": 1.0, "expected_dish_band": 1}'

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value


def test_status_command(device_under_test):
    """
    Test the Status command of the packet validation device.
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


@pytest.mark.parametrize(
    ("id", "expected_mnemonic", "exception_expectation"),
    [
        # SKA dish valid tests
        (0x1001, "SKA001", does_not_raise()),
        (0x100A, "SKA010", does_not_raise()),
        (0x100B, "SKA011", does_not_raise()),
        (0x1069, "SKA105", does_not_raise()),
        (0x1085, "SKA133", does_not_raise()),
        # SKA dish invalid tests
        (0x1000, None, pytest.raises(ValueError)),  # SKA000 is not valid
        (0x1086, None, pytest.raises(ValueError)),  # SKA134 is not valid
        (0x10A3, None, pytest.raises(ValueError)),  # Out of range
        (0x2030, None, pytest.raises(ValueError)),  # Invalid dish type
        # MKT dish valid tests
        (0x0000, "MKT000", does_not_raise()),
        (0x0001, "MKT001", does_not_raise()),
        (0x0037, "MKT055", does_not_raise()),
        (0x003F, "MKT063", does_not_raise()),
        # MKT dish invalid tests
        (0x0040, None, pytest.raises(ValueError)),  # Out of range
        (0x0085, None, pytest.raises(ValueError)),  # Out of range
        (0x3010, None, pytest.raises(ValueError)),  # Invalid dish type
        # Other invalid tests
        (0x2000, None, pytest.raises(ValueError)),  # 2 is not a dish type
        (0x1000, None, pytest.raises(ValueError)),  # SKA000 is not valid
        (0x1086, None, pytest.raises(ValueError)),  # SKA134 is not valid
        (0x0040, None, pytest.raises(ValueError)),  # MKT134 is not valid
        # Special case
        (0xFFFF, "DIDINV", does_not_raise()),
    ],
)
def test_convert_dish_id(id, expected_mnemonic, exception_expectation):
    with exception_expectation:
        assert convert_dish_id_uint16_t_to_mnemonic(id) == expected_mnemonic


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


def test_register_polling_healthstate_failed(device_under_test, event_tracer):
    config_json = '{"expected_sample_rate": 3920000000, "noise_diode_transition_holdoff_seconds": 1.0, "expected_dish_band": 1}'

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value

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

    time.sleep(5)

    healthState = device_under_test.read_attribute("healthState")

    assert healthState.value is HealthState.FAILED.value


def test_register_polling_healthstate_ok(device_under_test, event_tracer):
    config_json = '{"expected_sample_rate": 3960000000, "noise_diode_transition_holdoff_seconds": 1.0, "expected_dish_band": 1}'

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    assert device_under_test.read_attribute("obsState").value is ObsState.READY.value

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

    time.sleep(5)

    healthState = device_under_test.read_attribute("healthState")

    assert healthState.value is HealthState.OK.value
