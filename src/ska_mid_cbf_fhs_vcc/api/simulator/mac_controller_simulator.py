from __future__ import annotations

import logging

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["MacBaseControllerSimulator"]


class MacBaseControllerSimulator(BaseSimulatorApi):
    def __init__(self: MacBaseControllerSimulator, device_id: str, logger: logging.Logger) -> None:
        super().__init__(device_id=device_id, logger=logger)
