from __future__ import annotations
import logging  # allow forward references in type hints

from ska_control_model import HealthState, ObsState
from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface

import tango


__all__ = ["MacBaseSimulator"]


class MacBaseControllerSimulator(FhsBaseApiInterface):
    def __init__(self: MacBaseControllerSimulator, device_id: str) -> None:
        self.mac_id = device_id
        
    def recover(self) -> None:
        print('Recover called from the simulator')
    
    def configure(self, config) -> None:
        print('Configure was called from the simulator')
        
    def start(self) -> int:
        print('Start was called from the simulator')

    def stop(self, force: bool = False) -> int:
        print('Stop was called from the simulator')

    def deconfigure(self, config) -> None:
        print('Deconfigure was called from the simulator')

        
    def status(self, status, clear: bool = False) -> str:
        print('Status was called from the simulator')
        return 'status okay'
