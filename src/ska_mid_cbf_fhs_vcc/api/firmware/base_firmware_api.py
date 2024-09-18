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
    def __init__(self: BaseFirmwareApi, config_location: str, logger: logging.Logger) -> None:
        logger.info(f"FIRMWARE API: {config_location}")

        self._logger = logger
        self._download_fw(config_location)

        # TODO: extend the C logger to forward messages to the python logger
        from .contrib.driver_source_code.talon_dx_agilex_m_vcc_base_vcc_processing import fpga_driver_base

        # --- resources to be used by child classes
        self._c_logger = fpga_driver_base.Logger(fpga_driver_base.LogLevel.Debug)

        # --- resources to be provided by child classes
        self._driver = None
        self._config_t = None
        self._status_t = None

    def recover(self) -> tuple[ResultCode, str]:
        try:
            self._driver.recover()
        except Exception as exc:
            return ResultCode.FAILED, f"Recover failed: {exc!r}"
        else:
            return ResultCode.OK, "Recover Called Successfully"

    def configure(self, config: dict) -> tuple[ResultCode, str]:
        try:
            self._driver.configure(self._config_t(**config))
        except Exception as exc:
            return ResultCode.FAILED, f"Configure failed: {exc!r}"
        else:
            return ResultCode.OK, "Configure Called Successfully"

    def start(self) -> tuple[ResultCode, str]:
        try:
            self._driver.start()
        except Exception as exc:
            return ResultCode.FAILED, f"Start failed: {exc!r}"
        else:
            return ResultCode.OK, "Start Called Successfully"

    def stop(self, force: bool = False) -> tuple[ResultCode, str]:
        try:
            self._driver.stop(force)
        except Exception as exc:
            return ResultCode.FAILED, f"Stop failed: {exc!r}"
        else:
            return ResultCode.OK, "Stop Called Successfully"

    def deconfigure(self, config: dict) -> tuple[ResultCode, str]:
        try:
            self._driver.deconfigure(self._config_t(**config))
        except Exception as exc:
            return ResultCode.FAILED, f"Deconfigure failed: {exc!r}"
        else:
            return ResultCode.OK, "Deconfigure Called Successfully"

    def status(self, status: dict, clear: bool = False) -> tuple[ResultCode, str]:
        try:
            status_t = self._status_t(**status)
            self._driver.status(status_t, clear)
        except Exception as exc:
            return ResultCode.FAILED, f"Status failed: {exc!r}"
        else:
            return ResultCode.OK, json.dumps(status_t)

    def _download_fw(self, config_location: str):
        """
        Download firmware pybind libraries to ./contrib
        """
        api_config_reader = APIConfigReader(config_location, self._logger)

        registry = api_config_reader.getConfigMapValue("firmwareRegistry")
        bitstream_id = api_config_reader.getConfigMapValue("firmwareImage")
        version = api_config_reader.getConfigMapValue("firmwareVersion")

        url = f"{registry}/{bitstream_id}-{version}.tar.gz"
        dirpath = os.path.join(os.path.dirname(__file__), "contrib")

        self._logger.info(f"Attempting to pull `{url}`...")
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception(f"Failed to pull with error code {resp.status_code}")

        self._logger.info(f"Extracting data from pulled artefact to {dirpath}")
        with tarfile.open(fileobj=BytesIO(resp.content), mode="r:gz") as tar:
            tar.extractall(path=dirpath, filter="tar")
        self._logger.info(f"Extracted successfully to {dirpath}.")
