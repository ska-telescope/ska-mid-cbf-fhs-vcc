import pytest
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_manager import WidebandFrequencyShifterConfig, WidebandFrequencyShifterManager


class TestWidebandFrequencyShifter:

    @pytest.fixture(scope="function")
    def wideband_frequency_shifter(self):
        """Fixture to set up the Wideband Frequency Shifter."""
        manager = WidebandFrequencyShifterManager(
            ip_block_id="WidebandFrequencyShifter",
            controlling_device_name="n/a",
            bitstream_path="n/a",
            bitstream_id="n/a",
            bitstream_version="n/a",
            firmware_ip_block_id="n/a",
            create_log_file=False,
        )
        yield manager

    def test_configure(self, wideband_frequency_shifter: WidebandFrequencyShifterManager):
        """Test the configure method of the Wideband Frequency Shifter."""
        with open("tests/test_data/device_config/wideband_frequency_shifter.json", "r") as f:
            config_json = f.read()
        result = wideband_frequency_shifter.configure(WidebandFrequencyShifterConfig.schema().loads(config_json))
        assert result == 0, f"Expected return code 0, got {result}"

    def test_deconfigure(self, wideband_frequency_shifter: WidebandFrequencyShifterManager):
        """Test the deconfigure method of the Wideband Frequency Shifter."""
        self.test_configure(wideband_frequency_shifter)
        result = wideband_frequency_shifter.deconfigure()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_status(self, wideband_frequency_shifter: WidebandFrequencyShifterManager):
        """Test the status method of the Wideband Frequency Shifter."""
        result = wideband_frequency_shifter.status(clear=False)
        assert result is not None, f"Expected valid return value, got {result}"

    def test_recover(self, wideband_frequency_shifter: WidebandFrequencyShifterManager):
        """Test the recover method of the Wideband Frequency Shifter."""
        result = wideband_frequency_shifter.recover()
        assert result == 0, f"Expected return code 0, got {result}"
