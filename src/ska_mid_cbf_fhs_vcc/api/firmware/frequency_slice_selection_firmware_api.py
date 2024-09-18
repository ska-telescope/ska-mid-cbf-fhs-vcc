from __future__ import annotations
import logging

from ska_mid_cbf_fhs_vcc.api.firmware.base_firmware_api import BaseFirmwareApi

__all__ = ["FrequencySliceSelectionFirmwareApi"]


class FrequencySliceSelectionFirmwareApi(BaseFirmwareApi):
    def __init__(self, config_location: str, logger: logging.Logger) -> None:
        super(FrequencySliceSelectionFirmwareApi, self).__init__(config_location, logger)
        from .contrib.driver_source_code.talon_dx_agilex_m_vcc_base_vcc_processing import (
            circuit_switch,
            fpga_driver_base,
        )

        # TODO: get these values from somewhere
        self._params = circuit_switch.param_t()
        self._regsetinfo = fpga_driver_base.RegisterSetInfo("", 0, 64, "2.0.0")
        self._regset = {"csr": self._regsetinfo}

        self._driver = circuit_switch.driver(self._params, self._regset, self._c_logger)
        self._config_t = circuit_switch.config_t
        self._status_t = circuit_switch.status_t
