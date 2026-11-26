from pydantic import Field
from ska_mid_cbf_fhs_common import FhsControllerBaseConfig, FhsDataclass


class VCCAllBandsConfigureScanPowerMeterConfig(FhsDataclass):
    """Dataclass representing a power meter configuration as part of the VCC All Bands ConfigureScan input parameter."""

    averaging: float
    flagging: int


class VCCAllBandsConfigureScanFSLaneConfig(FhsDataclass):
    """Dataclass representing an element of the fs_lanes property of the VCC All Bands ConfigureScan input parameter."""

    vlan_alias: str
    fs_id: int
    power_meter: VCCAllBandsConfigureScanPowerMeterConfig


class VCCAllBandsConfigureScanArgin(FhsControllerBaseConfig, FhsDataclass):
    """Dataclass representing the VCC All Bands ConfigureScan input parameter."""

    config_id: str
    expected_dish_id: str
    dish_sample_rate: int
    frequency_band: str
    frequency_band_offset_stream1: int
    vcc_gains_stream_1: list[float]
    noise_diode_transition_holdoff_count: int
    b123_power_meter: VCCAllBandsConfigureScanPowerMeterConfig
    b45_1_power_meter: VCCAllBandsConfigureScanPowerMeterConfig
    b45_2_power_meter: VCCAllBandsConfigureScanPowerMeterConfig
    fs_lanes: list[VCCAllBandsConfigureScanFSLaneConfig]
    frequency_band_offset_stream2: int = 0
    band_5_tuning: float = 0.0
    transaction_id: str | None = None


class VCCAllBandsAbortArgin(FhsDataclass):
    """Dataclass representing the VCC All Bands Abort input parameter."""

    subarray_id: int
    transaction_id: str | None = None


class VCCAllBandsGoToIdleArgin(FhsDataclass):
    """Dataclass representing the VCC All Bands GoToIdle input parameter."""

    subarray_id: int
    transaction_id: str | None = None


class VCCAllBandsAutoSetFilterGainsArgin(FhsDataclass):
    """Dataclass representing the VCC All Bands AutoSetFilterGains input parameter."""

    headrooms: list[float] | None = Field(default_factory=lambda: [3.0])
    transaction_id: str | None = None


class VCCAllBandsConfigureVCCBiteNoiseInfoPolarityConfig(FhsDataclass):
    """Dataclass representing Polarity config for Noise Info field in VCC Bite Config"""

    seed: int
    noise_std: int
    noise_mean: int


class VCCAllBandsConfigureVCCBiteNoiseInfoConfig(FhsDataclass):
    """Dataclass representing Noise Info config in VCC Bite Config"""

    pol_x: VCCAllBandsConfigureVCCBiteNoiseInfoPolarityConfig
    pol_y: VCCAllBandsConfigureVCCBiteNoiseInfoPolarityConfig


class VCCAllBandsConfigureVCCBiteNoiseDiodeConfig(FhsDataclass):
    """Dataclass representing Noise Diode config in VCC Bite Config"""

    dwell_time_us: int
    random_pattern_seed: int
    on_state_scaling_factor: float


class VCCAllBandsConfigureVCCBiteReceiverConfig(FhsDataclass):
    """Dataclass representing the VCC All Bands ConfigureVCCBite Receiver parameter."""

    dish_id: str
    dish_sample_rate: int
    noise_diode: VCCAllBandsConfigureVCCBiteNoiseDiodeConfig
    noise_info: VCCAllBandsConfigureVCCBiteNoiseInfoConfig | None = None


class VCCAllBandsConfigureVCCBiteSourceConfig(FhsDataclass):
    """Dataclass representing the VCC All Bands ConfigureVCCBite Sources parameter."""

    noise_info: VCCAllBandsConfigureVCCBiteNoiseInfoConfig
    pol_coupling_rho: float
    pol_Y_1_sample_delay: bool


class VCCAllBandsConfigureVCCBiteRfiInfoPolarityConfig(FhsDataclass):
    """Dataclass representing Polarity config for RFI in VCC Bite Config"""

    frequency: int
    scale: float


class VCCAllBandsConfigureVCCBiteRfiConfig(FhsDataclass):
    """Dataclass representing the VCC All Bands ConfigureVCCBite RFI parameter."""

    pol_x: VCCAllBandsConfigureVCCBiteRfiInfoPolarityConfig
    # TODO: pol_y is currently not used even if provided.
    # It should used in case there is an x and y bite tone gen driver,
    # but currently there is a single driver so pol_y is ignored
    pol_y: VCCAllBandsConfigureVCCBiteRfiInfoPolarityConfig | None = None


class VCCAllBandsConfigureVCCBiteArgin(FhsDataclass):
    """Dataclass representing the VCC All Bands ConfigureVCCBite input parameter."""

    receiver: VCCAllBandsConfigureVCCBiteReceiverConfig
    source: VCCAllBandsConfigureVCCBiteSourceConfig
    rfi: list[VCCAllBandsConfigureVCCBiteRfiConfig]
    utc_start_time: int
    band: int
    transaction_id: str | None = None


class VCCAllBandsDeconfigureVCCBiteArgin(FhsDataclass):
    """Dataclass representing the VCC All Bands DeconfigureVCCBite input parameter."""

    transaction_id: str | None = None
