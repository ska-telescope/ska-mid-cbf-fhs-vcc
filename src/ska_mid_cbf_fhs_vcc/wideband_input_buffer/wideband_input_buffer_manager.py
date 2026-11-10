from typing import Any

from ska_control_model import HealthState
from ska_mid_cbf_fhs_common import BaseMonitoringIPBlockManager, FhsDataclass, UInt8, UInt16, UInt32, UInt64, convert_dish_id_uint16_to_str, non_blocking

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_simulator import WidebandInputBufferSimulator


class WidebandInputBufferConfig(FhsDataclass):
    expected_sample_rate: UInt64
    noise_diode_transition_holdoff_count: int
    expected_dish_band: UInt8
    transaction_id: str | None = None


##
# status class that will be populated by the APIs and returned to provide the status of the Wideband Input Buffer
##
class WidebandInputBufferStatus(FhsDataclass):
    buffer_overflow: bool
    loss_of_signal: UInt32
    error: bool
    packet_error: bool
    packet_error_count: UInt32
    packet_drop: bool
    packet_drop_count: UInt32
    loss_of_signal_seconds: UInt32
    meta_band_id: UInt8
    meta_dish_id: UInt16
    rx_sample_rate: UInt32
    rx_packet_rate: UInt32
    meta_transport_sample_rate: UInt32
    link_failure: bool
    expected_sample_rate: UInt32


class WidebandInputBufferManager(BaseMonitoringIPBlockManager[WidebandInputBufferConfig, WidebandInputBufferStatus]):
    """Wideband Input Buffer IP block manager."""

    @property
    def config_dataclass(self) -> type[WidebandInputBufferConfig]:
        """:obj:`type[WidebandInputBufferConfig]`: The configuration dataclass for the Wideband Input Buffer."""
        return WidebandInputBufferConfig

    @property
    def status_dataclass(self) -> type[WidebandInputBufferStatus]:
        """:obj:`type[WidebandInputBufferStatus]`: The status dataclass for the Wideband Input Buffer."""
        return WidebandInputBufferStatus

    @property
    def simulator_api_class(self) -> type[WidebandInputBufferSimulator]:
        """:obj:`type[WidebandInputBufferSimulator]`: The simulator API class for the Wideband Input Buffer."""
        return WidebandInputBufferSimulator

    def _manager_specific_setup(self, **kwargs):
        self.expected_sample_rate: int | None = None
        self.expected_dish_id: str | None = None

    def configure(self, config: WidebandInputBufferConfig) -> int:
        """Configure the Wideband Input Buffer."""
        self.expected_sample_rate = config.expected_sample_rate
        return super().configure(config)

    def deconfigure(self, config: WidebandInputBufferConfig | None = None) -> int:
        """Deconfigure the Wideband Input Buffer."""
        if config is None:
            return super().recover()
        return super().deconfigure(config)

    @non_blocking
    def start(self) -> int:
        return super().start()

    @non_blocking
    def stop(self) -> int:
        return super().stop()

    def get_status_healthstates(self, status: WidebandInputBufferStatus) -> dict[str, HealthState]:
        status_healthstates = {}

        meta_dish_id_str = convert_dish_id_uint16_to_str(status.meta_dish_id)
        status_healthstates["meta_dish_id"] = self.get_health_state_by_expected_value(
            self.expected_dish_id,
            meta_dish_id_str,
            failure_msg=f"meta_dish_id mismatch. Expected: {self.expected_dish_id}, Actual: {meta_dish_id_str} ({status.meta_dish_id})",
        )

        status_healthstates["rx_sample_rate"] = self.get_health_state_by_expected_value(
            self.expected_sample_rate,
            status.rx_sample_rate,
            failure_msg=f"rx_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.rx_sample_rate}",
        )

        status_healthstates["meta_transport_sample_rate"] = self.get_health_state_by_expected_value(
            self.expected_sample_rate,
            status.meta_transport_sample_rate,
            failure_msg=f"meta_transport_sample_rate mismatch. Expected {self.expected_sample_rate}, Actual: {status.meta_transport_sample_rate}",
        )

        status_healthstates["packet_error"] = self.get_health_state_by_expected_value(
            False,
            status.packet_error,
            health_on_failure=HealthState.DEGRADED,
        )

        status_healthstates["packet_drop"] = self.get_health_state_by_expected_value(
            False,
            status.packet_drop,
            health_on_failure=HealthState.DEGRADED,
        )

        status_healthstates["link_failure"] = self.get_health_state_by_expected_value(
            False,
            status.link_failure,
            failure_msg=f"link_failure mismatch. Expected False, Actual: {status.link_failure}",
        )

        status_healthstates["buffer_overflow"] = self.get_health_state_by_expected_value(
            False,
            status.buffer_overflow,
            failure_msg=f"buffer_overflow mismatch. Expected False, Actual: {status.buffer_overflow}",
        )

        self.logger.info(f"REGISTER_STATUSES={status_healthstates}")

        return status_healthstates

    def get_health_state_by_expected_value(
        self,
        expected_value: Any,
        actual_value: Any,
        success_msg: str | None = None,
        failure_msg: str | None = None,
        health_on_success: HealthState = HealthState.OK,
        health_on_failure: HealthState = HealthState.FAILED,
    ) -> HealthState:
        if expected_value == actual_value:
            if success_msg:
                self.logger.info(success_msg)
            return health_on_success
        if failure_msg:
            self.logger.error(failure_msg)
        return health_on_failure
