from __future__ import annotations

import json
import logging
import os

import yaml  # allow forward references in type hints


class EmulatorApiUrlGenerator:
    def __init__(self: EmulatorApiUrlGenerator, logger: logging.Logger) -> None:
        self._emulator_config_key = "emulatorConfigPath"
        self._emulator_base_url_key = "emulatorBaseUrl"
        self._emulator_id_key = "emulatorId"
        self._emulator_config_ipblock_key = "ip_blocks"
        self._logger = logger
        self._config_map_name = "low_level_ds_config.yaml"
        self._emulator_config_name = "0.0.1.json"
        pass

    def generateDeviceApiUrl(
        self: EmulatorApiUrlGenerator, device_id: str, config_location: str
    ) -> str:
        try:
            config_map_path = f"{config_location}/{self._config_map_name}"

            self._logger.info(f"ConfigMap location: {config_map_path}")
            self._logger.info(f"Generating {device_id} api url")

            config_map = self._getFileContentsAsYamlOrJson(config_map_path)

            emulator_config_path = self._getConfigMapValue(config_map, self._emulator_config_key)
            emulator_base_url = self._getConfigMapValue(config_map, self._emulator_base_url_key)
            emulator_id = self._getConfigMapValue(config_map, self._emulator_id_key)

            emulator_config_path = f"{emulator_config_path}/{self._emulator_config_name}"

            self._logger.info(f"Emulator Config: {emulator_config_path}")

            emulator_config_json = self._getFileContentsAsYamlOrJson(
                emulator_config_path, isYaml=False
            )

            api_url_base = None

            for ip_block in emulator_config_json[self._emulator_config_ipblock_key]:
                self._logger.info(f"IP_BLOCK ID: {ip_block['id']} , DEVICE_ID: {device_id}")
                if ip_block["id"] == device_id:
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

    def _getConfigMapValue(self: EmulatorApiUrlGenerator, config_map: json, key: str) -> str:
        if key in config_map:
            return config_map[key]
        else:
            raise KeyError(f"{key} not found in ConfigMap {config_map}")

    def _getFileContentsAsYamlOrJson(self, path: str, isYaml: bool = True) -> json:
        if os.path.isfile(path):
            with open(path, "r") as config_file:
                if isYaml:
                    return yaml.safe_load(config_file)
                else:
                    return json.load(config_file)
        else:
            raise FileNotFoundError(f"Unable to open file, {path} not found")
