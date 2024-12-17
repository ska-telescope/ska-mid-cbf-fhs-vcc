from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass, field
from typing import Any

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.frequency_slice_selection_simulator import FrequencySliceSelectionSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager


@dataclass_json
@dataclass
class FrequencySliceSelectionConfig:
    band_select: int
    band_start_channel: list[int]


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class FrequencySliceSelectionStatus:
    band_select: int
    band_start_channel: list[int]


@dataclass_json
@dataclass
class FssConfigArgin:
    band_select: int = 1
    band_start_channel: list[int] = field(default_factory=lambda: [0, 1, 2])


class FrequencySliceSelectionComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: FrequencySliceSelectionComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=FrequencySliceSelectionSimulator,
            **kwargs,
        )

    def go_to_idle(self: FrequencySliceSelectionComponentManager) -> tuple[ResultCode, str]:
        result = self.deconfigure()

        if result[0] is not ResultCode.FAILED:
            result = super().go_to_idle()

        return result

    ##
    # Public Commands
    ##
    def configure(self: FrequencySliceSelectionComponentManager, argin: dict) -> tuple[ResultCode, str]:
        try:
            self.logger.info("FS Selection Configuring..")

            configJson: FssConfigArgin = FssConfigArgin.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {configJson.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            result = super().configure(configJson.to_dict())

            if result[0] != ResultCode.OK:
                self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")

        except ValidationError as vex:
            errorMsg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{errorMsg}: {vex}")
            result = ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{errorMsg}: {ex!r}")
            result = ResultCode.FAILED, errorMsg

        return result

    def deconfigure(self: FrequencySliceSelectionComponentManager, argin: dict = None) -> tuple[ResultCode, str]:
        try:
            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} deconfigured successfully",
            )

            if argin is None:
                result = super().recover()
            else:
                wfsJsonConfig: FssConfigArgin = FssConfigArgin.schema().loads(argin)

                self.logger.info(f"DECONFIG JSON CONFIG: {wfsJsonConfig.to_json()}")

                result = super().deconfigure(argin)

                if result[0] != ResultCode.OK:
                    self.logger.error(f"DeConfiguring {self._device_id} failed. {result[1]}")

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
    async def start_communicating(self: FrequencySliceSelectionComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
