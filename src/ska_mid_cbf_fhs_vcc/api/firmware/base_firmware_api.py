from __future__ import annotations

import logging
import os
import sys

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class BaseFirmwareApi(FhsBaseApiInterface):
    def __init__(self: BaseFirmwareApi, bitstream_path: str, firmware_ip_block_id: str, logger: logging.Logger) -> None:
        logger.info(f".....................FIRMWARE API: {bitstream_path} {firmware_ip_block_id}........................")

        self._logger = logger

        driver_path = os.path.join(bitstream_path, "drivers")

        try:
            logger.info("Loading driver from: " + driver_path)
            sys.path.append(driver_path)
            from py_driver_initializer import Py_Driver_Initializer
        except ImportError as e:
            msg = f"Driver not found in {driver_path}: {e!r}"
            logger.error(msg)
            raise RuntimeError(msg)

        memory_map_file = ""
        logger.info(f"Initializing driver with firmware_id: {firmware_ip_block_id}, and memory_map: {memory_map_file}")
        self._initializer = Py_Driver_Initializer(
            instance_name=firmware_ip_block_id, memory_map_file=memory_map_file, logger=logger
        )
        self._config_t = self._initializer.driver_submodule.config_t
        self._status_t = self._initializer.driver_submodule.status_t
        self._driver = self._initializer.driver

    def recover(self) -> tuple[ResultCode, str]:
        self._driver.recover()
        return ResultCode.OK, "Recover Called Successfully"

    def configure(self, config: dict) -> tuple[ResultCode, str]:
        self._driver.configure(self._config_t(**config))
        return ResultCode.OK, "Configure Called Successfully"

    def start(self) -> tuple[ResultCode, str]:
        self._driver.start()
        return ResultCode.OK, "Start Called Successfully"

    def stop(self, force: bool = False) -> tuple[ResultCode, str]:
        self._driver.stop(force)
        return ResultCode.OK, "Stop Called Successfully"

    def deconfigure(self, config: dict) -> tuple[ResultCode, str]:
        self._driver.deconfigure(self._config_t(**config))
        return ResultCode.OK, "Deconfigure Called Successfully"

    def status(self, clear: bool = False) -> tuple[ResultCode, dict]:
        status_t = self._status_t()
        self._driver.status(status_t, clear)
        status = {attr: getattr(status_t, attr) for attr in dir(status_t) if not attr.startswith("_")}
        return ResultCode.OK, status
