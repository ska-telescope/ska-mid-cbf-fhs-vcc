from __future__ import annotations
import logging  # allow forward references in type hints

from ska_control_model import HealthState, ObsState
from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface

import tango


__all__ = ["MacBaseSimulator"]


class MacBaseControllerSimulator(FhsBaseApiInterface):
    def __init__(self: MacBaseControllerSimulator, device_id: str) -> None:
        self.mac_id = device_id

        self.obs_state = ObsState.IDLE
        self._health_state = HealthState.UNKNOWN
        
    def recover(self) -> None:
        raise NotImplementedError('Method is abstract')
    
    def configure(self, config) -> None:
        raise NotImplementedError('Method is abstract')

    def start(self) -> int:
        raise NotImplementedError('Method is abstract')

    def stop(self, force: bool = False) -> int:
        raise NotImplementedError('Method is abstract')

    def deconfigure(self, config) -> None:
        raise NotImplementedError('Method is abstract')

    def status(self, status, clear: bool = False) -> str:
        raise NotImplementedError('Method is abstract')