from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode

from ska_mid_cbf_fhs_vcc.api.emulator.wib_emulator_api import WibEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.wideband_input_buffer_simulator import WidebandInputBufferSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager


@dataclass_json
@dataclass
class WideBandInputBufferConfig:
    expected_sample_rate: np.uint64
    noide_diode_transition_holdoff_seconds: float


##
# status class that will be populated by the APIs and returned to provide the status of Mac
##
@dataclass_json
@dataclass
class WideBandInputBufferStatus:
    buffer_underflowed: bool
    buffer_overflowed: bool
    loss_of_signal: np.uint32
    band_id: np.uint8


@dataclass_json
@dataclass
class WibArginConfig:
    expected_sample_rate: np.uint64
    noise_diode_transition_holdoff_seconds: float


class WidebandInputBufferComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: WidebandInputBufferComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=WidebandInputBufferSimulator,
            emulator_api=WibEmulatorApi,
            firmware_api=None,
            **kwargs,
        )

    ##
    # Public Commands
    ##
    def configure(self: FhsLowLevelComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WIB Configuring..")

            configJson: WibArginConfig = WibArginConfig.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {configJson.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            wibJsonConfig = WideBandInputBufferConfig(
                expected_sample_rate=configJson.expected_sample_rate,
                noide_diode_transition_holdoff_seconds=configJson.noise_diode_transition_holdoff_seconds,
            )

            self.logger.info(f"WIB JSON CONFIG: {wibJsonConfig.to_json()}")

            result = super().configure(wibJsonConfig.to_dict())

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

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandInputBufferComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
