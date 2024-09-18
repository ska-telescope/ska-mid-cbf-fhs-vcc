from __future__ import annotations

import logging

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["WidebandFrequencyShifterSimulator"]


class WidebandFrequencyShifterSimulator(BaseSimulatorApi):
    def __init__(
        self: WidebandFrequencyShifterSimulator, device_id: str, logger: logging.Logger
    ) -> None:
        super().__init__(device_id=device_id, logger=logger)
