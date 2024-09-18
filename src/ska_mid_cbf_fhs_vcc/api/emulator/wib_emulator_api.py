import logging

from ska_mid_cbf_fhs_vcc.api.emulator.base_emulator_api import BaseEmulatorApi


class WibEmulatorApi(BaseEmulatorApi):
    def __init__(self, device_id: str, config_location: str, logger: logging.Logger) -> None:
        super().__init__(device_id, config_location, logger)
