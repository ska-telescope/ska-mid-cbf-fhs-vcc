from dataclasses import field
from typing import Optional

from dataclasses_json import DataClassJsonMixin
from pydantic.dataclasses import dataclass
from ska_mid_cbf_fhs_common import FhsControllerBaseConfig


@dataclass
class VCCAllBandsConfigureScanPowerMeterConfig(DataClassJsonMixin):
    """Dataclass representing a power meter configuration as part of the VCC All Bands ConfigureScan input parameter."""

    averaging_time: int
    flagging: int


@dataclass
class VCCAllBandsConfigureScanFSLaneConfig(DataClassJsonMixin):
    """Dataclass representing an element of the fs_lanes property of the VCC All Bands ConfigureScan input parameter."""

    vlan_id: int
    fs_id: int
    averaging_time: int
    flagging: int


@dataclass
class VCCAllBandsConfigureScanConfig(FhsControllerBaseConfig, DataClassJsonMixin):
    """Dataclass representing the VCC All Bands ConfigureScan input parameter."""

    config_id: str
    expected_dish_id: str
    dish_sample_rate: int
    samples_per_frame: int
    frequency_band: str
    frequency_band_offset_stream_1: int
    vcc_gain: list[float]
    noise_diode_transition_holdoff_seconds: int
    b123_pwrm: VCCAllBandsConfigureScanPowerMeterConfig
    b45a_pwrm: VCCAllBandsConfigureScanPowerMeterConfig
    b5b_pwrm: VCCAllBandsConfigureScanPowerMeterConfig
    fs_lanes: list[VCCAllBandsConfigureScanFSLaneConfig]
    frequency_band_offset_stream_2: int = 0
    band_5_tuning: float = 0.0
    transaction_id: Optional[str] = None


@dataclass
class VCCAllBandsAutoSetFilterGainsSchema(DataClassJsonMixin):
    """Dataclass representing the VCC All Bands AutoSetFilterGains input parameter."""

    headrooms: Optional[list[float]] = field(default_factory=lambda: [3.0])
    transaction_id: Optional[str] = None


@dataclass
class VCCAllBandsConfigureVCCBiteNoiseInfoPolarityConfig(DataClassJsonMixin):
    # TODO: Fill in the docstring here
    """"""

    seed: int
    noise_std: int
    noise_mean: int


@dataclass
class VCCAllBandsConfigureVCCBiteNoiseInfoConfig(DataClassJsonMixin):
    # TODO: Fill in the docstring here
    """"""

    pol_x: VCCAllBandsConfigureVCCBiteNoiseInfoPolarityConfig
    pol_y: VCCAllBandsConfigureVCCBiteNoiseInfoPolarityConfig


@dataclass
class VCCAllBandsConfigureVCCBiteNoiseDiodeConfig(DataClassJsonMixin):
    # TODO: Fill in the docstring here
    """"""

    dwell_time_us: int
    random_pattern_seed: int
    on_state_scaling_factor: float


@dataclass
class VCCAllBandsConfigureVCCBiteReceiverConfig(DataClassJsonMixin):
    """Dataclass representing the VCC All Bands ConfigureVCCBite Receiever parameter."""

    dish_id: str
    dish_sample_rate_MHz: int  # pylint: disable=invalid-name
    noise_diode: VCCAllBandsConfigureVCCBiteNoiseDiodeConfig


@dataclass
class VCCAllBandsConfigureVCCBiteSourceConfig(DataClassJsonMixin):
    """Dataclass representing the VCC All Bands ConfigureVCCBite Sources parameter."""

    noise_info: VCCAllBandsConfigureVCCBiteNoiseInfoConfig
    pol_coupling_rho: float
    pol_Y_1_sample_delay: bool  # pylint: disable=invalid-name


@dataclass
class VCCAllBandsConfigureVCCBiteRfiInfoPolarityConfig(DataClassJsonMixin):
    # TODO: Fill in the docstring here
    """"""

    frequency: int
    scale: int


@dataclass
class VCCAllBandsConfigureVCCBiteRfiConfig(DataClassJsonMixin):
    """Dataclass representing the VCC All Bands ConfigureVCCBite RFI parameter."""

    pol_x: VCCAllBandsConfigureVCCBiteRfiInfoPolarityConfig
    pol_y: VCCAllBandsConfigureVCCBiteRfiInfoPolarityConfig


@dataclass
class VCCAllBandsConfigureVCCBiteSchema(DataClassJsonMixin):
    """Dataclass representing the VCC All Bands ConfigureVCCBite input parameter."""

    receiver: VCCAllBandsConfigureVCCBiteReceiverConfig
    source: VCCAllBandsConfigureVCCBiteSourceConfig
    rfi: list[VCCAllBandsConfigureVCCBiteRfiConfig]
    utc_start_time: int
    band: int
    transaction_id: Optional[str] = None


@dataclass
class VCCAllBandsDeconfigureVCCBiteSchema(DataClassJsonMixin):
    """Dataclass representing the VCC All Bands DeconfigureVCCBite input parameter."""

    transaction_id: Optional[str] = None
