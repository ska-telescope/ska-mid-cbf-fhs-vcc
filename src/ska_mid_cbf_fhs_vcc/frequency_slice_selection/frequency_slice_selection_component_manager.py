from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass, field
from typing import Any

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_simulator import FrequencySliceSelectionSimulator


@dataclass_json
@dataclass
class FrequencySliceSelectionConfig:
    band_select: int = 1
    band_start_channel: list[int] = field(default_factory=lambda: [0, 1, 2])


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class FrequencySliceSelectionStatus:
    band_select: int
    band_start_channel: list[int]


class FrequencySliceSelectionComponentManager(FhsLowLevelComponentManagerBase):
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

            fss_config: FrequencySliceSelectionConfig = FrequencySliceSelectionConfig.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {fss_config.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            result = super().configure(fss_config.to_dict())

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

    def deconfigure(self: FrequencySliceSelectionComponentManager, argin: str = None) -> tuple[ResultCode, str]:
        try:
            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} deconfigured successfully",
            )

            if argin is None:
                result = super().recover()
            else:
                fss_config: FrequencySliceSelectionConfig = FrequencySliceSelectionConfig.schema().loads(argin)

                self.logger.info(f"DECONFIG JSON CONFIG: {fss_config.to_json()}")

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
    def start_communicating(self: FrequencySliceSelectionComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
