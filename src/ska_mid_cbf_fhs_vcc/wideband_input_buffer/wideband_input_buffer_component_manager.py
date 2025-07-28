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
    buffer_overflow: bool
    loss_of_signal: np.uint32
    error: bool
    packet_error: bool
    packet_error_count: np.uint32
    packet_drop: bool
    packet_drop_count: np.uint32
    loss_of_signal_seconds: np.uint32
    meta_band_id: np.uint8
    meta_dish_id: np.uint16
    rx_sample_rate: np.uint32
    rx_packet_rate: np.uint32
    meta_transport_sample_rate: np.uint32
    link_failure: bool
    expected_sample_rate: np.uint32


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

    def check_registers(self: WidebandInputBufferComponentManager, status_dict: dict) -> dict[str, HealthState]:
        status: WidebandInputBufferStatus = WidebandInputBufferStatus.schema().load(status_dict)

        register_statuses = {}

        register_statuses["meta_dish_id"] = self.check_meta_dish_id(status.meta_dish_id)

        register_statuses["rx_sample_rate"] = self.check_register(
            self.expected_sample_rate,
            status.rx_sample_rate,
            error_msg=f"rx_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.rx_sample_rate}",
        )

        register_statuses["meta_transport_sample_rate"] = self.check_register(
            self.expected_sample_rate,
            status.meta_transport_sample_rate,
            error_msg=f"meta_transport_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.meta_transport_sample_rate}",
        )

        if status.error:
            if status.buffer_overflow is True or status.link_failure is True:
                register_statuses["error"] = HealthState.FAILED
            else:
                register_statuses[
                    "error"
                ] = (
                    HealthState.DEGRADED
                )  # if not overflow or underflow, goes to degraded because one of packet_drop and packet_error set
        else:
            register_statuses["error"] = HealthState.OK

        register_statuses["link_failure"] = self.check_register(
            False,
            status.link_failure,
            error_msg=f"link_failure mismatch. Expected False, Actual: {status.link_failure}",
        )

        register_statuses["buffer_overflow"] = self.check_register(
            False,
            status.buffer_overflow,
            error_msg=f"buffer_overflow mismatch. Expected False, Actual: {status.buffer_overflow}",
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

        if expected_value is not None:
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

        if expected_value is not None and register_value is not None:
            if expected_value == register_value:
                result = HealthState.OK
        else:
            result = HealthState.FAILED

        return result
