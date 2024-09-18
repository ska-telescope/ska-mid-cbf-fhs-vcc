import logging

import requests
from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.api_config_reader import APIConfigReader
from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import (
    FhsBaseApiInterface,
)


class BaseEmulatorApi(FhsBaseApiInterface):
    _emulator_config_key = "emulatorConfigPath"
    _emulator_base_url_key = "emulatorBaseUrl"
    _emulator_id_key = "emulatorId"
    _emulator_config_ipblock_key = "ip_blocks"
    _emulator_config_name = "0.0.1.json"

    # TODO have a way to dynamically grab the emulator host / port values from the emulator config file
    def __init__(self, device_id: str, config_location: str, logger: logging.Logger) -> None:
        logger.info(f"EMULATOR API: {device_id} {config_location}")

        self._device_id = device_id
        self._logger = logger

        self._api_base_url = self._generateDeviceApiUrl(config_location)
        self._json_header = {"Content-Type": "application/json"}

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
            return ResultCode.OK, (success_msg if success_msg is not None else f"{cmd} for {self._device_id} completed OK")
        else:
            return ResultCode.FAILED, response.reason

    def _generateDeviceApiUrl(self, config_location: str) -> str:
        try:
            self._logger.info(f"Generating {self._device_id} api url")

            api_config_reader = APIConfigReader(config_location, self._logger)

            emulator_config_path = api_config_reader.getConfigMapValue(self._emulator_config_key)
            emulator_base_url = api_config_reader.getConfigMapValue(self._emulator_base_url_key)
            emulator_id = api_config_reader.getConfigMapValue(self._emulator_id_key)

            emulator_config_path = f"{emulator_config_path}/{self._emulator_config_name}"

            self._logger.info(f"Emulator Config: {emulator_config_path}")

            emulator_config_json = api_config_reader._getFileContentsAsYamlOrJson(emulator_config_path, isYaml=False)

            api_url_base = None

            for ip_block in emulator_config_json[self._emulator_config_ipblock_key]:
                self._logger.info(f"IP_BLOCK ID: {ip_block['id']} , DEVICE_ID: {self._device_id}")
                if ip_block["id"] == self._device_id:
                    api_url_base = f"http://{emulator_id}.{emulator_base_url}/{ip_block['id']}"
                    break

            if api_url_base is None:
                raise KeyError(
                    f"{api_url_base} not found in emulator configuration. \
                        Ensure that the emulator ip block id corresponds to the device server id"
                )

            self._logger.debug(f"Base Emulator API Url created: {api_url_base}")
            return api_url_base

        except Exception as ex:
            self._logger.error("Unable to generate API URLs", repr(ex))
