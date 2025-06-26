from __future__ import annotations

from abc import abstractmethod
from logging import Logger
from threading import Lock
from typing import Callable, Type

from ska_control_model import HealthState, SimulationMode
from ska_mid_cbf_fhs_common import BaseSimulatorApi, FhsHealthMonitor

from ska_mid_cbf_fhs_vcc.ip_block_manager.base_ip_block_manager import BaseIPBlockManager


class BaseMonitoringIPBlockManager(BaseIPBlockManager):
    """Base class for health monitoring IP Block Manager classes."""

    def __init__(
        self,
        ip_block_id: str,
        bitstream_path: str,
        bitstream_id: str,
        bitstream_version: str,
        firmware_ip_block_id: str,
        simulator_api: Type[BaseSimulatorApi],
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        emulator_ip_block_id: str | None = None,
        emulator_id: str | None = None,
        emulator_base_url: str | None = None,
        logger: Logger | None = None,
        health_monitor_poll_interval: float = 30.0,
        update_health_state_callback: Callable = lambda _: None,
    ):
        if health_monitor_poll_interval <= 0.1:
            raise ValueError("health_monitor_poll_interval must be at least 0.1 seconds.")

        super().__init__(
            ip_block_id,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            simulator_api,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logger,
        )

        self._health_state_lock = Lock()
        self._update_health_state_callback = update_health_state_callback

        self.fhs_health_monitor = FhsHealthMonitor(
            logger=self.logger,
            get_device_health_state=self.get_health_state,
            update_health_state_callback=self._update_health_state,
            check_registers_callback=self.get_status_healthstates,
            api=self._api,
            poll_interval=health_monitor_poll_interval,
        )

    def start(self) -> int:
        try:
            self.fhs_health_monitor.start_polling()
            self._start()
        except Exception as e:
            self.logger.exception(e)
            return 1
        return 0

    def stop(self) -> int:
        try:
            self.fhs_health_monitor.stop_polling()
            self._stop()
        except Exception as e:
            self.logger.exception(e)
            return 1
        return 0

    def _start(self) -> None:
        super()._start()

    def _stop(self) -> None:
        super()._stop()

    def _update_health_state(self, health_state: HealthState) -> None:
        with self._health_state_lock:
            if self._health_state != health_state:
                self._health_state = health_state
                self._update_health_state_callback(health_state)

    @abstractmethod
    def get_status_healthstates(self, status_dict: dict) -> dict[str, HealthState]:
        ...
