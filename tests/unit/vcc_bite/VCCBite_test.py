import logging
import pytest

from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAllBandsConfigureVCCBiteSchema
from ska_mid_cbf_fhs_vcc.vcc_bite.vcc_bite_manager import VCCBiteManager

import grpc
from concurrent import futures
from ska_mid_cbf_fhs_vcc_grpc_controller.driver_registry.driver_registry import DriverRegistry
from ska_mid_cbf_fhs_vcc_grpc_controller.simulators.mock_driver_instantiator import MockDriverInstantiator
from ska_mid_cbf_fhs_vcc_grpc_controller.services.vcc_driver_servicer import VccDriverServicer
from ska_mid_cbf_fhs_vcc_grpc_controller.generated import vcc_drivers_pb2_grpc



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

    # TODO: Uncomment fixture when firmware mode is working
    # @pytest.fixture(scope="function")
    # def vcc_bite_firmware(self):
    #     """Fixture to set up the VCC Bite."""
    #     logger = logging.Logger("VCC Bite Logger")

    #     server = grpc.server(
    #         futures.ThreadPoolExecutor(max_workers=2),
    #     )

    #     driver_registry = DriverRegistry(logger)
    #     mock_driver_instantiator = MockDriverInstantiator(driver_registry, "")
    #     mock_driver_instantiator.instantiate_mock_drivers()
    #     vcc_drivers_servicer = VccDriverServicer(logger, driver_registry)

    #     vcc_drivers_pb2_grpc.add_VccFpgaDriverServicer_to_server(vcc_drivers_servicer, server)

    #     server.add_insecure_port("localhost:50051")
    #     server.start()

    #     manager = VCCBiteManager(
    #         logger=logger,
    #         simulation_mode=SimulationMode.FALSE,
    #     )
    #     yield manager

    #     server.stop(None)

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

    def test_status(self, vcc_bite: VCCBiteManager):
        """Test the status method of the VCC Bite."""
        result = vcc_bite.status(clear=False)
        assert result is not None, f"Expected valid return value, got {result}"

    # TODO: Uncomment tests when firmware mode is working
    # def test_configure_firmware(self, vcc_bite_firmware: VCCBiteManager):
    #     """Test the configure method of the VCC Bite."""
    #     with open("tests/test_data/device_config/vcc_bite.json", "r") as f:
    #         config_json = f.read()
    #     result = vcc_bite_firmware.configure(VCCAllBandsConfigureVCCBiteSchema.schema().loads(config_json))
    #     assert result == 0, f"Expected return code 0, got {result}"

    # def test_deconfigure_firmware(self, vcc_bite_firmware: VCCBiteManager):
    #     """Test the deconfigure method of the VCC Bite."""
    #     self.test_configure(vcc_bite_firmware)
    #     result = vcc_bite_firmware.deconfigure()
    #     assert result == 0, f"Expected return code 0, got {result}"

    # def test_start_firmware(self, vcc_bite_firmware: VCCBiteManager):
    #     """Test the start method of the VCC Bite."""
    #     result = vcc_bite_firmware.start()
    #     assert result == 0, f"Expected return code 0, got {result}"

    # def test_stop_firmware(self, vcc_bite_firmware: VCCBiteManager):
    #     """Test the stop method of the VCC Bite."""
    #     self.test_start(vcc_bite_firmware)
    #     result = vcc_bite_firmware.stop()
    #     assert result == 0, f"Expected return code 0, got {result}"

    # def test_status_firmware(self, vcc_bite_firmware: VCCBiteManager):
    #     """Test the status method of the VCC Bite."""
    #     result = vcc_bite_firmware.status(clear=False)
    #     assert result is not None, f"Expected valid return value, got {result}"
