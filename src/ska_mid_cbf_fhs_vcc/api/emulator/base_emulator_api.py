import json
import logging
import os

import requests
from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class BaseEmulatorApi(FhsBaseApiInterface):
    def __init__(
        self,
        bitstream_path: str,
        emulator_ip_block_id: str,
        emulator_id: str,
        emulator_base_url: str,
        logger: logging.Logger,
    ) -> None:
        logger.info(f".....................EMULATOR API: {bitstream_path} {emulator_ip_block_id}........................")

        self._logger = logger

        bitstream_emulator_config_path = os.path.join(bitstream_path, "emulators", "config.json")

        self._api_base_url = self._generateDeviceApiUrl(
            bitstream_emulator_config_path, emulator_ip_block_id, emulator_id, emulator_base_url
        )
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
        response = requests.post(f"{self._api_base_url}/start", headers=self._json_header, json={})
        return self._get_response_status(response, "Start")

    def stop(self, force: bool = False) -> int:
        response = requests.post(f"{self._api_base_url}/stop", headers=self._json_header, json={})
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

        response_dict: dict = response.json()

        if response_dict.get("request_validation_result") is not None:
            response_dict.pop("request_validation_result")

        return self._get_response_status(response=response, cmd="GetStatus", success_msg=response_dict)

    def _get_response_status(
        self, response: requests.Response, cmd: str, success_msg: str | dict | None = None
    ) -> tuple[ResultCode, str]:
        if response.status_code >= 200 and response.status_code < 300:
            return ResultCode.OK, (success_msg if success_msg is not None else f"{cmd} completed OK")
        else:
            return ResultCode.FAILED, response.reason

    def _generateDeviceApiUrl(
        self, bitstream_emulator_config_path: str, emulator_ip_block_id: str, emulator_id: str, emulator_base_url: str
    ) -> str:
        try:
            self._logger.info(
                f"Generating {emulator_ip_block_id} api url for emulator {emulator_id} using config {bitstream_emulator_config_path}"
            )

            if os.path.isfile(bitstream_emulator_config_path):
                with open(bitstream_emulator_config_path, "r") as config_file:
                    emulator_config_json = json.load(config_file)
            else:
                raise FileNotFoundError(f"Unable to open file, {bitstream_emulator_config_path} not found")

            api_url_base = None

            # Loop through the emulators config file checking that the given emulator_ip_block_id exists in the list of
            # emulator ip blocks, if it doesn't exist in the emulator config then we have a configuration error between
            # the device server and the emulator
            for ip_block in emulator_config_json["ip_blocks"]:
                if ip_block["id"] == emulator_ip_block_id:
                    self._logger.info(f"IP_BLOCK ID: {ip_block['id']}, DEVICE_ID: {emulator_ip_block_id}")
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
