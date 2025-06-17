import time
from assertpy import assert_that
import pytest
from tango import DevState
from ska_tango_testing.integration import TangoEventTracer
from ska_control_model import HealthState, ResultCode
from ska_mid_cbf_fhs_common import ConfigurableThreadedTestTangoContextManager, DeviceTestUtils
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_device import WidebandInputBuffer

EVENT_TIMEOUT = 30


@pytest.mark.forked
class TestWidebandInputBuffer:

    @pytest.fixture(name="test_context", scope="module")
    def init_test_context(self):
        """
        Fixture to set up the Wideband Input Buffer device for testing with a mock Tango database.
        """
        harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)
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

    def test_device_initialization(self, device_under_test):
        """
        Test that the Wideband Input Buffer device initializes correctly.
        """

        # Check device state
        state = device_under_test.state()
        assert state == DevState.ON, f"Expected state ON, got {state}"

        # # Check device status
        status = device_under_test.status()
        assert status == "ON", f"Expected status 'ON', got '{status}'"

    def test_configure_command(self, device_under_test):
        """
        Test the Configure command of the Wideband Input Buffer device.
        """

        # Define configuration input
        with open("tests/test_data/device_config/wideband_input_buffer.json", "r") as f:
            config_json = f.read()

        # Invoke the command
        result = device_under_test.command_inout("Configure", config_json)

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    def test_status_command(self, device_under_test):
        """
        Test the Status command of the Wideband Input Buffer device.
        """
        # Define input for clear flag
        clear = False  # or True, depending on the test case

        # Invoke the command
        result = device_under_test.command_inout("GetStatus", clear)

        # Extract the result code and message
        result_code, message = result[0][0], result[1][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    def test_recover_command(self, device_under_test):
        """
        Test the Recover command of the Wideband Input Buffer device.
        """

        # Invoke the command
        result = device_under_test.command_inout("Recover")

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    def test_start_command(self, device_under_test, event_tracer: TangoEventTracer):
        """
        Test the Start command of the Wideband Input Buffer device.
        """

        # Invoke the command
        result = device_under_test.command_inout("Start")

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.QUEUED.value, f"Expected ResultCode.QUEUED ({ResultCode.QUEUED.value}), got {result_code}"

        assert_that(event_tracer).within_timeout(EVENT_TIMEOUT).with_early_stop(
            DeviceTestUtils.lrc_early_stop_matcher([ResultCode.OK], "Start", inverted=True)
        ).has_change_event_occurred(
            device_name=device_under_test,
            attribute_name="longRunningCommandResult",
            custom_matcher=DeviceTestUtils.lrc_result_matcher([ResultCode.OK], "Start")
        )

    def test_stop_command(self, device_under_test, event_tracer: TangoEventTracer):
        """
        Test the Stop command of the Wideband Input Buffer device.
        """
        result = device_under_test.command_inout("Stop")

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.QUEUED.value, f"Expected ResultCode.QUEUED ({ResultCode.QUEUED.value}), got {result_code}"

        assert_that(event_tracer).within_timeout(EVENT_TIMEOUT).with_early_stop(
            DeviceTestUtils.lrc_early_stop_matcher([ResultCode.OK], "Stop", inverted=True)
        ).has_change_event_occurred(
            device_name=device_under_test,
            attribute_name="longRunningCommandResult",
            custom_matcher=DeviceTestUtils.lrc_result_matcher([ResultCode.OK], "Stop")
        )

    def test_register_polling_healthstate_ok(self, device_under_test, event_tracer):

        DeviceTestUtils.polling_test_setup(
            device_under_test=device_under_test,
            event_tracer=event_tracer,
            config_json_file="tests/test_data/device_config/wideband_input_buffer.json",
            event_timeout=EVENT_TIMEOUT
        )

        time.sleep(2)

        health_state = device_under_test.read_attribute("healthState")

        assert health_state.value is HealthState.OK.value

    def test_register_polling_healthstate_failed(self, device_under_test, event_tracer):

        DeviceTestUtils.polling_test_setup(
            device_under_test=device_under_test,
            event_tracer=event_tracer,
            config_json_file="tests/test_data/device_config/wideband_input_buffer_health_failure.json",
            event_timeout=EVENT_TIMEOUT
        )

        time.sleep(2)

        health_state = device_under_test.read_attribute("healthState")

        assert health_state.value is HealthState.FAILED.value
