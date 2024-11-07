from __future__ import annotations

import json

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["B123VccOsppfbChanneliserSimulator"]


class B123VccOsppfbChanneliserSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> tuple[ResultCode, dict]:
        return (
            ResultCode.OK,
            json.loads(
                '{"sample_rate": 3960000000, "num_channels": 10, "num_polarisations": 2, "gains": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]}'
            ),
        )
