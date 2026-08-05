import logging
from dataclasses import dataclass
from enum import IntEnum

from dataclasses_json import DataClassJsonMixin
from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_common.services.api.firmware_api import FirmwareApi

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
    pol_Y_1_sample_delay: bool  # pylint: disable=invalid-name


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
    magnitude: int
    band: int


@dataclass
class GaussianNoiseDriverStatus(DataClassJsonMixin):
    seed: int
    mean: int
    std_dev: int


@dataclass
class NoiseDiodeStatus(DataClassJsonMixin):
    # TODO: Confirm if this field is needed, it exists in the driver on gitlab nrc config schema: sample_rate
    switching_period: float
    seed: int
    std_dev: float


@dataclass
class PolarizationCouplerStatus(DataClassJsonMixin):
    # TODO: Confirm if these fields are correct. They are different from the ones on NRC gitlab
    # TODO: NRC gitlab has delay_enable: bool, correlation_coefficient: float
    # TODO: Confirm if they are the same but just with differnt names
    pol_coupling_rho: float
    pol_Y_1_sample_delay: bool  # pylint: disable=invalid-name


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
    polarization_coupler: PolarizationCouplerStatus
    spfrx_packetizer: SPFRxPacketizerStatus


class VCCBiteManager:
    """VCC Bite manager."""

    def __init__(self, logger: logging.Logger, simulation_mode: SimulationMode = SimulationMode.TRUE):
        self._simulation_mode = simulation_mode
        self.logger = logger
        self._vcc_source_select_apis: list[VCCSourceSelectSimulator] | list[FirmwareApi] = []
        self._vcc_bite_apis: list[VCCBiteSimulator] | list[FirmwareApi] = []
        self._vcc_bite_tone_gen_apis: list[VCCBiteToneGenSimulator] | list[FirmwareApi] = []
        self._gaussian_noise_driver_x_apis: list[GaussianNoiseDriverSimulator] | list[FirmwareApi] = []
        self._noise_diode_driver_x_apis: list[NoiseDiodeSimulator] | list[FirmwareApi] = []
        self._gaussian_noise_driver_y_apis: list[GaussianNoiseDriverSimulator] | list[FirmwareApi] = []
        self._noise_diode_driver_y_apis: list[NoiseDiodeSimulator] | list[FirmwareApi] = []
        self._polarization_coupler_api: PolarizationCouplerSimulator | FirmwareApi | None = None
        self._spfrx_packetizer_api: SPFRxPacketizerSimulator | FirmwareApi | None = None

        if self._simulation_mode == SimulationMode.TRUE:
            for i in range(0, 3):
                self._vcc_source_select_apis.append(VCCSourceSelectSimulator(f"{i}_source_select", self.logger))
                self._vcc_bite_apis.append(VCCBiteSimulator(f"{i}_bite_control", self.logger))
                self._vcc_bite_tone_gen_apis.append(VCCBiteToneGenSimulator(f"{i}_bite_tone_gen", self.logger))
                self._gaussian_noise_driver_x_apis.append(GaussianNoiseDriverSimulator(f"{i}_bite_noise_gen_polX", self.logger))
                self._gaussian_noise_driver_y_apis.append(GaussianNoiseDriverSimulator(f"{i}_bite_noise_gen_polY", self.logger))
                self._noise_diode_driver_x_apis.append(NoiseDiodeSimulator(f"{i}_bite_noise_diode_polX", self.logger))
                self._noise_diode_driver_y_apis.append(NoiseDiodeSimulator(f"{i}_bite_noise_diode_polY", self.logger))

            self._polarization_coupler_api = PolarizationCouplerSimulator("polarization_coupler", self.logger)
            self._spfrx_packetizer_api = SPFRxPacketizerSimulator("spfrx_packetizer", self.logger)
        else:
            # Firmware Mode
            # TODO: Initialise all driver apis as FirmwareAPIs with proper grpc info fields
            return

    def configure(self, config: VCCAllBandsConfigureVCCBiteSchema) -> int:
        """Configure the VCC Bite."""
        result = 0

        # VCC Source Select Config
        vcc_source_select_config = VCCSourceSelectApiConfig(
            source_select=VCCSourceSelect.VCC_BITE,
            # TODO: Fix this default value and get from config
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
            sample_rate=config.receiver.dish_sample_rate_MHz,
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
            sample_rate=config.receiver.dish_sample_rate_MHz,
            # TODO: Figure out the driver situations and add the y ones
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
            # TODO: switching_period=
            switching_period=0.0,
            seed=config.source.noise_info.pol_x.seed,
            std_dev=config.source.noise_info.pol_x.noise_std,
        )
        for api in self._noise_diode_driver_x_apis:
            result = api.configure(noise_diode_x_config)
            if result == 1:
                self.logger.error("Could not configure Noise Diode X")
                return result
        noise_diode_y_config = NoiseDiodeApiConfig(
            # TODO: switching_period=
            switching_period=0.0,
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
            # TODO: Confirm if these fields are correct. They are different from the ones on NRC gitlab
            # TODO: NRC gitlab has delay_enable: bool, correlation_coefficient: float
            # TODO: Confirm if they are the same but just with differnt names
            pol_coupling_rho=config.source.pol_coupling_rho,
            pol_Y_1_sample_delay=config.source.pol_Y_1_sample_delay,
        )
        result = self._polarization_coupler_api.configure(config=polarization_coupler_config)
        if result == 1:
            self.logger.error("Could not configure Polarization Coupler")
            return result

        # TODO: Spfrx Packetizer Config
        # spfrx_packetizer_config = SPFRxPacketizerApiConfig()
        # self._spfrx_packetizer_api.configure(config=spfrx_packetizer_config)

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
        result = self._polarization_coupler_api.deconfigure(config=config)
        if result == 1:
            self.logger.error("Could not deconfigure Polarization Coupler")
            return result

        # TODO: Spfrx Packetizer
        # self._spfrx_packetizer_api.deconfigure(config=config)

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
        result = self._polarization_coupler_api.start()
        if result == 1:
            self.logger.error("Could not start Polarization Coupler")
            return result

        # TODO: Spfrx Packetizer
        # self._spfrx_packetizer_api.start()

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
        result = self._polarization_coupler_api.stop()
        if result == 1:
            self.logger.error("Could not stop Polarization Coupler")
            return result

        # TODO: Spfrx Packetizer
        # self._spfrx_packetizer_api.stop()

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
        polarization_coupler_status = self._polarization_coupler_api.status(clear=clear)
        if polarization_coupler_status is None:
            self.logger.error("Could not get status from Polarization Coupler")
            return polarization_coupler_status
        polarization_coupler_status = PolarizationCouplerStatus.from_dict(polarization_coupler_status)

        # TODO: Spfrx Packetizer
        spfrx_packetizer_status = self._spfrx_packetizer_api.status(clear=clear)
        if spfrx_packetizer_status is None:
            self.logger.error("Could not get status from SPFRx Packetizer")
            return spfrx_packetizer_status
        spfrx_packetizer_status = SPFRxPacketizerStatus.from_dict(spfrx_packetizer_status)

        return VCCBiteManagerStatus(
            source_select=vcc_source_select_statuses,
            bite_control=vcc_bite_statues,
            bite_tone_gen=vcc_bite_tone_gen_statuses,
            bite_noise_gen_polX=gaussian_noise_driver_x_statuses,
            bite_noise_gen_polY=gaussian_noise_driver_y_statuses,
            bite_noise_diode_polX=noise_diode_driver_x_statuses,
            bite_noise_diode_polY=noise_diode_driver_y_statuses,
            polarization_coupler=polarization_coupler_status,
            spfrx_packetizer=spfrx_packetizer_status,
        )
