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
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=WidebandFrequencyShifterSimulator,
            emulator_api=None,
            firmware_api=None,
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
