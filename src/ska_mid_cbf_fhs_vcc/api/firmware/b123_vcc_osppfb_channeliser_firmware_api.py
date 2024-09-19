from __future__ import annotations

import logging

from ska_mid_cbf_fhs_vcc.api.firmware.base_firmware_api import BaseFirmwareApi

__all__ = ["B123VccOsppfbChanneliserFirmwareApi"]


class B123VccOsppfbChanneliserFirmwareApi(BaseFirmwareApi):
    def __init__(self, config_location: str, logger: logging.Logger) -> None:
        super(B123VccOsppfbChanneliserFirmwareApi, self).__init__(config_location, logger)
        from .contrib.driver_source_code.talon_dx_agilex_m_vcc_base_vcc_processing import fpga_driver_base, vcc_ch20

        # TODO: get these values from somewhere
        self._params = vcc_ch20.param_t()
        self._regsetinfo = fpga_driver_base.RegisterSetInfo("", 0, 64, "1.0.0")
        self._regset = {"csr": self._regsetinfo}

        self._driver = vcc_ch20.driver(self._params, self._regset, self._c_logger)
        self._config_t = vcc_ch20.config_t
        self._status_t = vcc_ch20.status_t
