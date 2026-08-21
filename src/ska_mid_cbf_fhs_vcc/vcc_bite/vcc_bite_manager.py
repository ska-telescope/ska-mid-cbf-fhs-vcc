import logging
from dataclasses import dataclass
from enum import IntEnum

from dataclasses_json import DataClassJsonMixin
from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_common.services.api.firmware_api import FirmwareApi
from ska_mid_cbf_fhs_common.services.grpc.grpc_client import GRPCInfo
from ska_mid_cbf_fhs_vcc_grpc_controller.generated import vcc_drivers_pb2, vcc_drivers_pb2_grpc

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAllBandsConfigureVCCBiteSchema, VCCAllBandsDeconfigureVCCBiteSchema
from ska_mid_cbf_fhs_vcc.vcc_bite.vcc_bite_simulator import (
    GaussianNoiseDriverSimulator,
    NoiseDiodeSimulator,
    PolarizationCouplerSimulator,
    SPFRxPacketizerSimulator,
    VCCBiteSimulator,
    VCCBiteToneGenSimulator,
    VCCSourceSelectSimulator,
)


class VCCSourceSelect(IntEnum):
    ETHERNET_200GB = 0
    VCC_BITE = 1
    ARKVILLE_PCIE = 2
    RESERVED = 3


@dataclass
class VCCSourceSelectApiConfig(DataClassJsonMixin):
    source_select: VCCSourceSelect
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
    magnitude: float
    band: int


@dataclass
class GaussianNoiseDriverApiConfig(DataClassJsonMixin):
    seed: int
    mean: int
    std_dev: int


@dataclass
class NoiseDiodeApiConfig(DataClassJsonMixin):
    sample_rate: int
    switching_period: float
    seed: int
    std_dev: float


@dataclass
class PolarizationCouplerApiConfig(DataClassJsonMixin):
    correlation_coefficient: float
    delay_enable: bool


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


@dataclass
class VCCSourceSelectStatus(DataClassJsonMixin):
    source_select: int
    test_select: bool


@dataclass
class VCCBiteStatus(DataClassJsonMixin):
    band: int
    start_time: int
    sample_rate: int
    speed: int


@dataclass
class VCCBiteToneGenStatus(DataClassJsonMixin):
    sample_rate: int
    frequency: int
    magnitude: float
    band: int


@dataclass
class GaussianNoiseDriverStatus(DataClassJsonMixin):
    seed: int
    mean: int
    std_dev: int


@dataclass
class NoiseDiodeStatus(DataClassJsonMixin):
    sample_rate: int
    switching_period: float
    seed: int
    std_dev: float


@dataclass
class PolarizationCouplerStatus(DataClassJsonMixin):
    correlation_coefficient: float
    delay_enable: bool


@dataclass
class SPFRxPacketizerStatus(DataClassJsonMixin):
    running: bool
    fifo_overflow_error: int
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
# status class that will be populated by the APIs and returned to provide the status of VCC Bite
##
@dataclass
class VCCBiteManagerStatus(DataClassJsonMixin):
    source_select: list[VCCSourceSelectStatus]
    bite_control: list[VCCBiteStatus]
    bite_tone_gen: list[VCCBiteToneGenStatus]
    bite_noise_gen_polX: list[GaussianNoiseDriverStatus]  # pylint: disable=invalid-name
    bite_noise_gen_polY: list[GaussianNoiseDriverStatus]  # pylint: disable=invalid-name
    bite_noise_diode_polX: list[NoiseDiodeStatus]  # pylint: disable=invalid-name
    bite_noise_diode_polY: list[NoiseDiodeStatus]  # pylint: disable=invalid-name
    polarization_coupler: list[PolarizationCouplerStatus]
    spfrx_packetizer: list[SPFRxPacketizerStatus]


