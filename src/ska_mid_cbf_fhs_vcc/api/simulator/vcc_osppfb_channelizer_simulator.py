from __future__ import annotations

import json

from ska_control_model import ResultCode
from logging import Logger
from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["VccOsppfbChannelizerSimulator"]


class VccOsppfbChannelizerSimulator(BaseSimulatorApi):
    def __init__(self: VccOsppfbChannelizerSimulator, device_id: str, logger: Logger, channelizer_type: str) -> None:
        self._status_str = ''
        if channelizer_type == "B123":
            self._status_str = {"sample_rate": 3_960_000_000, "num_channels": 10, "num_polarisations": 2, "gains": [1.0 for i in range(20)]}
        else:
            self._status_str = {"sample_rate": 11_880_000_000, "num_channels": 15, "num_polarisations": 2, "gains": [1.0 for i in range(30)]}
        super.__init__(device_id, logger)
        
    def status(self, clear: bool = False) -> tuple[ResultCode, dict]:
        return (
            ResultCode.OK,
            json.dumps(
                self._status_str
            ),
        )
