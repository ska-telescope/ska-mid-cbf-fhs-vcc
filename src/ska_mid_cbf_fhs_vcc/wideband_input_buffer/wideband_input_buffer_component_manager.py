from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any, Callable, Tuple

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, HealthState, ResultCode, TaskStatus
from ska_mid_cbf_fhs_common import (
    FhsHealthMonitor,
    FhsLowLevelBaseDevice,
    FhsLowLevelComponentManagerBase,
    convert_dish_id_uint16_t_to_mnemonic,
)

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_simulator import WidebandInputBufferSimulator


@dataclass_json
@dataclass
class WidebandInputBufferConfig:
    expected_sample_rate: np.uint64
    noise_diode_transition_holdoff_seconds: float
    expected_dish_band: np.uint8


##
# status class that will be populated by the APIs and returned to provide the status of the Wideband Input Buffer
##
@dataclass_json
@dataclass
class WidebandInputBufferStatus:
    buffer_underflowed: bool
    buffer_overflowed: bool
    loss_of_signal: np.uint32
    error: bool
    loss_of_signal_seconds: np.uint32
    meta_band_id: np.uint8
    meta_dish_id: np.uint16
    rx_sample_rate: np.uint32
    meta_transport_sample_rate: np.uint32


class WidebandInputBufferComponentManager(FhsLowLevelComponentManagerBase):
    def __init__(
        self: WidebandInputBufferComponentManager,
        *args: Any,
        device: FhsLowLevelBaseDevice,
        health_state_callback: Callable[[HealthState], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            device=device,
            simulator_api=WidebandInputBufferSimulator,
            **kwargs,
        )

        self.expected_sample_rate = None
        self.expected_dish_id = None

        self.fhs_health_monitor = FhsHealthMonitor(
            logger=self.logger,
            get_device_health_state=self.get_device_health_state,
            update_health_state_callback=health_state_callback,
            check_registers_callback=self.check_registers,
            api=self._api,
            poll_interval=device.health_monitor_poll_interval,
        )

    ##
    # Public Commands
    ##
    def configure(self: FhsLowLevelComponentManagerBase, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WIB Configuring..")

            wib_config: WidebandInputBufferConfig = WidebandInputBufferConfig.schema().loads(argin)

            self.logger.info(f"WIB JSON CONFIG: {wib_config.to_json()}")

            self.expected_sample_rate = wib_config.expected_sample_rate

            result = super().configure(wib_config.to_dict())

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

    # add self.logger warnings to check for variables to see whats being missed
    # check check_register function been called, log whole status object at start, log dictionary right before return at end, check that they look correct (don't need to match, but bufferunder should associate with healthstate and output as expected)

    def check_registers(self: WidebandInputBufferComponentManager, status_dict: dict) -> dict[str, HealthState]:
        status: WidebandInputBufferStatus = WidebandInputBufferStatus.schema().load(status_dict)

        self.logger.warning(f"Status object log: {status}")

        register_statuses = {}
        self.logger.warning(f"Status = {status}")

        register_statuses["meta_dish_id"] = self.check_meta_dish_id(status.meta_dish_id)
        self.logger.warning(f"reg status meta_dish_id = {register_statuses}")

        register_statuses["rx_sample_rate"] = self.check_register(
            self.expected_sample_rate,
            status.rx_sample_rate,
            error_msg=f"rx_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.rx_sample_rate}",
        )
        self.logger.warning(f"reg status rx_sample_rate = {register_statuses}")
        self.logger.warning(f"Actual rx_sample_rate: {status.rx_sample_rate}, Expected: {self.expected_sample_rate}")

        register_statuses["meta_transport_sample_rate"] = self.check_register(
            self.expected_sample_rate,
            status.meta_transport_sample_rate,
            error_msg=f"meta_transport_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.meta_transport_sample_rate}",
        )
        self.logger.warning(f"reg status meta_transport_sample_rate = {register_statuses}")
        self.logger.warning(
            f"Actual meta_transport_sample_rate: {status.meta_transport_sample_rate}, Expected: {self.expected_sample_rate}"
        )

        if status.error:
            register_statuses["error"] = HealthState.DEGRADED
            self.logger.warning(f"error mismatch. Expected False, Actual {status.error}")
            # logger line here to indicate if it did if
            self.logger.warning(f" Healthstate Degraded if executed")
        else:
            register_statuses["error"] = HealthState.OK
            # logger line here to indicate if it did else
            self.logger.warning(f"Healthstate Okay else executed")

        register_statuses["buffer_underflowed"] = self.check_register(
            False,
            status.buffer_underflowed,
            error_msg=f"buffer_underflowed mismatch. Expected False, Actual: {status.buffer_underflowed}",
        )
        self.logger.warning(f"reg status buffer_underflowed = {register_statuses}")
        self.logger.warning(f"Actual buffer_underflowed: {status.buffer_underflowed}, Expected False")

        register_statuses["buffer_overflowed"] = self.check_register(
            False,
            status.buffer_overflowed,
            error_msg=f"buffer_overflowed mismatch. Expected False, Actual: {status.buffer_overflowed}",
        )
        self.logger.warning(f"reg status buffer_overflowed = {register_statuses}")
        self.logger.warning(f"Actual buffer_overflowed: {status.buffer_overflowed}, Expected False")

        self.logger.warning(f"Dictionary log: {dict}")

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
