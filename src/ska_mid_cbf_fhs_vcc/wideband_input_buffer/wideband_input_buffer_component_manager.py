from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any
import threading
from time import sleep

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
    noise_diode_transition_holdoff_seconds: float
    expected_dish_band: np.uint8


##
# status class that will be populated by the APIs and returned to provide the status of Mac
##
@dataclass_json
@dataclass
class WideBandInputBufferStatus:
    buffer_underflowed: bool
    buffer_overflowed: bool
    loss_of_signal: np.uint32
    error: bool
    loss_of_signal_seconds: np.uint32
    meta_band_id: np.uint8
    meta_dish_id: np.uint16
    rx_sample_rate: np.uint32
    meta_transport_sample_rate_lsw: np.uint32
    meta_transport_sample_rate_msw: np.uint16


@dataclass_json
@dataclass
class WibArginConfig:
    expected_sample_rate: np.uint64
    noise_diode_transition_holdoff_seconds: float
    expected_dish_band: np.uint8


class WidebandInputBufferComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: WidebandInputBufferComponentManager,
        *args: Any,
        dish_id_poll_interval_s: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=WidebandInputBufferSimulator,
            emulator_api=WibEmulatorApi,
            **kwargs,
        )
        self.dish_id_poll_interval_s = dish_id_poll_interval_s

        self.expected_dish_id = None
        self.should_poll_dish_id = False
        self.dish_id_thread = threading.Thread(target=self.poll_dish_id, daemon=True)
        self.dish_id_thread.start()

    ##
    # Public Commands
    ##
    def configure(self: FhsLowLevelComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WIB Configuring..")

            wibJsonConfig: WibArginConfig = WibArginConfig.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {wibJsonConfig.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
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

    def start(self: WidebandInputBufferComponentManager, *args, **kwargs) -> None:
        super().start(*args, **kwargs)
        self.should_poll_dish_id = True

    def stop(self: WidebandInputBufferComponentManager, *args, **kwargs) -> None:
        super().stop(*args, **kwargs)
        self.should_poll_dish_id = False

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandInputBufferComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()

    def poll_dish_id(self):
        while True:
            if self.should_poll_dish_id and self.expected_dish_id is not None:
                self.logger.debug(f"Polling dish id, expecting: {self.expected_dish_id}")

                result = super().status()
                if result[0] != ResultCode.OK:
                    self.logger.error(f"Getting status failed. {result}")
                else:
                    status: WideBandInputBufferStatus = WideBandInputBufferStatus.schema().loads(result[1], unknown="exclude")

                    if status.meta_dish_id != self.expected_dish_id:
                        self.logger.error(f"Dish id mismatch. Expected: {self.expected_dish_id}, Actual: {status.meta_dish_id}")
                    else:
                        self.logger.debug(f"Dish id matched {status.meta_dish_id}")

            sleep(self.dish_id_poll_interval_s)
