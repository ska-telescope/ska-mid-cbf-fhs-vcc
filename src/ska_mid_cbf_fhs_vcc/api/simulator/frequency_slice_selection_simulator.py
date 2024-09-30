from __future__ import annotations

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["FrequencySliceSelectionSimulator"]


class FrequencySliceSelectionSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        return (
            ResultCode.OK,
            '{"num_inputs": 10, "num_outputs": 10, "connected": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]}',
        )
