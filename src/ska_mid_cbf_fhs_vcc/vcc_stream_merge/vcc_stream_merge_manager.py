from dataclasses import dataclass, field

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import SimulationMode

from ska_mid_cbf_fhs_common import BaseIPBlockManager
from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_simulator import VCCStreamMergeSimulator


@dataclass_json
@dataclass
class VCCStreamMergeConfig:
    vid: np.uint16  # VLAN identifier, for unique VLAN identification.
    vcc_id: np.uint16  # Influences the Source MAC address.
    fs_id: np.uint16  # Frequency slice identifier.


##
# status class that will be populated by the APIs and returned to provide the status of VCC Stream Merge
##
@dataclass
class VCCStreamMergeStatus:
    mac_source_register: np.uint64  # Source MAC Address.
    vid_register: np.uint16  # VLAN identifier.
    flags_register: np.uint16  # Various flags, currently used for noise diode state.
    psn_register: np.uint16  # Packet sequence number.
    packet_count_register: np.uint32  # Packet count.


@dataclass_json
@dataclass
class VCCStreamMergeConfigureArgin:
    fs_lane_configs: list[VCCStreamMergeConfig] = field(default_factory=lambda: [])


class VCCStreamMergeManager(BaseIPBlockManager):
    """Mock VCC Stream Merge IP block manager."""

    def __init__(
        self,
        ip_block_id: str,
        controlling_device_name: str,
        bitstream_path: str,
        bitstream_id: str,
        bitstream_version: str,
        firmware_ip_block_id: str,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        emulator_ip_block_id: str | None = None,
        emulator_id: str | None = None,
        emulator_base_url: str | None = None,
        logging_level: str = "INFO",
    ):
        super().__init__(
            ip_block_id,
            controlling_device_name,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            VCCStreamMergeSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logging_level,
        )

    def configure(self, config: VCCStreamMergeConfigureArgin) -> int:
        """Configure the VCC Stream Merge."""
        result = 0
        for lane_config in config.fs_lane_configs:
            result = super().configure(lane_config.to_dict())
            if result == 1:
                break
        return result

    def deconfigure(self, config: VCCStreamMergeConfigureArgin | None) -> int:
        """Deconfigure the VCC Stream Merge."""
        if config is None:
            return super().recover()
        result = 0
        for lane_config in config.fs_lane_configs:
            result = super().deconfigure(lane_config.to_dict())
            if result == 1:
                break
        return result
