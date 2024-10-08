from __future__ import annotations

import json
import logging
import sys

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.api_config_reader import APIConfigReader
from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class BaseFirmwareApi(FhsBaseApiInterface):
    def __init__(self: BaseFirmwareApi, device_id: str, config_location: str, logger: logging.Logger) -> None:
        logger.info(f"FIRMWARE API: {config_location}")

        self._logger = logger

        api_config_reader = APIConfigReader(config_location, self._logger)

        version = api_config_reader.getConfigMapValue("firmwareVersion")
        driver_path = "/app/mnt/bitstream/" + version + "/drivers/"

        try:
            logger.info("Loading driver from: " + driver_path)
            sys.path.append(driver_path)
            from py_driver_initializer import Py_Driver_Initializer
        except ImportError as e:
            msg = f"Driver version {version} not found in volume mount {driver_path}: {e!r}"
            logger.error(msg)
            raise RuntimeError(msg)

        self._initializer = Py_Driver_Initializer(instance_name=device_id, memory_map_file="/dev/null", logger=logger)
        self._driver = self._initializer.driver

    def recover(self) -> tuple[ResultCode, str]:
        self._driver.driver.recover()
        return ResultCode.OK, "Recover Called Successfully"

    def configure(self, config: dict) -> tuple[ResultCode, str]:
        self._driver.driver.configure(self._driver.config_t(**config))
        return ResultCode.OK, "Configure Called Successfully"

    def start(self) -> tuple[ResultCode, str]:
        self._driver.driver.start()
        return ResultCode.OK, "Start Called Successfully"

    def stop(self, force: bool = False) -> tuple[ResultCode, str]:
        self._driver.driver.stop(force)
        return ResultCode.OK, "Stop Called Successfully"

    def deconfigure(self, config: dict) -> tuple[ResultCode, str]:
        self._driver.driver.deconfigure(self._driver.config_t(**config))
        return ResultCode.OK, "Deconfigure Called Successfully"

    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        status_t = self._driver.status_t()
        self._driver.driver.status(status_t, clear)
        status = {attr: getattr(status_t, attr) for attr in dir(status_t) if not attr.startswith("_")}
        return ResultCode.OK, json.dumps(status)
