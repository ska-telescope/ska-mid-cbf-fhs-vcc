from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.wideband_frequency_shifter import WidebandFrequencyShifterSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager


@dataclass_json
@dataclass
class WidebandFrequencyShifterConfig:
    shift_frequency: float = 0.0


##
# status class that will be populated by the APIs and returned to provide the status of Wideband frequency shifter
##
@dataclass_json
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
            **kwargs,
        )

    ##
    # Public Commands
    ##
    def go_to_idle(self: WidebandFrequencyShifterComponentManager) -> tuple[ResultCode, str]:
        result = self.deconfigure()

        if result[0] is not ResultCode.FAILED:
            result = super().go_to_idle()
        else:
            self.logger.error("Unable to go to idle, result from deconfiguring was FAILED")

        return result

    def configure(self: WidebandFrequencyShifterComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WFS Configuring..")

            wfsJsonConfig: WidebandFrequencyShifterConfig = WidebandFrequencyShifterConfig.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {wfsJsonConfig.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            self.logger.info(f"WFS JSON CONFIG: {wfsJsonConfig.to_json()}")

            result = super().configure(wfsJsonConfig.to_dict())

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

    def deconfigure(self: WidebandFrequencyShifterComponentManager, argin: dict = None) -> tuple[ResultCode, str]:
        try:
            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} deconfigured successfully",
            )

            if argin is None:
                result = super().recover()
            else:
                wfsJsonConfig: WidebandFrequencyShifterConfig = WidebandFrequencyShifterConfig.schema().loads(argin)

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
    def start_communicating(self: WidebandFrequencyShifterComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
