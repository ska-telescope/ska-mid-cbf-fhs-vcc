from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.circuit_switch.circuit_switch_simulator import (
    CircuitSwitchSimulator,
)


@dataclass_json
@dataclass
class CircuitSwitchConfig:
    output: int
    input: int


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class CircuitSwitchStatus:
    num_inputs: int
    num_outputs: int
    connected: list[int]


@dataclass_json
@dataclass
class CircuitSwitchConfigureArgin:
    band: list[dict]


class CircuitSwitchComponentManager(FhsLowLevelComponentManagerBase):
    def __init__(
        self: CircuitSwitchComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=CircuitSwitchSimulator,
            **kwargs,
        )

    ##
    # Public Commands
    ##
    def configure(
        self: FhsLowLevelComponentManagerBase, argin: str
    ) -> tuple[ResultCode, str]:
        try:
            self.logger.info("Circuit Switch Configuring..")

            argin_parsed: CircuitSwitchConfigureArgin = (
                CircuitSwitchConfigureArgin.schema().loads(argin)
            )

            self.logger.info(f"CONFIG JSON CONFIG: {argin_parsed.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            for band in argin_parsed.band:
                cs_config = CircuitSwitchConfig(
                    output=band.get("output"), input=band.get("input")
                )

                self.logger.info(
                    f"Circuit Switch JSON CONFIG: {cs_config.to_json()}"
                )

                result = super().configure(cs_config.to_dict())

                if result[0] != ResultCode.OK:
                    self.logger.error(
                        f"Configuring {self._device_id} failed. {result[1]}"
                    )
                    break

        except ValidationError as vex:
            error_msg = (
                "Validation error: argin doesn't match the required schema"
            )
            self.logger.error(f"{error_msg}: {vex}")
            result = ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            result = ResultCode.FAILED, error_msg

        return result

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: CircuitSwitchComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
