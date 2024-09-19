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

        from .contrib.driver_source_code.talon_dx_agilex_m_vcc_base_vcc_processing import fpga_driver_base

        class CLogger(fpga_driver_base.Logger):
            severity_to_level = {
                "Failure": logging.CRITICAL,
                "Error": logging.ERROR,
                "Warning": logging.WARNING,
                "Info": logging.INFO,
                "Pass": logging.INFO,
                "Debug": logging.DEBUG,
                "Trace": logging.DEBUG,
            }
            level_to_severity = {v: k for k, v in reversed(severity_to_level.items())}

            def __init__(self, level: int = logging.WARNING):
                """Init the C logger with the provided python log level"""
                fpga_driver_base.Logger.__init__(self, fpga_driver_base.LogLevel.__members__[self.level_to_severity[level]])
                self._monkey_patch_set_level()

            def log_message(self, severity: fpga_driver_base.Loglevel, msg: str):
                """Override the C log_message and forward logs to the python logger"""
                logger.log(self.severity_to_level[severity.name], msg)

            def _monkey_patch_set_level(self):
                """Hook the python setLevel function and forward the new level to C"""
                if hasattr(logger, "_is_c_patched") and logger._is_c_patched:
                    return

                original_setLevel = logger.setLevel

                def patched_setLevel(level):
                    original_setLevel(level)
                    severity = fpga_driver_base.LogLevel.__members__[self.level_to_severity[level]]
                    logger.info(f"Setting C logger to level {severity.name}")
                    self.set_logging_level(severity)

                logger.setLevel = patched_setLevel
                logger._is_c_patched = True

        # --- resources to be used by child classes
        self._c_logger = CLogger(logger.getEffectiveLevel())

        # --- resources to be provided by child classes
        # self._driver = None
        # self._config_t = None
        # self._status_t = None

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

    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        status_t = self._status_t()
        self._driver.status(status_t, clear)
        status = {attr: getattr(status_t, attr) for attr in dir(status_t) if not attr.startswith("_")}
        return ResultCode.OK, json.dumps(status)

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
            raise RuntimeError(f"Failed to pull with error code {resp.status_code}")

        self._logger.info(f"Extracting data from pulled artefact to {dirpath}")
        with tarfile.open(fileobj=BytesIO(resp.content), mode="r:gz") as tar:
            tar.extractall(path=dirpath, filter="tar")
        self._logger.info(f"Extracted successfully to {dirpath}.")
