import logging
import pytest

from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAllBandsConfigureVCCBiteSchema
from ska_mid_cbf_fhs_vcc.vcc_bite.vcc_bite_manager import VCCBiteManager


class TestVCCBite:

    @pytest.fixture(scope="function")
    def vcc_bite(self):
        """Fixture to set up the VCC Bite."""
        logger = logging.Logger("VCC Bite Logger")
        manager = VCCBiteManager(
            logger=logger,
            simulation_mode=SimulationMode.TRUE,
        )
        yield manager

    def test_configure(self, vcc_bite: VCCBiteManager):
        """Test the configure method of the VCC Bite."""
        with open("tests/test_data/device_config/vcc_bite.json", "r") as f:
            config_json = f.read()
        result = vcc_bite.configure(VCCAllBandsConfigureVCCBiteSchema.schema().loads(config_json))
        assert result == 0, f"Expected return code 0, got {result}"

    def test_deconfigure(self, vcc_bite: VCCBiteManager):
        """Test the deconfigure method of the VCC Bite."""
        self.test_configure(vcc_bite)
        result = vcc_bite.deconfigure()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_start(self, vcc_bite: VCCBiteManager):
        """Test the start method of the VCC Bite."""
        result = vcc_bite.start()
        assert result == 0, f"Expected return code 0, got {result}"

    def test_stop(self, vcc_bite: VCCBiteManager):
        """Test the stop method of the VCC Bite."""
        self.test_start(vcc_bite)
        result = vcc_bite.stop()
        assert result == 0, f"Expected return code 0, got {result}"

    # def test_status(self, vcc_bite: VCCBiteManager):
    #     """Test the status method of the VCC Bite."""
    #     result = vcc_bite.status(clear=False)
    #     assert result is not None, f"Expected valid return value, got {result}"
