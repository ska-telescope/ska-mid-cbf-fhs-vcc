import pytest

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_manager import B123VccOsppfbChannelizerConfigureArgin, B123VccOsppfbChannelizerManager


class TestB123VccOsppfbChannelizer:

    @pytest.fixture(scope="function")
    def b123_vcc(self):
        """Fixture to set up the B123 VCC."""
        manager = B123VccOsppfbChannelizerManager(
            ip_block_id="B123VccOsppfbChannelizer",
            controlling_device_name="n/a",
            bitstream_path="n/a",
            bitstream_id="n/a",
            bitstream_version="n/a",
            firmware_ip_block_id="n/a",
            create_log_file=False,
        )
        yield manager

    def test_configure(self, b123_vcc: B123VccOsppfbChannelizerManager):
        """Test the configure method of the B123 VCC."""
        with open("tests/test_data/device_config/b123_vcc_osppfb_channelizer.json", "r") as f:
            config_json = f.read()
        result = b123_vcc.configure(B123VccOsppfbChannelizerConfigureArgin.schema().loads(config_json))
        assert result == 0, f"Expected return code 0, got {result}"

    def test_deconfigure(self, b123_vcc: B123VccOsppfbChannelizerManager):
        """Test the deconfigure method of the B123 VCC."""
        self.test_configure(b123_vcc)
        result = b123_vcc.deconfigure()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_status(self, b123_vcc: B123VccOsppfbChannelizerManager):
        """Test the status method of the B123 VCC."""
        result = b123_vcc.status(clear=False)
        assert result is not None, f"Expected valid return value, got {result}"

    def test_recover(self, b123_vcc: B123VccOsppfbChannelizerManager):
        """Test the recover method of the B123 VCC."""
        result = b123_vcc.recover()
        assert result == 0, f"Expected return code 0, got {result}"
