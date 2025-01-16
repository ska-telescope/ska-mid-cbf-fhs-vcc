from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.api.simulator.circuit_switch_simulator import CircuitSwitchSimulator


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
class CircuitSwitchConfigArgin:
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
    def configure(self: FhsLowLevelComponentManagerBase, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("Circuit Switch Configuring..")

            configJson: CircuitSwitchConfigArgin = CircuitSwitchConfigArgin.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {configJson.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            for band in configJson.band:
                csJsonConfig = CircuitSwitchConfig(output=band.get("output"), input=band.get("input"))

                self.logger.info(f"Circuit Switch JSON CONFIG: {csJsonConfig.to_json()}")

                result = super().configure(csJsonConfig.to_dict())

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
    def start_communicating(self: CircuitSwitchComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
