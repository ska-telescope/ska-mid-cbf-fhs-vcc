from dataclasses import dataclass
from logging import Logger
from typing import Any, Callable

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import HealthState, SimulationMode
from ska_mid_cbf_fhs_common import convert_dish_id_uint16_t_to_mnemonic

from ska_mid_cbf_fhs_vcc.ip_block_manager.base_monitoring_ip_block_manager import BaseMonitoringIPBlockManager
from ska_mid_cbf_fhs_vcc.ip_block_manager.non_blocking_function import non_blocking
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


class WidebandInputBufferManager(BaseMonitoringIPBlockManager):
    """Mock Wideband Input Buffer IP block manager."""

    def __init__(
        self,
        ip_block_id: str,
        bitstream_path: str,
        bitstream_id: str,
        bitstream_version: str,
        firmware_ip_block_id: str,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        emulator_ip_block_id: str | None = None,
        emulator_id: str | None = None,
        emulator_base_url: str | None = None,
        logger: Logger | None = None,
        health_monitor_poll_interval: float = 30.0,
        update_health_state_callback: Callable = lambda _: None,
    ):
        self.test_attr_value: int = 15
        self.expected_sample_rate = None
        self.expected_dish_id = None

        super().__init__(
            ip_block_id,
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
            logger,
            health_monitor_poll_interval,
            update_health_state_callback,
        )

    def configure(self, config: WidebandInputBufferConfig):
        """Configure the Wideband Input Buffer."""
        self.expected_sample_rate = config.expected_sample_rate
        return super().configure(config.to_dict())

    @non_blocking
    def start(self) -> int:
        return super().start()

    @non_blocking
    def stop(self) -> int:
        return super().stop()

    def check_registers(self, status_dict: dict) -> dict[str, HealthState]:
        status: WidebandInputBufferStatus = WidebandInputBufferStatus.schema().load(status_dict)

        register_statuses = {}

        meta_dish_id_mnemonic = convert_dish_id_uint16_t_to_mnemonic(status.meta_dish_id)
        register_statuses["meta_dish_id"] = self.health_check_assert_values_equal(
            self.expected_dish_id,
            meta_dish_id_mnemonic,
            error_msg=f"meta_dish_id mismatch. Expected: {self.expected_dish_id}, Actual: {meta_dish_id_mnemonic} ({status.meta_dish_id})",
        )
        register_statuses["rx_sample_rate"] = self.health_check_assert_values_equal(
            self.expected_sample_rate,
            status.rx_sample_rate,
            error_msg=f"rx_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.rx_sample_rate}",
        )
        register_statuses["meta_transport_sample_rate"] = self.health_check_assert_values_equal(
            self.expected_sample_rate,
            status.meta_transport_sample_rate,
            error_msg=f"meta_transport_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.meta_transport_sample_rate}",
        )

        self.logger.info(f"REGISTER_STATUSES={register_statuses}")

        return register_statuses

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
