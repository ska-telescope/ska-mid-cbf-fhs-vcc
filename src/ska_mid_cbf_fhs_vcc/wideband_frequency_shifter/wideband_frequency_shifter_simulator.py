from __future__ import annotations
import json

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["WidebandFrequencyShifterSimulator"]


class WidebandFrequencyShifterSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads('{"shift_frequency": 110.0}')
