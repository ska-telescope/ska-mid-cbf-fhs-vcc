from __future__ import annotations

import json
import logging
import os

import yaml


class APIConfigReader:
    def __init__(self: APIConfigReader, config_location: str, logger: logging.Logger) -> None:
        self._logger = logger
        config_map_path = f"{config_location}/low_level_ds_config.yaml"
        self._logger.info(f"Reading ConfigMap in location: {config_map_path}")
        self._config_map = self._getFileContentsAsYamlOrJson(config_map_path)
        pass

    def getConfigMapValue(self: APIConfigReader, key: str) -> str:
        return self._getConfigMapValue(self._config_map, key)

    def _getConfigMapValue(self: APIConfigReader, config_map: json, key: str) -> str:
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
