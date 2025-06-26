from __future__ import annotations

import json

from ska_control_model import ResultCode
from ska_mid_cbf_fhs_common.base_classes.api.base_simulator_api import BaseSimulatorApi

__all__ = ["WidebandPowerMeterSimulator"]


class WidebandPowerMeterSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> tuple[ResultCode, dict]:
        return (
            ResultCode.OK,
            json.loads(
                """
                {
                    "timestamp": 0.0,
                    "avg_power_polX": 0.0,
                    "avg_power_polY": 0.0,
                    "avg_power_polX_noise_diode_on": 0.0,
                    "avg_power_polY_noise_diode_on": 0.0,
                    "avg_power_polX_noise_diode_off": 0.0,
                    "abg_power_polY_noise_diode_off": 0.0,
                    "flag": 0,
                    "overflow": 0
                }
                """
            ),
        )
