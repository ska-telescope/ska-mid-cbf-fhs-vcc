from pydantic import Field
from ska_mid_cbf_fhs_common import BaseIPBlockManager, FhsDataclass, UInt8, UInt16, UInt32, UInt64

from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_simulator import VCCStreamMergeSimulator


class VCCStreamMergeConfig(FhsDataclass):
    mac_destination: UInt64  # Destination MAC Address.
    vid: UInt16  # VLAN identifier, for unique VLAN identification.
    vcc_id: UInt16  # Influences the Source MAC address.
    fs_id: UInt16  # Frequency slice identifier.
    fs_index: UInt8  # Index of the FS within the Stream Merge block (1 to 13).


class VCCStreamMergeStatusLutEntry(FhsDataclass):
    mac_destination: UInt64  # Destination MAC Address.
    vid: UInt16  # VLAN identifier.
    vcc_id: UInt16  # VCC ID.
    fs_id: UInt16  # Frequency Slice ID.


##
# status class that will be populated by the APIs and returned to provide the status of VCC Stream Merge
##
class VCCStreamMergeStatus(FhsDataclass):
    mac_destination: UInt64  # Destination MAC Address.
    vid: UInt16  # VLAN identifier.
    vcc_id: UInt16  # VCC ID.
    fs_id: UInt16  # Frequency Slice ID.
    fs_index: UInt8  # Frequency Slice ID.
    packet_count: UInt32  # Packet count.
    lut: list[VCCStreamMergeStatusLutEntry | None]


class VCCStreamMergeConfigureArgin(FhsDataclass):
    transaction_id: str | None = None
    fs_lane_configs: list[VCCStreamMergeConfig] = Field(default_factory=list)


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
