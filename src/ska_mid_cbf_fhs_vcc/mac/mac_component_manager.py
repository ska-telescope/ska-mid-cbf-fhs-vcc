from __future__ import annotations  # allow forward references in type hints

import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from ska_control_model import CommunicationStatus, HealthState, SimulationMode

from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import (
    FhsLowLevelComponentManager,
)
from ska_mid_cbf_fhs_vcc.api.emulator.mac_emulator_api import MacEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.mac_controller_simulator import (
    MacBaseControllerSimulator,
)


@dataclass
class MacConfig:
    rx_loopback_enable: bool = False


##
# status class that will be populated by the APIs and returned to provide the status of Mac
##
@dataclass
class MacStatus:
    class phy:
        rx_loopback: bool = False
        rx_freq_lock = []
        rx_word_lock = []

    class fec:
        rx_corrected_code_words: np.uint32 = 0
        rx_uncorrected_code_words: np.uint32 = 0

    class mac:
        rx_fragments: np.uint32 = 0
        rx_runt: np.uint32 = 0
        rx_64_bytes: np.uint32 = 0
        rx_65_to_127_bytes: np.uint32 = 0
        rx_128_to_255_bytes: np.uint32 = 0
        rx_256_to_511_bytes: np.uint32 = 0
        rx_512_to_1023_bytes: np.uint32 = 0
        rx_1024_to_1518_bytes: np.uint32 = 0
        rx_1519_to_max_bytes: np.uint32 = 0
        rx_oversize: np.uint32 = 0
        rx_frame_octets_ok: np.uint32 = 0
        rx_crcerr: np.uint32 = 0
        tx_fragments: np.uint32 = 0
        tx_runt: np.uint32 = 0
        tx_64_bytes: np.uint32 = 0
        tx_65_to_127_bytes: np.uint32 = 0
        tx_128_to_255_bytes: np.uint32 = 0
        tx_256_to_511_bytes: np.uint32 = 0
        tx_512_to_1023_bytes: np.uint32 = 0
        tx_1024_to_1518_bytes: np.uint32 = 0
        tx_1519_to_max_bytes: np.uint32 = 0
        tx_oversize: np.uint32 = 0
        tx_frame_octets_ok: np.uint32 = 0
        tx_crcerr: np.uint32 = 0


class MacComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: MacComponentManager,
        *args: Any,
        logger: logging.Logger,
        device_id,
        config_location,
        attr_change_callback: Callable[[str, Any], None] | None = None,
        attr_archive_callback: Callable[[str, Any], None] | None = None,
        health_state_callback: Callable[[HealthState], None] | None = None,
        obs_command_running_callback: Callable[[str, bool], None],
        max_queue_size: int = 32,
        simulation_mode: SimulationMode = SimulationMode.FALSE,
        emulation_mode: bool = True,
        **kwargs: Any,
    ) -> None:
        if simulation_mode == SimulationMode.TRUE:
            self._api = MacBaseControllerSimulator(device_id, logger)
        elif simulation_mode == SimulationMode.FALSE and emulation_mode is True:
            self._api = MacEmulatorApi(device_id, config_location, logger)
        else:
            raise NotImplementedError("FW Api not implemented")

        self.config_class = MacConfig()
        self.status_class = MacStatus()

        super().__init__(
            *args,
            logger=logger,
            device_id=device_id,
            api=self._api,
            status_class=self.status_class,
            config_class=self.config_class,
            attr_change_callback=attr_change_callback,
            attr_archive_callback=attr_archive_callback,
            health_state_callback=health_state_callback,
            obs_command_running_callback=obs_command_running_callback,
            max_queue_size=max_queue_size,
            simulation_mode=simulation_mode,
            emulation_mode=emulation_mode,
            **kwargs,
        )

    # --------------------
    # Public Commands
    # --------------------

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: MacComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
