import logging

import requests
from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.api.emulator.utils.emulator_api_url_generator import EmulatorApiUrlGenerator


class BaseEmulatorApi(FhsBaseApiInterface):
    # TODO have a way to dynamically grab the emulator host / port values from the emulator config file
    def __init__(self, device_id: str, config_location: str, logger: logging.Logger) -> None:
        self._device_id = device_id
        self._config_location = config_location
        self._api_url_generator = EmulatorApiUrlGenerator(logger)
        self._api_base_url = self._api_url_generator.generateDeviceApiUrl(self._device_id, self._config_location)
        self._json_header = {"Content-Type": "application/json"}
        self._logger = logger

    def recover(self) -> tuple[ResultCode, str]:
        response = requests.post(f"{self._api_base_url}/recover")
        return self._get_response_status(response, "Recover")

    def configure(self, config) -> tuple[ResultCode, str]:
        self._logger.info("............:::configuring from emulator api:::")

        response = requests.post(
            f"{self._api_base_url}/configure",
            headers=self._json_header,
            json=config,
        )

        return self._get_response_status(response, "Configure")

    def start(self) -> tuple[ResultCode, str]:
        response = requests.get(f"{self._api_base_url}/start")
        return self._get_response_status(response, "Start")

    def stop(self, force: bool = False) -> int:
        response = requests.get(f"{self._api_base_url}/stop")
        return self._get_response_status(response, "Stop")

    def deconfigure(self, config) -> tuple[ResultCode, str]:
        response = requests.post(
            f"{self._api_base_url}/deconfigure",
            headers=self._json_header,
            json=config,
        )
        return self._get_response_status(response, "Deconfigure")

    def status(self, status, clear: bool = False) -> tuple[ResultCode, str]:
        response = requests.get(f"{self._api_base_url}/status/clear={clear}")
        return self._get_response_status(self, "Status", response.content)

    def _get_response_status(
        self, response: requests.Response, cmd: str, success_msg: str | None = None
    ) -> tuple[ResultCode, str]:
        if response.status_code >= 200 and response.status_code < 300:
            return ResultCode.OK, success_msg if success_msg is not None else f"{cmd} for {self._device_id} completed OK"
        else:
            return ResultCode.FAILED, response.reason
