import logging
from dataclasses import dataclass
from enum import IntEnum

from dataclasses_json import DataClassJsonMixin
from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_common.base_classes.api.base_simulator_api import BaseSimulatorApi
from ska_mid_cbf_fhs_common.services.api.firmware_api import FirmwareApi
from ska_mid_cbf_fhs_common.services.grpc.grpc_client import GRPCInfo

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAllBandsConfigureVCCBiteSchema, VCCAllBandsDeconfigureVCCBiteSchema


class VCCSourceSelectSource(IntEnum):
    ETHERNET_200GB = 0
    VCC_BITE = 1
    ARKVILLE_PCIE = 2
    RESERVED = 3


@dataclass
class VCCSourceSelectApiConfig(DataClassJsonMixin):
    source_select: VCCSourceSelectSource
    test_select: bool


@dataclass
class VCCBiteApiConfig(DataClassJsonMixin):
    band: int = 1
    start_time: int = 0
    sample_rate: int = 3_960_000_000
    speed: int = 1


@dataclass
class VCCBiteToneGenApiConfig(DataClassJsonMixin):
    sample_rate: int
    frequency: int
    magnitude: int
    band: int


@dataclass
class GaussianNoiseDriverApiConfig(DataClassJsonMixin):
    seed: int
    mean: int
    std_dev: int


@dataclass
class NoiseDiodeApiConfig(DataClassJsonMixin):
    # TODO: Confirm if this field is needed, it exists in the driver on gitlab nrc config schema: sample_rate
    switching_period: float
    seed: int
    std_dev: float


@dataclass
class PolarizationCouplerApiConfig(DataClassJsonMixin):
    # TODO: Confirm if these fields are correct. They are different from the ones on NRC gitlab
    # TODO: NRC gitlab has delay_enable: bool, correlation_coefficient: float
    # TODO: Confirm if they are the same but just with differnt names
    pol_coupling_rho: float
    pol_y_1_sample_delay: bool


@dataclass
class SPFRxPacketizerApiConfig(DataClassJsonMixin):
    local_mac: int
    remote_mac: int
    ethertype: int
    dish_id: int
    hw_src_id: int
    band: int
    sample_rate: int
    sample_rate_b: int
    noise_diode_rising_holdoff: float
    noise_diode_rising_holdoff_b: float


##
# status class that will be populated by the APIs and returned to provide the status of VCC Stream Merge
##
@dataclass
class VCCBiteStatus(DataClassJsonMixin):
    pass


class VCCBiteManager:
    """VCC Bite manager."""

    def __init__(self, logger: logging.Logger, simulation_mode: SimulationMode = SimulationMode.TRUE, gprc_driver_info: dict[str, GRPCInfo] = None):
        self._simulation_mode = simulation_mode
        self.logger = logger

        if self._simulation_mode == SimulationMode.TRUE:
            self._vcc_source_select_api = BaseSimulatorApi("vcc_source_select", self.logger)
            self._vcc_bite_api = BaseSimulatorApi("vcc_bite", self.logger)
            self._vcc_bite_tone_gen_api = BaseSimulatorApi("vcc_bite_tone_gen", self.logger)
            self._gaussian_noise_driver_api = BaseSimulatorApi("gaussian_noise_driver", self.logger)
        # Firmware Mode
        else:
            vcc_source_select_grpc_info = gprc_driver_info.get("vcc_source_select", None)
            vcc_bite_grpc_info = gprc_driver_info.get("vcc_bite", None)
            vcc_bite_tone_gen_grpc_info = gprc_driver_info.get("vcc_bite_tone_gen", None)
            gaussian_noise_driver_grpc_info = gprc_driver_info.get("gaussian_noise_driver", None)

            if any(
                grpc_info is None
                for grpc_info in [vcc_source_select_grpc_info, vcc_bite_grpc_info, vcc_bite_tone_gen_grpc_info, gaussian_noise_driver_grpc_info]
            ):
                raise RuntimeError("One or more Firmware GRPC Infos not provided to VCCBiteManager when running in Firmware mode")

            # TODO: Figure out GRPC info field classes and addresses
            # TODO: These will likely not be configurable through deployment and will be static proto files in generated folder.
            # TODO: Temporarily using grpc_driver_info dict until correct design is clear, will eventually remoce
            self._vcc_source_select_api = FirmwareApi("vcc_source_select", self.logger, vcc_source_select_grpc_info, "localhost", "50051")
            self._vcc_bite_api = FirmwareApi("vcc_source_select", self.logger, vcc_bite_grpc_info, "localhost", "50051")
            self._vcc_bite_tone_gen_api = FirmwareApi("vcc_source_select", self.logger, vcc_bite_tone_gen_grpc_info, "localhost", "50051")
            self._gaussian_noise_driver_api = FirmwareApi("vcc_source_select", self.logger, gaussian_noise_driver_grpc_info, "localhost", "50051")

    def configure(self, config: VCCAllBandsConfigureVCCBiteSchema) -> int:
        """Configure the VCC Bite."""
        result = 0

        # TODO: Add configure functionality

        return result

    def deconfigure(self, config: VCCAllBandsDeconfigureVCCBiteSchema | None = None) -> int:
        """Deconfigure the VCC Bite."""
        result = 0

        # TODO: Add deconfigure functionality

        return result

    # TODO: Add start, stop, status methods
