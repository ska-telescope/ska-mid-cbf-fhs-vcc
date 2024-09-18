from __future__ import annotations  # allow forward references in type hints

import logging
from dataclasses import dataclass
from typing import Any, Callable

from ska_control_model import CommunicationStatus, HealthState, SimulationMode

from ska_mid_cbf_fhs_vcc.api.simulator.wideband_frequency_shifter import WidebandFrequencyShifterSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager


@dataclass
class WidebandFrequencyShifterConfig:
    shift_frequency: float


##
# status class that will be populated by the APIs and returned to provide the status of Wideband frequency shifter
##
@dataclass
class WidebandFrequencyShifterStatus:
    shift_frequency: float


class WidebandFrequencyShifterComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: WidebandFrequencyShifterComponentManager,
        *args: Any,
        logger: logging.Logger,
        device_id=None,
        attr_change_callback: Callable[[str, Any], None] | None = None,
        attr_archive_callback: Callable[[str, Any], None] | None = None,
        health_state_callback: Callable[[HealthState], None] | None = None,
        obs_command_running_callback: Callable[[str, bool], None],
        max_queue_size: int = 32,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        **kwargs: Any,
    ) -> None:
        if simulation_mode == SimulationMode.TRUE:
            self._api = WidebandFrequencyShifterSimulator(device_id, logger)
        elif simulation_mode == SimulationMode.FALSE and emulation_mode is True:
            raise NotImplementedError("Emulator Api not implemented")
        else:
            raise NotImplementedError("FW Api not implemented")

        self.config_class = WidebandFrequencyShifterConfig(0)
        self.status_class = WidebandFrequencyShifterStatus(0)

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

    ##
    # Public Commands
    ##

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandFrequencyShifterComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
