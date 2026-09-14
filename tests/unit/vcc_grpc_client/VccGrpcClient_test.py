from concurrent import futures
from datetime import datetime, timezone
import logging
import math

import grpc
import pytest

from ska_mid_cbf_fhs_common.grpc.driver_registry_base import DriverInfo
from ska_mid_cbf_fhs_vcc_grpc_controller.driver_registry.vcc_driver_registry import VccDriverRegistry
from ska_mid_cbf_fhs_vcc_grpc_controller.generated.vcc_drivers import vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_fs_selection_pb2, gaussian_noise_pb2, vcc_bite_tone_gen_pb2, polarization_coupler_pb2, spfrx_packetizer_pb2, vcc_bite_pb2,vcc_source_select_pb2, vcc_pkt_filter_pb2, wideband_input_buffer_pb2, vcc_pkt_capture_pb2, frequency_shifter_pb2, vcc_ch20_pb2, vcc_ch30_pb2, wideband_power_meter_pb2, vcc_stream_merge_pb2, pcie_stream_merge_pb2, noise_diode_pb2, ftile_ethernet_pb2
from ska_mid_cbf_fhs_vcc_grpc_controller.generated.common import sys_id_pb2
from ska_mid_cbf_fhs_vcc_grpc_controller.services.vcc_driver_servicer import VccDriverServicer
from google.protobuf.json_format import MessageToDict
from ska_mid_cbf_fhs_vcc_grpc_controller.simulators.mock_driver_instantiator import VccMockDriverInstantiator
from ska_mid_cbf_fhs_common.grpc.utils.proto_utils import message_to_dict_int64_as_int
from google.protobuf import empty_pb2
from ska_mid_cbf_fhs_vcc_grpc_controller.server import VccGrpcServer

from ska_mid_cbf_fhs_vcc.grpc.vcc_grpc_client import VccGrpcClient


logger = logging.Logger(__name__)

card = "t1413c1"

@pytest.fixture
def grpc_setup():

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=2),
    )

    driver_registry = VccDriverRegistry(logger)

    mock_driver_instantiator = VccMockDriverInstantiator(driver_registry, card)

    mock_driver_instantiator.instantiate_mock_drivers()

    vcc_drivers_servicer = VccDriverServicer(logger, driver_registry)

    vcc_drivers_pb2_grpc.add_VccFpgaDriverServicer_to_server(vcc_drivers_servicer, server)

    port = server.add_insecure_port("localhost:0")
    server.start()

    yield (port, driver_registry)
    server.stop(None)

class TestVccGrpcClient:
    
    def test_sys_id_configure(self, grpc_setup: tuple):
        vcc_grpc_client = VccGrpcClient("card0_sys_id_base_driver", logger, "localhost", grpc_setup[0])
        sys_id_config = {
                            "scratch": 10
                        }

        driver_info:DriverInfo = grpc_setup[1].get_driver_info_obj("card0_sys_id_base_driver")

        vcc_grpc_client.configure(sys_id_config)

        assert driver_info.driver.configuration["scratch"] == 10

        vcc_grpc_client.channel.close()

    def test_wideband_input_buffer_configure(self, grpc_setup: tuple):
        vcc_grpc_client = VccGrpcClient(f"{card}_receptor0_wideband_input_buffer_driver", logger, "localhost", grpc_setup[0])
        sys_id_config = {
                            "expected_sample_rate": int(3.96e9),
                            "noise_diode_transition_holdoff_seconds": float(0.0),
                            "expected_dish_band": int(1)
                        }

        driver_info:DriverInfo = grpc_setup[1].get_driver_info_obj(f"{card}_receptor0_wideband_input_buffer_driver")

        vcc_grpc_client.configure(sys_id_config)

        expected_config = {
            "expected_sample_rate": int(3.96e9),
            "noise_diode_transition_holdoff_seconds": float(0.0),
            "expected_dish_band": int(1),
        }

        assert driver_info.driver.configuration == expected_config

    def test_wideband_input_buffer_deconfigure_with_config(self, grpc_setup: tuple):
        self.test_wideband_input_buffer_configure(grpc_setup)

        vcc_grpc_client = VccGrpcClient(f"{card}_receptor0_wideband_input_buffer_driver", logger, "localhost", grpc_setup[0])
        sys_id_config = {
                            "expected_sample_rate": int(3.96e9),
                            "noise_diode_transition_holdoff_seconds": float(0.0),
                            "expected_dish_band": int(1)
                        }

        driver_info:DriverInfo = grpc_setup[1].get_driver_info_obj(f"{card}_receptor0_wideband_input_buffer_driver")

        vcc_grpc_client.deconfigure(sys_id_config)

        assert driver_info.driver.configuration == {}

    def test_wideband_input_buffer_deconfigure_without_config(self, grpc_setup: tuple):
        self.test_wideband_input_buffer_configure(grpc_setup)

        vcc_grpc_client = VccGrpcClient(f"{card}_receptor0_wideband_input_buffer_driver", logger, "localhost", grpc_setup[0])

        driver_info:DriverInfo = grpc_setup[1].get_driver_info_obj(f"{card}_receptor0_wideband_input_buffer_driver")

        vcc_grpc_client.deconfigure()

        assert driver_info.driver.configuration == {}

    def test_b123_vcc_osppfb_channeliser_configure(self, grpc_setup: tuple):
        vcc_grpc_client = VccGrpcClient(f"{card}_receptor0_wideband_input_buffer_driver", logger, "localhost", grpc_setup[0])
        sys_id_config = {
                            "expected_sample_rate": int(3.96e9),
                            "noise_diode_transition_holdoff_seconds": float(0.0),
                            "expected_dish_band": int(1)
                        }

        driver_info:DriverInfo = grpc_setup[1].get_driver_info_obj(f"{card}_receptor0_wideband_input_buffer_driver")

        vcc_grpc_client.configure(sys_id_config)

        expected_config = {
            "expected_sample_rate": int(3.96e9),
            "noise_diode_transition_holdoff_seconds": float(0.0),
            "expected_dish_band": int(1),
        }

        assert driver_info.driver.configuration == expected_config

    def test_b123_vcc_osppfb_channeliser_deconfigure_with_config(self, grpc_setup: tuple):
        self.test_wideband_input_buffer_configure(grpc_setup)

        vcc_grpc_client = VccGrpcClient(f"{card}_receptor0_wideband_input_buffer_driver", logger, "localhost", grpc_setup[0])
        sys_id_config = {
                            "expected_sample_rate": int(3.96e9),
                            "noise_diode_transition_holdoff_seconds": float(0.0),
                            "expected_dish_band": int(1)
                        }

        driver_info:DriverInfo = grpc_setup[1].get_driver_info_obj(f"{card}_receptor0_wideband_input_buffer_driver")

        vcc_grpc_client.deconfigure(sys_id_config)

        assert driver_info.driver.configuration == {}
        
        
