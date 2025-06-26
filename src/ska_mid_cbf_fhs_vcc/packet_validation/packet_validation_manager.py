from dataclasses import dataclass
from logging import Logger

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import SimulationMode

from ska_mid_cbf_fhs_vcc.ip_block_manager.base_ip_block_manager import BaseIPBlockManager
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_simulator import PacketValidationSimulator


@dataclass_json
@dataclass
class PacketValidationConfig:
    drop_dst_mac: bool = True
    drop_src_mac: bool = True
    drop_ethertype: bool = True
    drop_antenna_id: bool = True
    clr_cnt: bool = True
    exp_dst_mac: np.uint64 = 0
    exp_src_mac: np.uint64 = 0
    exp_ethertype: np.uint64 = 0
    exp_antenna_id: np.uint64 = 0


##
# status class that will be populated by the APIs and returned to provide the status of Packet Validation
##
@dataclass_json
@dataclass
class PacketValidationStatus:
    drop_dst_mac: bool = True
    drop_src_mac: bool = True
    drop_ethertype: bool = True
    drop_antenna_id: bool = True
    egress_cnt: np.uint32 = 0
    ingress_error_cnt: np.uint32 = 0
    size_error_cnt: np.uint32 = 0
    exp_dst_mac: np.uint64 = 0
    last_wrong_dst_mac: np.uint64 = 0
    wrong_dst_mac_cnt: np.uint32 = 0
    exp_src_mac: np.uint64 = 0
    last_wrong_src_mac: np.uint64 = 0
    wrong_src_mac_cnt: np.uint32 = 0
    exp_ethertype: np.uint64 = 0
    last_wrong_ethertype: np.uint64 = 0
    wrong_ethertype_cnt: np.uint32 = 0
    exp_antenna_id: np.uint64 = 0
    last_wrong_antenna_id: np.uint64 = 0
    wrong_antenna_id_cnt: np.uint32 = 0


class PacketValidationManager(BaseIPBlockManager):
    """Mock Packet Validation IP block manager."""

    def __init__(
        self,
        ip_block_id: str,
        bitstream_path: str,
        bitstream_id: str,
        bitstream_version: str,
        firmware_ip_block_id: str,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        emulator_ip_block_id: str | None = None,
        emulator_id: str | None = None,
        emulator_base_url: str | None = None,
        logger: Logger | None = None,
    ):
        super().__init__(
            ip_block_id,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            PacketValidationSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logger,
        )

    def configure(self, config: PacketValidationConfig):
        """Configure the Packet Validation."""
        return super().configure(config.to_dict())

    def deconfigure(self, config: PacketValidationConfig | None):
        """Deconfigure the Packet Validation."""
        if config is None:
            return super().recover()
        return super().deconfigure(config.to_dict())
