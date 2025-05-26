import pytest
from tango import DevState
from ska_control_model import ResultCode
from ska_mid_cbf_fhs_common import ConfigurableThreadedTestTangoContextManager
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_device import WidebandFrequencyShifter

EVENT_TIMEOUT = 30


@pytest.fixture(name="test_context", scope="module")
def init_test_context():
    """
    Fixture to set up the Frequency Shifter device for testing with a mock Tango database.
    """
    harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)
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


@pytest.mark.forked
def test_device_initialization(device_under_test):
    """
    Test that the Frequency Shifter device initializes correctly.
    """

    # Check device state
    state = device_under_test.state()
    assert state == DevState.ON, f"Expected state ON, got {state}"

    # # Check device status
    status = device_under_test.status()
    assert status == "ON", f"Expected status 'ON', got '{status}'"


@pytest.mark.forked
def test_configure_command(device_under_test):
    """
    Test the Configure command of the Frequency Shifter device.
    """

    config_json = '{"shift_frequency": 110.0}'

    # Invoke the command
    result = device_under_test.command_inout("Configure", config_json)

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"


@pytest.mark.forked
def test_deconfigure_command(device_under_test):
    """
    Test the Deconfigure command of the Frequency Shifter device.
    """

    test_configure_command(device_under_test)

    # Invoke the command
    result = device_under_test.command_inout("Deconfigure")

    # Extract the result code and message
    result_code, message = result[0][0], result[1][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"


@pytest.mark.forked
def test_status_command(device_under_test):
    """
    Test the Status command of the Frequency Shifter device.
    """
    # Define input for clear flag
    clear = False  # or True, depending on the test case

    # Invoke the command
    result = device_under_test.command_inout("getstatus", clear)

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"


@pytest.mark.forked
def test_recover_command(device_under_test):
    """
    Test the Recover command of the Frequency Shifter device.
    """

    # Invoke the command
    result = device_under_test.command_inout("Recover")

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
