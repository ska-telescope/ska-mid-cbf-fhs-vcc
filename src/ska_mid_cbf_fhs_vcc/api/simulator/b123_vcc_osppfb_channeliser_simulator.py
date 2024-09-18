from __future__ import annotations

import logging

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["B123VccOsppfbChanneliserSimulator"]


class B123VccOsppfbChanneliserSimulator(BaseSimulatorApi):
    def __init__(
        self: B123VccOsppfbChanneliserSimulator, device_id: str, logger: logging.Logger
    ) -> None:
        super().__init__(device_id=device_id, logger=logger)
