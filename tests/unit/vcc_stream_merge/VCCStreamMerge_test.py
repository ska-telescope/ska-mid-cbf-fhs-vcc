import pytest

from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_manager import VCCStreamMergeConfigureArgin, VCCStreamMergeManager


class TestVCCStreamMerge:

    @pytest.fixture(scope="function")
    def vcc_stream_merge(self):
        """Fixture to set up the VCC Stream Merge block."""
        manager = VCCStreamMergeManager(
            ip_block_id="VCCStreamMerge",
            controlling_device_name="n/a",
            bitstream_path="n/a",
            bitstream_id="n/a",
            bitstream_version="n/a",
            firmware_ip_block_id="n/a",
            create_log_file=False,
        )
        yield manager

    def test_configure(self, vcc_stream_merge: VCCStreamMergeManager):
        """Test the configure method of the VCC Stream Merge block."""
        with open("tests/test_data/device_config/vcc_stream_merge.json", "r") as f:
            config_json = f.read()
        result = vcc_stream_merge.configure(VCCStreamMergeConfigureArgin.schema().loads(config_json))
        assert result == 0, f"Expected return code 0, got {result}"

    def test_deconfigure(self, vcc_stream_merge: VCCStreamMergeManager):
        """Test the deconfigure method of the VCC Stream Merge block."""
        self.test_configure(vcc_stream_merge)
        result = vcc_stream_merge.deconfigure()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_start(self, vcc_stream_merge: VCCStreamMergeManager):
        """Test the start method of the VCC Stream Merge block."""
        result = vcc_stream_merge.start()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_stop(self, vcc_stream_merge: VCCStreamMergeManager):
        """Test the stop method of the VCC Stream Merge block."""
        self.test_start(vcc_stream_merge)
        result = vcc_stream_merge.stop()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_status(self, vcc_stream_merge: VCCStreamMergeManager):
        """Test the status method of the VCC Stream Merge block."""
        result = vcc_stream_merge.status(clear=False)
        assert result is not None, f"Expected valid return value, got {result}"

    def test_recover(self, vcc_stream_merge: VCCStreamMergeManager):
        """Test the recover method of the VCC Stream Merge block."""
        result = vcc_stream_merge.recover()
        assert result == 0, f"Expected return code 0, got {result}"
