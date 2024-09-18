import logging

from ska_mid_cbf_fhs_vcc.api.emulator.base_emulator_api import BaseEmulatorApi


class FrequencySliceSelectionEmulatorApi(BaseEmulatorApi):
    def __init__(self, device_id: str, config_location: str, logger: logging.Logger) -> None:
        super().__init__(device_id=device_id, config_location=config_location, logger=logger)
