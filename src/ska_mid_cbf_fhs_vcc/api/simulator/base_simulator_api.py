from __future__ import annotations

import json
import logging

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class BaseSimulatorApi(FhsBaseApiInterface):
    def __init__(self: BaseSimulatorApi, device_id: str, logger: logging.Logger) -> None:
        logger.info(f"SIMULATOR API: {device_id}")

        self.mac_id = device_id
        self._logger = logger

    def recover(self) -> tuple[ResultCode, str]:
        self._logger.info("Recover called from the simulator")
        return ResultCode.OK, "Recover Called Successfully"

    def configure(self, config: dict) -> tuple[ResultCode, str]:
        self._logger.info("Configure was called from the simulator")

        gains_json = json.loads(config)

        self._logger.info(f"Received gains: {gains_json}")
        return ResultCode.OK, "Configure Called Successfully"

    def start(self) -> tuple[ResultCode, str]:
        self._logger.info("Start was called from the simulator")
        return ResultCode.OK, "Start Called Successfully"

    def stop(self, force: bool = False) -> tuple[ResultCode, str]:
        self._logger.info("Stop was called from the simulator")
        return ResultCode.OK, "Stop Called Successfully"

    def deconfigure(self, config) -> tuple[ResultCode, str]:
        self._logger.info("Deconfigure was called from the simulator")
        return ResultCode.OK, "Deconfigure Called Successfully"

    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        self._logger.info("Status was called from the simulator")
        return ResultCode.OK, "Status Called Successfully"
