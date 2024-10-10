from __future__ import annotations

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["FrequencySliceSelectionSimulator"]


class FrequencySliceSelectionSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        return (
            ResultCode.OK,
            '{"band_select": 1, "band_start_channel": [0, 1]}',
        )
