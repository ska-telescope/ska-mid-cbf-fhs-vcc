from assertpy import assert_that
import pytest
from tango import DevState
from ska_tango_testing.integration import TangoEventTracer
from ska_control_model import ResultCode
from ska_mid_cbf_fhs_common import ConfigurableThreadedTestTangoContextManager, DeviceTestUtils
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_device import PacketValidation

EVENT_TIMEOUT = 30


@pytest.mark.forked
class TestPacketValidation:

    @pytest.fixture(name="test_context", scope="module")
    def init_test_context(self):
        """
        Fixture to set up the packet validation device for testing with a mock Tango database.
        """
        harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)
        harness.add_device(
            device_name="test/packet_validation/1",
            device_class=PacketValidation,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="packet_validation",
            emulator_id="vcc-emulator-1",
        )

        with harness as test_context:
            yield test_context

    def test_device_initialization(self, device_under_test):
        """
        Test that the packet validation device initializes correctly.
        """

        # Check device state
        state = device_under_test.state()
        assert state == DevState.ON, f"Expected state ON, got {state}"

        # # Check device status
        status = device_under_test.status()
        assert status == "ON", f"Expected status 'ON', got '{status}'"

    def test_start_command(self, device_under_test, event_tracer: TangoEventTracer):
        """
        Test the Start command of the Packet Validation device.
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
        Test the Stop command of the Packet Validation device.
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

    def test_status_command(self, device_under_test):
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

    def test_recover_command(self, device_under_test):
        """
        Test the Recover command of the packet validation device.
        """

        # Invoke the command
        result = device_under_test.command_inout("Recover")

        # Extract the result code and message
        result_code = result[0][0]

        # Assertions
        assert result_code == ResultCode.OK.value, f"Expected ResultCode.OK ({ResultCode.OK.value}), got {result_code}"
