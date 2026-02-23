from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from dataclasses_json import DataClassJsonMixin
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_simulator import VCCStreamMergeSimulator


@dataclass
class VCCStreamMergeConfig(DataClassJsonMixin):
    vid: np.uint16  # VLAN identifier, for unique VLAN identification.
    vcc_id: np.uint16  # Influences the Source MAC address.
    fs_id: np.uint16  # Frequency slice identifier.


##
# status class that will be populated by the APIs and returned to provide the status of VCC Stream Merge
##
@dataclass
class VCCStreamMergeStatus(DataClassJsonMixin):
    mac_source_register: np.uint64  # Source MAC Address.
    vid_register: np.uint16  # VLAN identifier.
    flags_register: np.uint16  # Various flags, currently used for noise diode state.
    psn_register: np.uint16  # Packet sequence number.
    packet_count_register: np.uint32  # Packet count.


@dataclass
class VCCStreamMergeConfigureArgin(DataClassJsonMixin):
    transaction_id: Optional[str] = None
    fs_lane_configs: list[VCCStreamMergeConfig] = field(default_factory=lambda: [])


class VCCStreamMergeManager(BaseIPBlockManager[VCCStreamMergeConfig, VCCStreamMergeStatus]):
    """VCC Stream Merge IP block manager."""

    @property
    def config_dataclass(self) -> type[VCCStreamMergeConfig]:
        """:obj:`type[VCCStreamMergeConfig]`: The configuration dataclass for the VCC Stream Merge block."""
        return VCCStreamMergeConfig

    @property
    def status_dataclass(self) -> type[VCCStreamMergeStatus]:
        """:obj:`type[VCCStreamMergeStatus]`: The status dataclass for the VCC Stream Merge block."""
        return VCCStreamMergeStatus

    @property
    def simulator_api_class(self) -> type[VCCStreamMergeSimulator]:
        """:obj:`type[VCCStreamMergeSimulator]`: The simulator API class for the VCC Stream Merge block."""
        return VCCStreamMergeSimulator

    def configure(self, config: VCCStreamMergeConfigureArgin) -> int:
        """Configure the VCC Stream Merge."""
        result = 0
        for lane_config in config.fs_lane_configs:
            result = super().configure(lane_config)
            if result == 1:
                break
        return result

    def deconfigure(self, config: VCCStreamMergeConfigureArgin | None = None) -> int:
        """Deconfigure the VCC Stream Merge."""
        if config is None:
            return super().recover()
        result = 0
        for lane_config in config.fs_lane_configs:
            result = super().deconfigure(lane_config)
            if result == 1:
                break
        return result
