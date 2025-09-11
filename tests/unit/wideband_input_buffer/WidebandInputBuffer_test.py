import time
import pytest
from ska_control_model import HealthState

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager import WidebandInputBufferConfig, WidebandInputBufferManager

class TestWidebandInputBuffer:

    @pytest.fixture(scope="class")
    def wideband_input_buffer(self):
        """Fixture to set up the Wideband Input Buffer."""
        manager = WidebandInputBufferManager(
            ip_block_id="WidebandInputBuffer",
            controlling_device_name="n/a",
            bitstream_path="n/a",
            bitstream_id="n/a",
            bitstream_version="n/a",
            firmware_ip_block_id="n/a",
            health_monitor_poll_interval=1,
            update_health_state_callback=lambda _: None,
            create_log_file=False,
        )
        yield manager
        if manager.health_monitor.is_polling():
            manager.health_monitor.stop_polling()
        del manager

    def test_configure(self, wideband_input_buffer: WidebandInputBufferManager):
        """Test the configure method of the Wideband Input Buffer."""
        with open("tests/test_data/device_config/wideband_input_buffer.json", "r") as f:
            config_json = f.read()
        result = wideband_input_buffer.configure(WidebandInputBufferConfig.schema().loads(config_json))
        assert result == 0, f"Expected return code 0, got {result}"

    def test_status(self, wideband_input_buffer: WidebandInputBufferManager):
        """Test the status method of the Wideband Input Buffer."""
        result = wideband_input_buffer.status(clear=False)
        assert result is not None, f"Expected valid return value, got {result}"

    def test_recover(self, wideband_input_buffer: WidebandInputBufferManager):
        """Test the recover method of the Wideband Input Buffer."""
        result = wideband_input_buffer.recover()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_start(self, wideband_input_buffer: WidebandInputBufferManager):
        """Test the start method of the Wideband Input Buffer."""
        result = wideband_input_buffer.start().await_result()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_stop(self, wideband_input_buffer: WidebandInputBufferManager):
        """Test the stop method of the Wideband Input Buffer."""
        result = wideband_input_buffer.stop().await_result()
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
