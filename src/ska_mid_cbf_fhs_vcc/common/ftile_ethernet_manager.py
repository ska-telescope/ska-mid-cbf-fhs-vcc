from dataclasses import dataclass, field
from logging import Logger
from typing import Callable

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import HealthState, SimulationMode

from ska_mid_cbf_fhs_vcc.common.ftile_ethernet_simulator import FtileEthernetSimulator
from ska_mid_cbf_fhs_vcc.ip_block_manager.base_monitoring_ip_block_manager import BaseMonitoringIPBlockManager
from ska_mid_cbf_fhs_vcc.ip_block_manager.non_blocking_function import non_blocking


@dataclass_json
@dataclass
class FtileEthernetConfig:
    loopback: bool = False
    unidirectional: bool = False


@dataclass_json
@dataclass
class FtileEthernetCastStats:
    data_err: np.uint32 = 0
    ctrl_err: np.uint32 = 0
    data_ok: np.uint64 = 0
    ctrl_ok: np.uint64 = 0


@dataclass_json
@dataclass
class FtileEthernetMacStats:
    fragments: np.uint32 = 0
    jabbers: np.uint32 = 0
    fcs_err: np.uint32 = 0
    pause_err: np.uint32 = 0
    multicast: FtileEthernetCastStats = field(default_factory=lambda: FtileEthernetCastStats())
    broadcast: FtileEthernetCastStats = field(default_factory=lambda: FtileEthernetCastStats())
    unicast: FtileEthernetCastStats = field(default_factory=lambda: FtileEthernetCastStats())
    packet_count_64b: np.uint64 = 0
    packet_count_65to127b: np.uint64 = 0
    packet_count_128to255b: np.uint64 = 0
    packet_count_256to511b: np.uint64 = 0
    packet_count_512to1023b: np.uint64 = 0
    packet_count_1024to1518: np.uint64 = 0
    packet_count_1519tomaxb: np.uint64 = 0
    packet_count_oversize: np.uint32 = 0
    pause: np.uint64 = 0
    runt: np.uint32 = 0
    frame_start: np.uint64 = 0
    length_error: np.uint32 = 0
    pfc_error: np.uint32 = 0
    pfc: np.uint32 = 0
    malformed: np.uint32 = 0
    dropped: np.uint32 = 0
    bad_length_type: np.uint32 = 0
    payload_bytes: np.uint64 = 0
    total_bytes: np.uint64 = 0


@dataclass_json
@dataclass
class FtileEthernetFecStats:
    corrected_codewords: list[np.uint64] = field(default_factory=lambda: [])
    uncorrected_codewords: list[np.uint64] = field(default_factory=lambda: [])


##
# status class that will be populated by the APIs and returned to provide the status of F-tile Ethernet
##
@dataclass_json
@dataclass
class FtileEthernetStatus:
    rx_mac: FtileEthernetMacStats = field(default_factory=lambda: FtileEthernetMacStats())
    tx_mac: FtileEthernetMacStats = field(default_factory=lambda: FtileEthernetMacStats())
    rx_fec: FtileEthernetFecStats = field(default_factory=lambda: FtileEthernetFecStats())
    tx_pll_locked: np.uint8 = 0
    tx_lanes_stable: bool = False
    rx_cdr_locked: np.uint8 = 0
    rx_deskew: bool = False
    rx_deskew_change: bool = False
    rx_pcs_ready: bool = False
    tx_ready: bool = False
    rx_ready: bool = False
    ready: bool = False


class FtileEthernetManager(BaseMonitoringIPBlockManager):
    """Mock Ftile Ethernet IP block manager."""

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
        health_monitor_poll_interval: float = 30.0,
        update_health_state_callback: Callable = lambda _: None,
    ):
        self.status_value_memo = {
            "rx_ready": False,
            "tx_ready": False,
        }

        super().__init__(
            ip_block_id,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            FtileEthernetSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logger,
            health_monitor_poll_interval,
            update_health_state_callback,
        )

    @non_blocking
    def start(self) -> int:
        return super().start()

    @non_blocking
    def stop(self) -> int:
        return super().stop()

    def get_status_healthstates(self, status_dict: dict) -> dict[str, HealthState]:
        eth_status: FtileEthernetStatus = FtileEthernetStatus.schema().load(status_dict)

        self.logger.info(f"Determining HealthStates for received F-tile Ethernet status: {eth_status.to_json()}")

        status_value_healthstates = {}

        for readiness_attr_key in ["rx_ready", "tx_ready"]:
            readiness_attr = bool(getattr(eth_status, readiness_attr_key))
            if readiness_attr is True:
                status_value_healthstates[readiness_attr_key] = HealthState.OK
            else:
                if self.status_value_memo.get(readiness_attr_key) is True:
                    status_value_healthstates[readiness_attr_key] = HealthState.FAILED
                elif readiness_attr_key not in self.health_monitor.component_statuses:
                    status_value_healthstates[readiness_attr_key] = HealthState.OK
            self.status_value_memo[readiness_attr_key] = readiness_attr

        for mac_stats_attr_key in ["rx_mac", "tx_mac"]:
            mac_stats_attr: FtileEthernetMacStats = getattr(eth_status, mac_stats_attr_key)
            for cast_stats_attr_key in ["multicast", "broadcast", "unicast"]:
                cast_stats_attr: FtileEthernetCastStats = getattr(mac_stats_attr, cast_stats_attr_key)
                status_value_healthstates["_".join([mac_stats_attr_key, cast_stats_attr_key, "data_err"])] = (
                    HealthState.FAILED if cast_stats_attr.data_err > 1 else HealthState.OK
                )

        self.logger.info(f"Determined HealthStates for F-tile Ethernet: {status_value_healthstates}")

        return status_value_healthstates
