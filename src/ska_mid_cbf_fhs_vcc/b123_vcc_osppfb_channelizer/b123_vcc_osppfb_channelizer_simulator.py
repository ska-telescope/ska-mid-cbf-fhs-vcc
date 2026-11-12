from __future__ import annotations

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["B123VccOsppfbChannelizerSimulator"]


class B123VccOsppfbChannelizerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "sample_rate": 3960000000,
            "num_channels": 10,
            "num_polarisations": 2,
            "gains": [{"pol": j, "channel": i, "gain": 1.0} for j in range(2) for i in range(10)],
        }
