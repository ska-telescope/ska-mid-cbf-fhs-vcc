from __future__ import annotations  # allow forward references in type hints

import logging
from dataclasses import dataclass
from typing import Any, Callable

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import (
    CommunicationStatus,
    HealthState,
    ResultCode,
    SimulationMode,
)

from ska_mid_cbf_fhs_vcc.api.frequency_slice_selection_wrapper import (
    FrequencySliceSelectionApi,
)
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import (
    FhsLowLevelComponentManager,
)


@dataclass_json
@dataclass
class FrequencySliceSelectionConfig:
    output: int
    input: int


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class FrequencySliceSelectionStatus:
    num_inputs: int
    num_outputs: int
    connected: list[int]


@dataclass_json
@dataclass
class FssConfigArgin:
    config: list[dict]


class FrequencySliceSelectionComponentManager(
    FhsLowLevelComponentManager[FrequencySliceSelectionConfig, FrequencySliceSelectionStatus]
):
    def __init__(
        self: FrequencySliceSelectionComponentManager,
        *args: Any,
        logger: logging.Logger,
        device_id=None,
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
        self._api = FrequencySliceSelectionApi(
            device_id=device_id,
            config_location=config_location,
            logger=logger,
            emulation_mode=emulation_mode,
            simulation_mode=simulation_mode,
        )

        self.status_class = FrequencySliceSelectionStatus(num_outputs=0, num_inputs=0, connected=[])
        self.config_class = FrequencySliceSelectionConfig(output=0, input=0)

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
    def configure(self: FhsLowLevelComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WIB Configuring..")

            configJson: FssConfigArgin = FssConfigArgin.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {configJson.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            for config in configJson.config:
                fssJsonConfig = FrequencySliceSelectionConfig(
                    output=config.get("output"), input=config.get("input")
                )

                self.logger.info(f"FSS JSON CONFIG: {fssJsonConfig.to_json()}")

                result = super().configure(fssJsonConfig.to_dict())

                if result[0] != ResultCode.OK:
                    self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")
                    break

        except ValidationError as vex:
            errorMsg = "Validation error: argin doesn't match the required schema."
            self.logger.error(errorMsg, repr(vex))
            result = ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to configure {self._device_id}"
            self.logger.error(errorMsg, repr(ex))
            result = ResultCode.FAILED, errorMsg

        return result

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: FrequencySliceSelectionComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
