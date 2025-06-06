from assertpy import assert_that
import pytest
from tango import DevState
from ska_tango_testing.integration import TangoEventTracer
from ska_control_model import ResultCode
from ska_mid_cbf_fhs_common import ConfigurableThreadedTestTangoContextManager
from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_device import VCCStreamMerge

EVENT_TIMEOUT = 30


@pytest.mark.forked
class TestVCCStreamMerge:

    @pytest.fixture(name="test_context", scope="module")
    def init_test_context(self):
        """
        Fixture to set up the VCC Stream Merge device for testing with a mock Tango database.
        """
        harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)
        harness.add_device(
            device_name="test/vcc-stream-merge/1",
            device_class=VCCStreamMerge,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="vcc_stream_merge1",
            emulator_id="vcc-emulator-1",
        )

        with harness as test_context:
            yield test_context

    def test_device_initialization(self, device_under_test):
        """
        Test that the VCC Stream Merge device initializes correctly.
        """

        # Check device state
        state = device_under_test.state()
        assert state == DevState.ON, f"Expected state ON, got {state}"

        # # Check device status
        status = device_under_test.status()
        assert status == "ON", f"Expected status 'ON', got '{status}'"

    def test_configure_command(self, device_under_test):
        """
        Test the Configure command of the VCC Stream Merge device.
        """

        with open("tests/test_data/device_config/vcc_stream_merge.json", "r") as f:
            config_json = f.read()

        # Invoke the command
        result = device_under_test.command_inout("Configure", config_json)

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    def test_deconfigure_command(self, device_under_test):
        """
        Test the Deconfigure command of the VCC Stream Merge device.
        """

        self.test_configure_command(device_under_test)

        # Invoke the command
        result = device_under_test.command_inout("Deconfigure")

        # Extract the result code and message
        result_code, message = result[0][0], result[1][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    def test_start_command(self, device_under_test, event_tracer: TangoEventTracer):
        """
        Test the Start command of the VCC Stream Merge device.
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

    def test_stop_command(self, device_under_test, event_tracer: TangoEventTracer):
        """
        Test the Stop command of the VCC Stream Merge device.
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

    def test_status_command(self, device_under_test):
        """
        Test the Status command of the VCC Stream Merge device.
        """
        # Define input for clear flag
        clear = False  # or True, depending on the test case

        # Invoke the command
        result = device_under_test.command_inout("GetStatus", clear)

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"

    def test_recover_command(self, device_under_test):
        """
        Test the Recover command of the VCC Stream Merge device.
        """

        # Invoke the command
        result = device_under_test.command_inout("Recover")

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
