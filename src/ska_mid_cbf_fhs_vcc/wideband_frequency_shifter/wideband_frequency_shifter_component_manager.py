from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_simulator import WidebandFrequencyShifterSimulator


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


class WidebandFrequencyShifterComponentManager(FhsLowLevelComponentManagerBase):
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

    def configure(self: WidebandFrequencyShifterComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WFS Configuring..")

            wfs_config: WidebandFrequencyShifterConfig = WidebandFrequencyShifterConfig.schema().loads(argin)

            self.logger.info(f"WFS JSON CONFIG: {wfs_config.to_json()}")

            result = super().configure(wfs_config.to_dict())

            if result[0] != ResultCode.OK:
                self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")

        except ValidationError as vex:
            error_msg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            result = ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            result = ResultCode.FAILED, error_msg

        return result

    def deconfigure(self: WidebandFrequencyShifterComponentManager, argin: str = None) -> tuple[ResultCode, str]:
        self.logger.error(f"############################# Deconfigure called")
        try:
            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} deconfigured successfully",
            )

            if argin is None:
                result = super().recover()
            else:
                wfs_config: WidebandFrequencyShifterConfig = WidebandFrequencyShifterConfig.schema().loads(argin)

                self.logger.info(f"DECONFIG JSON CONFIG: {wfs_config.to_json()}")

                result = super().deconfigure(argin)

                if result[0] != ResultCode.OK:
                    self.logger.error(f"DeConfiguring {self._device_id} failed. {result[1]}")

        except ValidationError as vex:
            error_msg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            result = ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            result = ResultCode.FAILED, error_msg

        return result

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandFrequencyShifterComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
