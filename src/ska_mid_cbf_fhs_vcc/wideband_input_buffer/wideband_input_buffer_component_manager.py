from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any, Callable, Tuple

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, HealthState, ResultCode, TaskStatus

from ska_mid_cbf_fhs_vcc.api.emulator.wib_emulator_api import WibEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.wideband_input_buffer_simulator import WidebandInputBufferSimulator
from ska_mid_cbf_fhs_vcc.common.fhs_health_monitor import FhsHealthMonitor
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
        health_state_callback: Callable[[HealthState], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=WidebandInputBufferSimulator,
            emulator_api=WibEmulatorApi,
            **kwargs,
        )

        self.registers_to_check = {"meta_dish_id", "rx_sample_rate", "meta_transport_sample_rate"}

        self.expected_sample_rate = None
        self.expected_dish_id = None

        self.fhs_health_monitor = FhsHealthMonitor(
            logger=self.logger,
            get_device_health_state=self.get_device_health_state, 
            update_health_state_callback=health_state_callback, 
            check_registers_callback=self.check_registers, 
            api=self._api, 
            poll_interval=poll_interval_s
        )

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
        self.fhs_health_monitor.start_polling()
        return super().start(*args, **kwargs)

    def stop(self: WidebandInputBufferComponentManager, *args, **kwargs) -> Tuple[TaskStatus, str]:
        self.fhs_health_monitor.stop_polling()
        return super().stop(*args, **kwargs)

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandInputBufferComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()

    def check_registers(self: WidebandInputBufferComponentManager, status_str: str) -> dict[str, HealthState]:
        status: WideBandInputBufferStatus = WideBandInputBufferStatus.schema().loads(status_str)

        register_statuses = {key: HealthState.UNKNOWN for key in self.registers_to_check}

        for register in self.registers_to_check:
            if register == "meta_dish_id":
                register_statuses["meta_dish_id"] = self.check_meta_dish_id(status.meta_dish_id)

            if register == "rx_sample_rate":
                register_statuses["rx_sample_rate"] = self.check_register(
                    self.expected_sample_rate,
                    status.rx_sample_rate,
                    error_msg=f"rx_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.rx_sample_rate}",
                )

            if register == "meta_transport_sample_rate":
                register_statuses["meta_transport_sample_rate"] = self.check_register(
                    self.expected_sample_rate,
                    status.meta_transport_sample_rate,
                    error_msg=f"meta_transport_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.meta_transport_sample_rate}",
                )

        return register_statuses

    def check_meta_dish_id(self: WidebandInputBufferComponentManager, meta_dish_id: int) -> HealthState:
        result = HealthState.OK

        if meta_dish_id:
            meta_dish_id_mnemonic = convert_dish_id_uint16_t_to_mnemonic(meta_dish_id)

            result = self.check_register(
                self.expected_dish_id,
                meta_dish_id_mnemonic,
                error_msg=f"meta_dish_id mismatch. Expected: {self.expected_dish_id}, Actual: {meta_dish_id_mnemonic} ({meta_dish_id})",
            )
        else:
            self.logger.error("Unable to convert meta_dish_id.  Meta_dish_id is none")
            result = HealthState.FAILED

        return result

    def check_register(
        self: WidebandInputBufferComponentManager,
        expected_value: Any,
        register_value: Any,
        success_msg: str = None,
        error_msg: str = None,
    ) -> HealthState:
        result = HealthState.OK

        if expected_value:
            result = self.check_register_expected_value(expected_value, register_value)

            if result != HealthState.OK:
                if error_msg:
                    self.logger.error(error_msg)
            else:
                if success_msg:
                    self.logger.info(success_msg)

        return result

    def check_register_expected_value(self, expected_value: Any, register_value: Any) -> HealthState:
        result = HealthState.FAILED

        if expected_value and register_value:
            if expected_value == register_value:
                result = HealthState.OK
        else:
            self.logger.error(
                f"Function expects an expected_value and register_value. Was given expected_value={expected_value}, register_value={register_value}"
            )
            result = HealthState.FAILED

        return result


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
        raise ValueError("Incorrect DISH type. First four bits must be 0000 (MKT) or 0001 (SKA)")

    # Convert to DISH TYPE mnemonic
    dish_type_str = SKA_DISH_TYPE_STR if dish_type_uint == SKA_DISH_TYPE_NUM else MKT_DISH_TYPE_STR

    dish_instance_uint = numerical_dish_id & 0x0FFF

    # Extract number from last 12 bits and validate
    if dish_type_str == SKA_DISH_TYPE_STR and (
        dish_instance_uint < SKA_DISH_INSTANCE_MIN or dish_instance_uint > SKA_DISH_INSTANCE_MAX
    ):
        raise ValueError(
            f"Incorrect DISH instance. Dish instance for SKA DISH type is {SKA_DISH_INSTANCE_MIN} to {SKA_DISH_INSTANCE_MAX} incl."
        )
    if dish_type_str == MKT_DISH_TYPE_STR and dish_instance_uint > MKT_DISH_INSTANCE_MAX:
        raise ValueError(f"Incorrect DISH instance. Dish instance for MKT DISH type is 0 to {MKT_DISH_INSTANCE_MAX} incl.")

    dish_instance_str = str(dish_instance_uint)
    padding_length = DISH_TYPE_STR_LEN - min(DISH_TYPE_STR_LEN, len(dish_instance_str))

    return dish_type_str + "0" * padding_length + dish_instance_str
