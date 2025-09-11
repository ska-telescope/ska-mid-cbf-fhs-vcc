from __future__ import annotations

import json

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["FrequencySliceSelectionSimulator"]


class FrequencySliceSelectionSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads('{"band_select": 1, "band_start_channel": [0, 1]}')
