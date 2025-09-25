import pytest

from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_manager import FrequencySliceSelectionConfig, FrequencySliceSelectionManager


class TestFrequencySliceSelection:

    @pytest.fixture(scope="function")
    def frequency_slice_selection(self):
        """Fixture to set up the Frequency Slice Selection block."""
        manager = FrequencySliceSelectionManager(
            ip_block_id="FrequencySliceSelection",
            controlling_device_name="n/a",
            bitstream_path="n/a",
            bitstream_id="n/a",
            bitstream_version="n/a",
            firmware_ip_block_id="n/a",
            create_log_file=False,
        )
        yield manager

    def test_configure(self, frequency_slice_selection: FrequencySliceSelectionManager):
        """Test the configure method of the Frequency Slice Selection block."""
        with open("tests/test_data/device_config/frequency_slice_selection.json", "r") as f:
            config_json = f.read()
        result = frequency_slice_selection.configure(FrequencySliceSelectionConfig.schema().loads(config_json))
        assert result == 0, f"Expected return code 0, got {result}"

    def test_deconfigure(self, frequency_slice_selection: FrequencySliceSelectionManager):
        """Test the deconfigure method of the Frequency Slice Selection block."""
        self.test_configure(frequency_slice_selection)
        result = frequency_slice_selection.deconfigure()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_status(self, frequency_slice_selection: FrequencySliceSelectionManager):
        """Test the status method of the Frequency Slice Selection block."""
        result = frequency_slice_selection.status(clear=False)
        assert result is not None, f"Expected valid return value, got {result}"

    def test_recover(self, frequency_slice_selection: FrequencySliceSelectionManager):
        """Test the recover method of the Frequency Slice Selection block."""
        result = frequency_slice_selection.recover()
        assert result == 0, f"Expected return code 0, got {result}"
