from ska_mid_cbf_fhs_common import BaseIPBlockManager, FhsDataclass, UInt32, UInt64, non_blocking

from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_simulator import PacketValidationSimulator


class PacketValidationConfig(FhsDataclass):
    drop_dst_mac: bool = True
    drop_src_mac: bool = True
    drop_ethertype: bool = True
    drop_antenna_id: bool = True
    clr_cnt: bool = True
    exp_dst_mac: UInt64 = 0
    exp_src_mac: UInt64 = 0
    exp_ethertype: UInt64 = 0
    exp_antenna_id: UInt64 = 0


##
# status class that will be populated by the APIs and returned to provide the status of Packet Validation
##
class PacketValidationStatus(FhsDataclass):
    drop_dst_mac: bool = True
    drop_src_mac: bool = True
    drop_ethertype: bool = True
    drop_antenna_id: bool = True
    egress_cnt: UInt32 = 0
    ingress_error_cnt: UInt32 = 0
    size_error_cnt: UInt32 = 0
    exp_dst_mac: UInt64 = 0
    last_wrong_dst_mac: UInt64 = 0
    wrong_dst_mac_cnt: UInt32 = 0
    exp_src_mac: UInt64 = 0
    last_wrong_src_mac: UInt64 = 0
    wrong_src_mac_cnt: UInt32 = 0
    exp_ethertype: UInt64 = 0
    last_wrong_ethertype: UInt64 = 0
    wrong_ethertype_cnt: UInt32 = 0
    exp_antenna_id: UInt64 = 0
    last_wrong_antenna_id: UInt64 = 0
    wrong_antenna_id_cnt: UInt32 = 0


class PacketValidationManager(BaseIPBlockManager[PacketValidationConfig, PacketValidationStatus]):
    """Packet Validation IP block manager."""

    @property
    def config_dataclass(self) -> type[PacketValidationConfig]:
        """:obj:`type[PacketValidationConfig]`: The configuration dataclass for the Packet Validation block."""
        return PacketValidationConfig

    @property
    def status_dataclass(self) -> type[PacketValidationStatus]:
        """:obj:`type[PacketValidationStatus]`: The status dataclass for the Packet Validation block."""
        return PacketValidationStatus

    @property
    def simulator_api_class(self) -> type[PacketValidationSimulator]:
        """:obj:`type[PacketValidationSimulator]`: The simulator API class for the Packet Validation block."""
        return PacketValidationSimulator

    def deconfigure(self, config: PacketValidationConfig | None):
        """Deconfigure the Packet Validation."""
        if config is None:
            return super().recover()
        return super().deconfigure(config)

    @non_blocking
    def start(self) -> int:
        return super().start()

    @non_blocking
    def stop(self) -> int:
        return super().stop()
