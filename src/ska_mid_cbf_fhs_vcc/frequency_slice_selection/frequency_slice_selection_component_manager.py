from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode

from ska_mid_cbf_fhs_vcc.api.emulator.frequency_slice_selection_emulator_api import FrequencySliceSelectionEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.frequency_slice_selection_simulator import FrequencySliceSelectionSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager


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


class FrequencySliceSelectionComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: FrequencySliceSelectionComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=FrequencySliceSelectionSimulator,
            emulator_api=FrequencySliceSelectionEmulatorApi,
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
                fssJsonConfig = FrequencySliceSelectionConfig(output=config.get("output"), input=config.get("input"))

                self.logger.info(f"FSS JSON CONFIG: {fssJsonConfig.to_json()}")

                result = super().configure(fssJsonConfig.to_dict())

                if result[0] != ResultCode.OK:
                    self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")
                    break

        except ValidationError as vex:
            errorMsg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{errorMsg}: {vex}")
            result = ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{errorMsg}: {ex!r}")
            result = ResultCode.FAILED, errorMsg

        return result

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: FrequencySliceSelectionComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()