from __future__ import annotations

import json

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["B123VccOsppfbChannelizerSimulator"]


class B123VccOsppfbChannelizerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            '{"sample_rate": 3960000000, "num_channels": 10, "num_polarisations": 2, "gains": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]}'
        )
