import pytest

from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_manager import PacketValidationManager


class TestPacketValidation:

    @pytest.fixture(scope="function")
    def packet_validation(self):
        """Fixture to set up the Packet Validation block."""
        manager = PacketValidationManager(
            ip_block_id="PacketValidation",
            controlling_device_name="n/a",
            bitstream_path="n/a",
            bitstream_id="n/a",
            bitstream_version="n/a",
            firmware_ip_block_id="n/a",
            create_log_file=False,
        )
        yield manager

    def test_start(self, packet_validation: PacketValidationManager):
        """Test the start method of the Packet Validation block."""
        result = packet_validation.start().await_result()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_stop(self, packet_validation: PacketValidationManager):
        """Test the stop method of the Packet Validation block."""
        self.test_start(packet_validation)
        result = packet_validation.stop().await_result()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_status(self, packet_validation: PacketValidationManager):
        """Test the status method of the Packet Validation block."""
        result = packet_validation.status(clear=False)
        assert result is not None, f"Expected valid return value, got {result}"

    def test_recover(self, packet_validation: PacketValidationManager):
        """Test the recover method of the Packet Validation block."""
        result = packet_validation.recover()
        assert result == 0, f"Expected return code 0, got {result}"