class VCCBiteManager:
    """VCC Bite manager."""

    # TODO: Pass in card name through values file
    def __init__(self, logger: logging.Logger, simulation_mode: SimulationMode = SimulationMode.TRUE, card_name=""):
        self._simulation_mode = simulation_mode
        self.logger = logger
        self._vcc_source_select_apis: list[VCCSourceSelectSimulator] | list[FirmwareApi] = []
        self._vcc_bite_apis: list[VCCBiteSimulator] | list[FirmwareApi] = []
        self._vcc_bite_tone_gen_apis: list[VCCBiteToneGenSimulator] | list[FirmwareApi] = []
        self._gaussian_noise_driver_x_apis: list[GaussianNoiseDriverSimulator] | list[FirmwareApi] = []
        self._noise_diode_driver_x_apis: list[NoiseDiodeSimulator] | list[FirmwareApi] = []
        self._gaussian_noise_driver_y_apis: list[GaussianNoiseDriverSimulator] | list[FirmwareApi] = []
        self._noise_diode_driver_y_apis: list[NoiseDiodeSimulator] | list[FirmwareApi] = []
        self._polarization_coupler_apis: list[PolarizationCouplerSimulator] | list[FirmwareApi] = []
        self._spfrx_packetizer_apis: list[SPFRxPacketizerSimulator] | list[FirmwareApi] = []

        if self._simulation_mode == SimulationMode.TRUE:
            for i in range(0, 3):
                self._vcc_source_select_apis.append(VCCSourceSelectSimulator(f"{card_name}_receptor{i}_source_select", self.logger))
                self._vcc_bite_apis.append(VCCBiteSimulator(f"{card_name}_receptor{i}_bite_control", self.logger))
                self._vcc_bite_tone_gen_apis.append(VCCBiteToneGenSimulator(f"{card_name}_receptor{i}_bite_tone_gen", self.logger))
                self._gaussian_noise_driver_x_apis.append(GaussianNoiseDriverSimulator(f"{card_name}_receptor{i}_bite_noise_gen_polX", self.logger))
                self._gaussian_noise_driver_y_apis.append(GaussianNoiseDriverSimulator(f"{card_name}_receptor{i}_bite_noise_gen_polY", self.logger))
                self._noise_diode_driver_x_apis.append(NoiseDiodeSimulator(f"{card_name}_receptor{i}_bite_noise_diode_polX", self.logger))
                self._noise_diode_driver_y_apis.append(NoiseDiodeSimulator(f"{card_name}_receptor{i}_bite_noise_diode_polY", self.logger))
                self._polarization_coupler_apis.append(PolarizationCouplerSimulator(f"{card_name}_receptor{i}_polarization_coupler", self.logger))
                self._spfrx_packetizer_apis.append(SPFRxPacketizerSimulator(f"{card_name}_receptor{i}_spfrx_packetizer", self.logger))
        else:
            # Firmware Mode
            # TODO: Change grpc addresses to be deploy time constants instead of hardcoded values here
            # TODO: Fix Firmware API base class in fhs-common to get this mode working
            for i in range(0, 3):
                self._vcc_source_select_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_source_select_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    )
                )
                self._vcc_bite_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_control_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    ),
                )
                self._vcc_bite_tone_gen_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_tone_gen_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    ),
                )
                self._gaussian_noise_driver_x_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_noise_gen_polX_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    ),
                )
                self._gaussian_noise_driver_y_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_noise_gen_polY_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    ),
                )
                self._noise_diode_driver_x_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_noise_diode_polX_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    ),
                )
                self._noise_diode_driver_y_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_noise_diode_polY_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    ),
                )

                self._polarization_coupler_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_polarization_coupler_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    )
                )

                self._spfrx_packetizer_apis.append(
                    FirmwareApi(
                        f"{card_name}_receptor{i}_bite_spfrx_packetizer_driver",
                        self.logger,
                        GRPCInfo(vcc_drivers_pb2, vcc_drivers_pb2_grpc, vcc_drivers_pb2_grpc.VccFpgaDriverStub),
                        "0.0.0.0",
                        "50051",
                    )
                )

    def configure(self, config: VCCAllBandsConfigureVCCBiteSchema) -> int:
        """Configure the VCC Bite."""
        result = 0

        # VCC Source Select Config
        vcc_source_select_config = VCCSourceSelectApiConfig(
            source_select=VCCSourceSelect.VCC_BITE,
            # TODO: In the future, Fix this default value and possibly get from config
            test_select=True,
        )
        for api in self._vcc_source_select_apis:
            result = api.configure(config=vcc_source_select_config)
            if result == 1:
                self.logger.error("Could not configure VCC Source Select")
                return result

        # VCC Bite Config
        vcc_bite_config = VCCBiteApiConfig(
            band=config.band,
            start_time=config.utc_start_time,
            sample_rate=config.receiver.dish_sample_rate,
            # TODO: Remove speed eventually
            speed=1,
        )
        for api in self._vcc_bite_apis:
            result = api.configure(config=vcc_bite_config)
            if result == 1:
                self.logger.error("Could not configure VCC Bite")
                return result

        # VCC Bite Tone Gen Config
        vcc_bite_tone_gen_config = VCCBiteToneGenApiConfig(
            sample_rate=config.receiver.dish_sample_rate,
            # TODO: If y driver is added, use the y values
            frequency=config.rfi[0].pol_x.frequency,
            magnitude=config.rfi[0].pol_x.scale,
            band=config.band,
        )
        for api in self._vcc_bite_tone_gen_apis:
            result = api.configure(vcc_bite_tone_gen_config)
            if result == 1:
                self.logger.error("Could not configure VCC Bite Tone Gen")
                return result

        # Gaussian Noise Driver Config
        gaussian_noise_driver_x_config = GaussianNoiseDriverApiConfig(
            seed=config.source.noise_info.pol_x.seed,
            mean=config.source.noise_info.pol_x.noise_mean,
            std_dev=config.source.noise_info.pol_x.noise_std,
        )
        for api in self._gaussian_noise_driver_x_apis:
            result = api.configure(gaussian_noise_driver_x_config)
            if result == 1:
                self.logger.error("Could not configure Gaussian Noise Driver X")
                return result
        gaussian_noise_driver_y_config = GaussianNoiseDriverApiConfig(
            seed=config.source.noise_info.pol_y.seed,
            mean=config.source.noise_info.pol_y.noise_mean,
            std_dev=config.source.noise_info.pol_y.noise_std,
        )
        for api in self._gaussian_noise_driver_y_apis:
            result = api.configure(gaussian_noise_driver_y_config)
            if result == 1:
                self.logger.error("Could not configure Gaussian Noise Driver Y")
                return result

        # Noise Diode config
        noise_diode_x_config = NoiseDiodeApiConfig(
            sample_rate=config.receiver.dish_sample_rate,
            switching_period=config.receiver.noise_diode.dwell_time_us / 1e6,
            seed=config.source.noise_info.pol_x.seed,
            std_dev=config.source.noise_info.pol_x.noise_std,
        )
        for api in self._noise_diode_driver_x_apis:
            result = api.configure(noise_diode_x_config)
            if result == 1:
                self.logger.error("Could not configure Noise Diode X")
                return result
        noise_diode_y_config = NoiseDiodeApiConfig(
            sample_rate=config.receiver.dish_sample_rate,
            switching_period=config.receiver.noise_diode.dwell_time_us / 1e6,
            seed=config.source.noise_info.pol_y.seed,
            std_dev=config.source.noise_info.pol_y.noise_std,
        )
        for api in self._noise_diode_driver_y_apis:
            result = api.configure(noise_diode_y_config)
            if result == 1:
                self.logger.error("Could not configure Noise Diode Y")
                return result

        # Polarization Coupler Config
        polarization_coupler_config = PolarizationCouplerApiConfig(
            correlation_coefficient=config.source.pol_coupling_rho,
            delay_enable=config.source.pol_Y_1_sample_delay,
        )
        for api in self._polarization_coupler_apis:
            result = api.configure(config=polarization_coupler_config)
            if result == 1:
                self.logger.error("Could not configure Polarization Coupler")
                return result

        # TODO: Fix default values here
        # SPFRx Packetizer Config
        spfrx_packetizer_config = SPFRxPacketizerApiConfig(
            local_mac=0x112233445566,
            remote_mac=0x778899AABBCC,
            ethertype=0xFEED,
            dish_id=config.receiver.dish_id,
            hw_src_id=0,
            band=config.band,
            sample_rate=config.receiver.dish_sample_rate,
            sample_rate_b=config.receiver.dish_sample_rate,
            noise_diode_rising_holdoff=0.0,
            noise_diode_rising_holdoff_b=0.0,
        )
        for api in self._spfrx_packetizer_apis:
            result = api.configure(config=spfrx_packetizer_config)
            if result == 1:
                self.logger.error("Could not configure SPFRx Packetizer")
                return result

        return result

    def deconfigure(self, config: VCCAllBandsDeconfigureVCCBiteSchema | None = None) -> int:
        """Deconfigure the VCC Bite."""
        result = 0

        if config is None:
            config = {}

        # VCC Source Select
        for api in self._vcc_source_select_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure VCC Source Select")
                return result

        # VCC Bite
        for api in self._vcc_bite_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure VCC Bite")
                return result

        # VCC Bite Tone Gen
        for api in self._vcc_bite_tone_gen_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure VCC Bite Tone Gen")
                return result

        # Gaussian Noise Driver
        for api in self._gaussian_noise_driver_x_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure Gaussian Noise Driver X")
                return result
        for api in self._gaussian_noise_driver_y_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure Gaussian Noise Driver Y")
                return result

        # Noise Diode
        for api in self._noise_diode_driver_x_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure Noise Diode X")
                return result
        for api in self._noise_diode_driver_y_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure Noise Diode Y")
                return result

        # Polarization Coupler
        for api in self._polarization_coupler_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure Polarization Coupler")
                return result

        # SPFRx Packetizer
        for api in self._spfrx_packetizer_apis:
            result = api.deconfigure(config=config)
            if result == 1:
                self.logger.error("Could not deconfigure SPFRx Packetizer")
                return result

        return result

    def start(self) -> int:
        """Start the VCC Bite."""
        result = 0

        # VCC Source Select
        for api in self._vcc_source_select_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start VCC Source Select")
                return result

        # VCC Bite
        for api in self._vcc_bite_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start VCC Bite")
                return result

        # VCC Bite Tone Gen
        for api in self._vcc_bite_tone_gen_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start VCC Bite Tone Gen")
                return result

        # Gaussian Noise Driver
        for api in self._gaussian_noise_driver_x_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start Gaussian Noise Driver X")
                return result
        for api in self._gaussian_noise_driver_y_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start Gaussian Noise Driver Y")
                return result

        # Noise Diode
        for api in self._noise_diode_driver_x_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start Noise Diode X")
                return result
        for api in self._noise_diode_driver_y_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start Noise Diode Y")
                return result

        # Polarization Coupler
        for api in self._polarization_coupler_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start Polarization Coupler")
                return result

        # SPFRx Packetizer
        for api in self._spfrx_packetizer_apis:
            result = api.start()
            if result == 1:
                self.logger.error("Could not start SPFRx Packetizer")
                return result

        return result

    def stop(self, force: bool = False) -> int:
        """Stop the VCC Bite."""
        result = 0

        # VCC Source Select
        for api in self._vcc_source_select_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop VCC Source Select")
                return result

        # VCC Bite
        for api in self._vcc_bite_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop VCC Bite")
                return result

        # VCC Bite Tone Gen
        for api in self._vcc_bite_tone_gen_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop VCC Bite Tone Gen")
                return result

        # Gaussian Noise Driver
        for api in self._gaussian_noise_driver_x_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop Gaussian Noise Driver X")
                return result
        for api in self._gaussian_noise_driver_y_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop Gaussian Noise Driver Y")
                return result

        # Noise Diode
        for api in self._noise_diode_driver_x_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop Noise Diode X")
                return result
        for api in self._noise_diode_driver_y_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop Noise Diode Y")
                return result

        # Polarization Coupler
        for api in self._polarization_coupler_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop Polarization Coupler")
                return result

        # Spfrx Packetizer
        for api in self._spfrx_packetizer_apis:
            result = api.stop()
            if result == 1:
                self.logger.error("Could not stop Spfrx Packetizer")
                return result

        return result

    def status(self, clear: bool = False) -> VCCBiteManagerStatus | None:
        """Get status for all the VCC Bite components."""
        # VCC Source Select
        vcc_source_select_statuses = []
        for api in self._vcc_source_select_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from VCC Source Select")
                return status
            vcc_source_select_statuses.append(VCCSourceSelectStatus.from_dict(status))

        # VCC Bite
        vcc_bite_statues = []
        for api in self._vcc_bite_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from VCC Bite")
                return status
            vcc_bite_statues.append(VCCBiteStatus.from_dict(status))

        # VCC Bite Tone Gen
        vcc_bite_tone_gen_statuses = []
        for api in self._vcc_bite_tone_gen_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from VCC Bite Tone Gen")
                return status
            vcc_bite_tone_gen_statuses.append(VCCBiteToneGenStatus.from_dict(status))

        # Gaussian Noise Driver
        gaussian_noise_driver_x_statuses = []
        for api in self._gaussian_noise_driver_x_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from Gaussian Noise Driver X")
                return status
            gaussian_noise_driver_x_statuses.append(GaussianNoiseDriverStatus.from_dict(status))
        gaussian_noise_driver_y_statuses = []
        for api in self._gaussian_noise_driver_y_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from Gaussian Noise Driver Y")
                return status
            gaussian_noise_driver_y_statuses.append(GaussianNoiseDriverStatus.from_dict(status))

        # Noise Diode
        noise_diode_driver_x_statuses = []
        for api in self._noise_diode_driver_x_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from Noise Diode X")
                return status
            noise_diode_driver_x_statuses.append(NoiseDiodeStatus.from_dict(status))
        noise_diode_driver_y_statuses = []
        for api in self._noise_diode_driver_y_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from Noise Diode Y")
                return status
            noise_diode_driver_y_statuses.append(NoiseDiodeStatus.from_dict(status))

        # Polarization Coupler
        polarization_coupler_statuses = []
        for api in self._polarization_coupler_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from Polarization Coupler")
                return status
            polarization_coupler_statuses.append(PolarizationCouplerStatus.from_dict(status))

        # Spfrx Packetizer
        spfrx_packetizer_statuses = []
        for api in self._spfrx_packetizer_apis:
            status = api.status(clear=clear)
            if status is None:
                self.logger.error("Could not get status from SPFRx Packetizer")
                return status
            spfrx_packetizer_statuses.append(SPFRxPacketizerStatus.from_dict(status))

        return VCCBiteManagerStatus(
            source_select=vcc_source_select_statuses,
            bite_control=vcc_bite_statues,
            bite_tone_gen=vcc_bite_tone_gen_statuses,
            bite_noise_gen_polX=gaussian_noise_driver_x_statuses,
            bite_noise_gen_polY=gaussian_noise_driver_y_statuses,
            bite_noise_diode_polX=noise_diode_driver_x_statuses,
            bite_noise_diode_polY=noise_diode_driver_y_statuses,
            polarization_coupler=polarization_coupler_statuses,
            spfrx_packetizer=spfrx_packetizer_statuses,
        )
