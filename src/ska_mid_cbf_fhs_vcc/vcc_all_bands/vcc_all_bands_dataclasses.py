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

    headrooms: Optional[list[float]] = None
    transaction_id: Optional[str] = None
