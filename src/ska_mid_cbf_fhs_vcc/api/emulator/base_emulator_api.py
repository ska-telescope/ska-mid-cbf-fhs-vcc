import logging

import requests
from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.api_config_reader import APIConfigReader
from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class BaseEmulatorApi(FhsBaseApiInterface):
    _bitstream_emulator_config_key = "bitstreamEmulatorConfigPath"
    _emulator_base_url_key = "emulatorBaseUrl"
    _emulator_config_ipblock_key = "ip_blocks"
    _firmware_version_key = "firmwareVersion"
    _bitstream_path_key = "bitstreamPath"
    _bitstream_id_key = "bitstreamId"

    # TODO have a way to dynamically grab the emulator host / port values from the emulator config file
    def __init__(
        self, device_id: str, config_location: str, emulator_ipblock_id: str, emulator_id: str, logger: logging.Logger
    ) -> None:
        logger.info(f".....................EMULATOR API: {device_id} {config_location}........................")

        self._emulator_id = device_id - 1
        self._logger = logger

        self._api_base_url = self._generateDeviceApiUrl(config_location, emulator_ipblock_id, emulator_id)
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

    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        self._logger.info(f"GETTING STATUS FROM {self._api_base_url}/status")
        response = requests.get(f"{self._api_base_url}/status")
        self._logger.info(response)
        return self._get_response_status(response=response, cmd="GetStatus", success_msg=response.content)

    def _get_response_status(
        self, response: requests.Response, cmd: str, success_msg: str | None = None
    ) -> tuple[ResultCode, str]:
        if response.status_code >= 200 and response.status_code < 300:
            return ResultCode.OK, (success_msg if success_msg is not None else f"{cmd} completed OK")
        else:
            return ResultCode.FAILED, response.reason

    def _generateDeviceApiUrl(self, config_location: str, emulator_ipblock_id: str, emulator_id: str) -> str:
        try:
            self._logger.info(f"Generating {emulator_ipblock_id} api url for emulator {self._emulator_id + 1}")

            api_config_reader = APIConfigReader(config_location, self._logger)

            bitstream_path = api_config_reader.getConfigMapValue(self._bitstream_path_key)
            bitstream_id = api_config_reader.getConfigMapValue(self._bitstream_id_key)
            bitstream_version = api_config_reader.getConfigMapValue(self._firmware_version_key)
            bitstream_emulator_config_path = api_config_reader.getConfigMapValue(self._bitstream_emulator_config_key)
            emulator_base_url = api_config_reader.getConfigMapValue(self._emulator_base_url_key)

            bitstream_id = bitstream_id.replace("-", "_")
            bitstream_version = f"_{bitstream_version.replace('.', '_')}"

            bitstream_emulator_config_path = (
                f"{bitstream_path}/{bitstream_id}/{bitstream_version}/{bitstream_emulator_config_path}"
            )

            self._logger.info(f"Emulator Config: {bitstream_emulator_config_path}")

            emulator_config_json = api_config_reader._getFileContentsAsYamlOrJson(bitstream_emulator_config_path, isYaml=False)

            api_url_base = None

            # Loop through the emulators config file checking that the given emulator_ipblock_id exists in the list of
            # emulator ip blocks, if it doesn't exist in the emulator config then we have a configuration error between
            # the device server and the emulator
            for ip_block in emulator_config_json[self._emulator_config_ipblock_key]:
                self._logger.info(f"IP_BLOCK ID: {ip_block['id']} , DEVICE_ID: {emulator_ipblock_id}")
                if ip_block["id"] == emulator_ipblock_id:
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
