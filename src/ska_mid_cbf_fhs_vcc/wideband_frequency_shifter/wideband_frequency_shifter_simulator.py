from __future__ import annotations

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["WidebandFrequencyShifterSimulator"]


class WidebandFrequencyShifterSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "shift_frequency": 110.0,
        }
