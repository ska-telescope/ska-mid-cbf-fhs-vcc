from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any, Tuple

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode, TaskStatus

from ska_mid_cbf_fhs_vcc.api.emulator.wib_emulator_api import WibEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.wideband_input_buffer_simulator import WidebandInputBufferSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager
from ska_mid_cbf_fhs_vcc.common.utils import PollingService


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
    meta_transport_sample_rate: np.uint32


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
        poll_interval_s: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=WidebandInputBufferSimulator,
            emulator_api=WibEmulatorApi,
            **kwargs,
        )
        self.polling_service = PollingService(interval=poll_interval_s, callback=self._poll_status)

        self.expected_sample_rate = None
        self.expected_dish_id = None

    ##
    # Public Commands
    ##
    def configure(self: FhsLowLevelComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WIB Configuring..")

            wibJsonConfig: WibArginConfig = WibArginConfig.schema().loads(argin)

            self.logger.info(f"WIB JSON CONFIG: {wibJsonConfig.to_json()}")

            self.expected_sample_rate = wibJsonConfig.expected_sample_rate

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

    def start(self: WidebandInputBufferComponentManager, *args, **kwargs) -> Tuple[TaskStatus, str]:
        self.polling_service.start()
        return super().start(*args, **kwargs)

    def stop(self: WidebandInputBufferComponentManager, *args, **kwargs) -> Tuple[TaskStatus, str]:
        self.polling_service.stop()
        return super().stop(*args, **kwargs)

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandInputBufferComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()

    def _poll_status(self: WidebandInputBufferComponentManager):
        if self._simulation_mode:
            return

        self.logger.debug("Polling status...")
        result = super().status()

        if result[0] != ResultCode.OK:
            self.logger.error(f"Getting status failed. {result}")
            return
        else:
            status: WideBandInputBufferStatus = WideBandInputBufferStatus.schema().loads(result[1], unknown="exclude")

        if self.expected_dish_id is not None:
            meta_dish_id_mnemonic = convert_dish_id_uint16_t_to_mnemonic(status.meta_dish_id)
            if meta_dish_id_mnemonic != self.expected_dish_id:
                self.logger.error(
                    f"meta_dish_id mismatch. Expected: {self.expected_dish_id}, Actual: {meta_dish_id_mnemonic} ({status.meta_dish_id})"
                )
            else:
                self.logger.debug(f"dish_id matched {status.meta_dish_id}")

        if self.expected_sample_rate is not None:
            if status.meta_transport_sample_rate != self.expected_sample_rate:
                self.logger.error(
                    f"meta_transport_sample_rate mismatch. Expected: {self.expected_sample_rate}, Actual: {status.meta_transport_sample_rate}"
                )
            elif status.rx_sample_rate != self.expected_sample_rate:
                self.logger.error(
                    f"rx_sample_rate mismatch. Expected: {self.expected_sample_rate}, Actual: {status.rx_sample_rate}"
                )
            else:
                self.logger.debug(f"sample rate matched {status.meta_dish_id}")


def convert_dish_id_uint16_t_to_mnemonic(numerical_dish_id: int) -> str:
    SKA_DISH_INSTANCE_MIN = 1
    SKA_DISH_INSTANCE_MAX = 133
    MKT_DISH_INSTANCE_MAX = 63
    DISH_INSTANCE_NUM_BITS = 12

    MKT_DISH_TYPE_NUM = 0
    SKA_DISH_TYPE_NUM = 1
    MKT_DISH_TYPE_STR = "MKT"
    SKA_DISH_TYPE_STR = "SKA"

    DISH_TYPE_STR_LEN = 3

    if numerical_dish_id == 0xFFFF:
        return "DIDINV"

    # Check the dish type mnemonic
    dish_type_uint = (numerical_dish_id & 0xF000) >> DISH_INSTANCE_NUM_BITS

    if dish_type_uint not in (SKA_DISH_TYPE_NUM, MKT_DISH_TYPE_NUM):
        raise ValueError(f"Incorrect DISH type {dish_type_uint}. First four bits must be 0000 (MKT) or 0001 (SKA)")

    # Convert to DISH TYPE mnemonic
    dish_type_str = SKA_DISH_TYPE_STR if dish_type_uint == SKA_DISH_TYPE_NUM else MKT_DISH_TYPE_STR

    dish_instance_uint = numerical_dish_id & 0x0FFF

    # Extract number from last 12 bits and validate
    if dish_type_str == SKA_DISH_TYPE_STR and (
        dish_instance_uint < SKA_DISH_INSTANCE_MIN or dish_instance_uint > SKA_DISH_INSTANCE_MAX
    ):
        raise ValueError(
            f"Incorrect DISH instance {dish_instance_uint}. Dish instance for SKA DISH type is {SKA_DISH_INSTANCE_MIN} to {SKA_DISH_INSTANCE_MAX} incl."
        )
    if dish_type_str == MKT_DISH_TYPE_STR and dish_instance_uint > MKT_DISH_INSTANCE_MAX:
        raise ValueError(
            f"Incorrect DISH instance {dish_instance_uint}. Dish instance for MKT DISH type is 0 to {MKT_DISH_INSTANCE_MAX} incl."
        )

    dish_instance_str = str(dish_instance_uint)
    padding_length = DISH_TYPE_STR_LEN - min(DISH_TYPE_STR_LEN, len(dish_instance_str))

    return dish_type_str + "0" * padding_length + dish_instance_str
