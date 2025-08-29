from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import HealthState, SimulationMode
from ska_mid_cbf_fhs_common import BaseMonitoringIPBlockManager, convert_dish_id_uint16_t_to_mnemonic, non_blocking

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


class WidebandInputBufferManager(BaseMonitoringIPBlockManager):
    """Mock Wideband Input Buffer IP block manager."""

    def __init__(
        self,
        ip_block_id: str,
        controlling_device_name: str,
        bitstream_path: str,
        bitstream_id: str,
        bitstream_version: str,
        firmware_ip_block_id: str,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        emulator_ip_block_id: str | None = None,
        emulator_id: str | None = None,
        emulator_base_url: str | None = None,
        logging_level: str = "INFO",
        health_monitor_poll_interval: float = 30.0,
        update_health_state_callback: Callable = lambda _: None,
    ):
        self.test_attr_value: int = 15
        self.expected_sample_rate = None
        self.expected_dish_id = None

        super().__init__(
            ip_block_id,
            controlling_device_name,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            WidebandInputBufferSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logging_level,
            health_monitor_poll_interval,
            update_health_state_callback,
        )

    def configure(self, config: WidebandInputBufferConfig) -> int:
        """Configure the Wideband Input Buffer."""
        self.expected_sample_rate = config.expected_sample_rate
        return super().configure(config.to_dict())

    @non_blocking
    def start(self) -> int:
        return super().start()

    @non_blocking
    def stop(self) -> int:
        return super().stop()

    def get_status_healthstates(self, status_dict: dict) -> dict[str, HealthState]:
        status: WidebandInputBufferStatus = WidebandInputBufferStatus.schema().load(status_dict)

        status_healthstates = {}

        meta_dish_id_mnemonic = convert_dish_id_uint16_t_to_mnemonic(status.meta_dish_id)
        status_healthstates["meta_dish_id"] = self.health_check_assert_values_equal(
            self.expected_dish_id,
            meta_dish_id_mnemonic,
            error_msg=f"meta_dish_id mismatch. Expected: {self.expected_dish_id}, Actual: {meta_dish_id_mnemonic} ({status.meta_dish_id})",
        )

        status_healthstates["rx_sample_rate"] = self.health_check_assert_values_equal(
            self.expected_sample_rate,
            status.rx_sample_rate,
            error_msg=f"rx_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.rx_sample_rate}",
        )

        status_healthstates["meta_transport_sample_rate"] = self.health_check_assert_values_equal(
            self.expected_sample_rate,
            status.meta_transport_sample_rate,
            error_msg=f"meta_transport_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.meta_transport_sample_rate}",
        )

        if status.error:
            if status.buffer_overflow is True or status.link_failure is True:
                status_healthstates["error"] = HealthState.FAILED
            else:
                # if not overflow or underflow, goes to degraded because one of packet_drop and packet_error set
                status_healthstates["error"] = HealthState.DEGRADED
        else:
            status_healthstates["error"] = HealthState.OK

        status_healthstates["link_failure"] = self.health_check_assert_values_equal(
            False,
            status.link_failure,
            error_msg=f"link_failure mismatch. Expected False, Actual: {status.link_failure}",
        )

        status_healthstates["buffer_overflow"] = self.health_check_assert_values_equal(
            False,
            status.buffer_overflow,
            error_msg=f"buffer_overflow mismatch. Expected False, Actual: {status.buffer_overflow}",
        )

        self.logger.info(f"REGISTER_STATUSES={status_healthstates}")

        return status_healthstates

    def health_check_assert_values_equal(
        self,
        expected_value: Any,
        actual_value: Any,
        success_msg: str = None,
        error_msg: str = None,
    ) -> HealthState:
        if expected_value == actual_value:
            if success_msg:
                self.logger.info(success_msg)
            return HealthState.OK
        if error_msg:
            self.logger.error(error_msg)
        return HealthState.FAILED
