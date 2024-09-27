from __future__ import annotations

import json
import logging
import os
import tarfile
from io import BytesIO

import requests
from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.api_config_reader import APIConfigReader
from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class BaseFirmwareApi(FhsBaseApiInterface):
    def __init__(self: BaseFirmwareApi, device_id: str, config_location: str, logger: logging.Logger) -> None:
        logger.info(f"FIRMWARE API: {config_location}")

        self._logger = logger
        self._download_fw(config_location)

        from .contrib.drivers.py_driver_initializer import Py_Driver_Initializer

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

    def _download_fw(self, config_location: str):
        """
        Download firmware pybind libraries to ./contrib
        """
        if hasattr(BaseFirmwareApi, "_has_downloaded_fw") and BaseFirmwareApi._has_downloaded_fw:
            return

        api_config_reader = APIConfigReader(config_location, self._logger)

        registry = api_config_reader.getConfigMapValue("firmwareRegistry")
        bitstream_id = api_config_reader.getConfigMapValue("firmwareImage")
        version = api_config_reader.getConfigMapValue("firmwareVersion")

        url = f"{registry}/{bitstream_id}-{version}.tar.gz"
        dirpath = os.path.join(os.path.dirname(__file__), "contrib")

        self._logger.info(f"Attempting to pull `{url}`...")
        resp = requests.get(url)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to pull with error code {resp.status_code}")

        self._logger.info(f"Extracting data from pulled artefact to {dirpath}")
        with tarfile.open(fileobj=BytesIO(resp.content), mode="r:gz") as tar:
            tar.extractall(path=dirpath, filter="tar")
        self._logger.info(f"Extracted successfully to {dirpath}.")

        BaseFirmwareApi._has_downloaded_fw = True
