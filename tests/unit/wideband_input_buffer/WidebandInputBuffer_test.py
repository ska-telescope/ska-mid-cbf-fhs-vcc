import time
import pytest
from ska_control_model import HealthState

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager import WidebandInputBufferConfig, WidebandInputBufferManager

class TestWidebandInputBuffer:

    @pytest.fixture(scope="class")
    def wideband_input_buffer(self):
        """
        Fixture to set up the Wideband Input Buffer.
        """
        wib = WidebandInputBufferManager(
            ip_block_id="WidebandInputBuffer",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            firmware_ip_block_id="",
            health_monitor_poll_interval=1,
            update_health_state_callback=lambda _: None
        )
        yield wib

    def test_configure(self, wideband_input_buffer: WidebandInputBufferManager):
        """
        Test the configure method of the Wideband Input Buffer.
        """

        # Define configuration input
        with open("tests/test_data/device_config/wideband_input_buffer.json", "r") as f:
            config_json = f.read()

        # Invoke the command
        result = wideband_input_buffer.configure(WidebandInputBufferConfig.schema().loads(config_json))

        # Assertions
        assert result == 0, f"Expected return code 0, got {result}"

    def test_status_command(self, wideband_input_buffer: WidebandInputBufferManager):
        """
        Test the Status command of the Wideband Input Buffer device.
        """
        # Define input for clear flag
        clear = False  # or True, depending on the test case

        # Invoke the command
        result = wideband_input_buffer.status(clear)

        # Assertions
        assert result is not None, f"Expected valid return value, got {result}"

    def test_recover_command(self, wideband_input_buffer: WidebandInputBufferManager):
        """
        Test the Recover command of the Wideband Input Buffer device.
        """

        # Invoke the command
        result = wideband_input_buffer.recover()

        # Assertions
        assert result == 0, f"Expected return code 0, got {result}"

    def test_start_command(self, wideband_input_buffer: WidebandInputBufferManager):
        """
        Test the Start command of the Wideband Input Buffer device.
        """

        # Invoke the command
        result = wideband_input_buffer.start().await_result()

        # Assertions
        assert result == 0, f"Expected return code 0, got {result}"

    def test_stop_command(self, wideband_input_buffer: WidebandInputBufferManager):
        """
        Test the Stop command of the Wideband Input Buffer device.
        """
        result = wideband_input_buffer.stop().await_result()

        # Assertions
        assert result == 0, f"Expected return code 0, got {result}"

    def test_register_polling_healthstate_ok(self, wideband_input_buffer: WidebandInputBufferManager):

        with open("tests/test_data/device_config/wideband_input_buffer.json", "r") as f:
            config_json = f.read()

        wideband_input_buffer.configure(WidebandInputBufferConfig.schema().loads(config_json))
        wideband_input_buffer.expected_dish_id = "MKT001"
        wideband_input_buffer.start().await_result()

        time.sleep(2)  # wait for polling to run at least once

        health_state = wideband_input_buffer.get_health_state()

        wideband_input_buffer.stop().await_result()

        assert health_state.value is HealthState.OK.value

    def test_register_polling_healthstate_failed(self, wideband_input_buffer: WidebandInputBufferManager):

        with open("tests/test_data/device_config/wideband_input_buffer_health_failure.json", "r") as f:
            config_json = f.read()

        wideband_input_buffer.configure(WidebandInputBufferConfig.schema().loads(config_json))
        wideband_input_buffer.expected_dish_id = "MKT001"
        wideband_input_buffer.start().await_result()

        time.sleep(2)  # wait for polling to run at least once

        health_state = wideband_input_buffer.get_health_state()

        wideband_input_buffer.stop().await_result()

        assert health_state.value is HealthState.FAILED.value
