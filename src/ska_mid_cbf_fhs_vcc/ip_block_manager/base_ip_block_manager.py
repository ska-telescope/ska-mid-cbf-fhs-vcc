from __future__ import annotations

import os
from abc import ABC
from logging import Logger
from typing import Type

from ska_control_model import HealthState, SimulationMode
from ska_mid_cbf_fhs_common import BaseSimulatorApi, EmulatorApi, FhsBaseApiInterface, FirmwareApi


class BaseIPBlockManager(ABC):
    """Base class for IP Block Manager classes."""

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
    ):
        self._simulation_mode = simulation_mode
        self._emulation_mode = emulation_mode

        self.logger = logger if logger is not None else Logger(ip_block_id)
        self.logger.info(f"Api starting for simulation_mode: {simulation_mode}, emulation_mode: {emulation_mode}")
        _bitstream_path = os.path.join(bitstream_path, bitstream_id, bitstream_version)

        self.ip_block_id = ip_block_id

        self._api: FhsBaseApiInterface
        if self._simulation_mode == SimulationMode.TRUE and simulator_api is not None:
            self._api = simulator_api(self.ip_block_id, self.logger)
        elif self._simulation_mode == SimulationMode.FALSE and self._emulation_mode and emulator_ip_block_id is not None:
            self._api = EmulatorApi(_bitstream_path, emulator_ip_block_id, emulator_id, emulator_base_url, self.logger)
        else:
            self._api = FirmwareApi(_bitstream_path, firmware_ip_block_id, self.logger)

        self._health_state = HealthState.OK

    def get_health_state(self) -> HealthState:
        return self._health_state

    def configure(self, argin: dict | None = None) -> int:
        try:
            self._configure(argin)
        except Exception as e:
            self.logger.exception(e)
            return 1
        return 0

    def deconfigure(self, argin: dict | None = None) -> int:
        try:
            self._deconfigure(argin)
        except Exception as e:
            self.logger.exception(e)
            return 1
        return 0

    def start(self) -> int:
        try:
            self._start()
        except Exception as e:
            self.logger.exception(e)
            return 1
        return 0

    def stop(self) -> int:
        try:
            self._stop()
        except Exception as e:
            self.logger.exception(e)
            return 1
        return 0

    def recover(self) -> int:
        try:
            self._recover()
        except Exception as e:
            self.logger.exception(e)
            return 1
        return 0

    def status(self, clear: bool = False) -> dict | None:
        try:
            result = self._status(clear)
        except Exception as e:
            self.logger.exception(e)
            return None
        return result

    def _configure(self, argin: dict | None = None) -> None:
        self._api.configure(argin)

    def _deconfigure(self, argin: dict | None = None) -> None:
        self._api.deconfigure(argin)

    def _start(self) -> None:
        self._api.start()

    def _stop(self) -> None:
        self._api.stop()

    def _recover(self) -> None:
        self._api.recover()

    def _status(self, clear: bool = False) -> dict:
        return self._api.status(clear)[1]
