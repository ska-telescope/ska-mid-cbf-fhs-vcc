from __future__ import annotations

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["FrequencySliceSelectionSimulator"]


class FrequencySliceSelectionSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "band_select": 1,
            "band_start_channel": [0, 1],
        }
