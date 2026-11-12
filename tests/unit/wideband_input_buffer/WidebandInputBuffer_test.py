import time
from unittest import mock
import pytest
from ska_control_model import HealthState

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager import WidebandInputBufferConfig, WidebandInputBufferManager

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.constants import (
    BER_DEGRADED_THRESHOLD,
    BER_FAILED_THRESHOLD,
)

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
            update_health_state_callback=lambda *_: None,
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
        wideband_input_buffer.poll_counter = 29

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
        wideband_input_buffer.poll_counter = 29

        time.sleep(2)  # wait for polling to run at least once

        health_state = wideband_input_buffer.get_health_state()

        wideband_input_buffer.stop().await_result()

        assert health_state.value is HealthState.FAILED.value
        
    def test_ber_healthy(self, wideband_input_buffer: WidebandInputBufferManager):
        bad_status = {
            "link_failure": False,
            "buffer_overflow": False,
            "loss_of_signal": 0,
            "error": False,
            "loss_of_signal_seconds": 0,
            "meta_band_id": 1,
            "meta_dish_id": 1,
            "rx_sample_rate": 3960000000,
            "meta_transport_sample_rate": 3960000000,
            "packet_error": False,
            "packet_error_count": 0,
            "packet_drop": False,
            "packet_drop_count": 0,
            "rx_packet_rate": 1500000,
            "expected_sample_rate": 3960000000
        }
        
        with open("tests/test_data/device_config/wideband_input_buffer.json", "r") as f:
            config_json = f.read()

        with mock.patch(
            "ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager.WidebandInputBufferSimulator.status",
            return_value=bad_status
        ):
            wideband_input_buffer.configure(WidebandInputBufferConfig.schema().loads(config_json))
            wideband_input_buffer.expected_dish_id = "MKT001"
            wideband_input_buffer.start().await_result()
            wideband_input_buffer.poll_counter = 29

            time.sleep(2)  # wait for polling to run at least once

            health_state = wideband_input_buffer.get_health_state()

            wideband_input_buffer.stop().await_result()
            
            assert wideband_input_buffer.bit_error_rate < BER_DEGRADED_THRESHOLD
            assert health_state.value is HealthState.OK.value

    def test_ber_degraded(self, wideband_input_buffer: WidebandInputBufferManager):
        bad_status = {
            "link_failure": False,
            "buffer_overflow": False,
            "loss_of_signal": 0,
            "error": False,
            "loss_of_signal_seconds": 0,
            "meta_band_id": 1,
            "meta_dish_id": 1,
            "rx_sample_rate": 3960000000,
            "meta_transport_sample_rate": 3960000000,
            "packet_error": True,
            "packet_error_count": 1,
            "packet_drop": False,
            "packet_drop_count": 0,
            "rx_packet_rate": 1500000,
            "expected_sample_rate": 3960000000
        }
        
        with open("tests/test_data/device_config/wideband_input_buffer.json", "r") as f:
            config_json = f.read()

        with mock.patch(
            "ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager.WidebandInputBufferSimulator.status",
            return_value=bad_status
        ):
            wideband_input_buffer.configure(WidebandInputBufferConfig.schema().loads(config_json))
            wideband_input_buffer.expected_dish_id = "MKT001"
            wideband_input_buffer.start().await_result()
            wideband_input_buffer.poll_counter = 29

            time.sleep(2)  # wait for polling to run at least once

            health_state = wideband_input_buffer.get_health_state()

            wideband_input_buffer.stop().await_result()
            
            assert wideband_input_buffer.bit_error_rate >= BER_DEGRADED_THRESHOLD
            assert wideband_input_buffer.bit_error_rate < BER_FAILED_THRESHOLD
            assert health_state.value is HealthState.DEGRADED.value
            
    def test_ber_failed(self, wideband_input_buffer: WidebandInputBufferManager):
        bad_status = {
            "link_failure": False,
            "buffer_overflow": False,
            "loss_of_signal": 0,
            "error": False,
            "loss_of_signal_seconds": 0,
            "meta_band_id": 1,
            "meta_dish_id": 1,
            "rx_sample_rate": 3960000000,
            "meta_transport_sample_rate": 3960000000,
            "packet_error": True,
            "packet_error_count": 2,
            "packet_drop": False,
            "packet_drop_count": 0,
            "rx_packet_rate": 1500000,
            "expected_sample_rate": 3960000000
        }
        
        with open("tests/test_data/device_config/wideband_input_buffer.json", "r") as f:
            config_json = f.read()

        with mock.patch(
            "ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager.WidebandInputBufferSimulator.status",
            return_value=bad_status
        ):
            wideband_input_buffer.configure(WidebandInputBufferConfig.schema().loads(config_json))
            wideband_input_buffer.expected_dish_id = "MKT001"
            wideband_input_buffer.start().await_result()
            wideband_input_buffer.poll_counter = 29

            time.sleep(2)  # wait for polling to run at least once

            health_state = wideband_input_buffer.get_health_state()

            wideband_input_buffer.stop().await_result()
            
            assert wideband_input_buffer.bit_error_rate >= BER_FAILED_THRESHOLD
            assert health_state.value is HealthState.FAILED.value