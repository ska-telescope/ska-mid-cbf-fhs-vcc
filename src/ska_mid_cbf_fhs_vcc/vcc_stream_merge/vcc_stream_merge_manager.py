from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_simulator import VCCStreamMergeSimulator


@dataclass
class VCCStreamMergeConfig(DataClassJsonMixin):
    mac_destination: int  # Destination MAC Address.
    vid: int  # VLAN identifier, for unique VLAN identification.
    vcc_id: int  # Influences the Source MAC address.
    fs_id: int  # Frequency slice identifier.
    fs_index: int  # Index of the FS within the Stream Merge block (1 to 13).


##
# status class that will be populated by the APIs and returned to provide the status of VCC Stream Merge
##
@dataclass
class VCCStreamMergeStatus(DataClassJsonMixin):
    mac_destination: int  # Destination MAC Address.
    vid: int  # VLAN identifier.
    vcc_id: int  # VCC ID.
    fs_id: int  # Frequency Slice ID.
    timestamp: int  # Timestamp.
    psn: list[int]  # Packet sequence number.
    packet_count: int  # Packet count.
    diag_stop_monitor: int


@dataclass
class VCCStreamMergeConfigureArgin(DataClassJsonMixin):
    transaction_id: str | None = None
    fs_lane_configs: list[VCCStreamMergeConfig] = field(default_factory=list)


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
