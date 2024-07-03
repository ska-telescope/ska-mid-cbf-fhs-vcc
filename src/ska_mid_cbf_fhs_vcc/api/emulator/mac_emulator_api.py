import requests

from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.mac.common.mac_component_manager_base import MacStatus, MacConfig

class MacEmulatorApi(FhsBaseApiInterface):
    
    # TODO have a way to dynamically grab the emulator host / port values from the emulator config file
    def __init__(self, instance_name: str, hostName: str = "localhost", port: str = "8000") -> None:
        self.address = f"{hostName}:{port}"
        self._instance_name = instance_name
        
    def recover(self) -> None:
        return super().recover()
    
    def configure(self, config: MacConfig) -> None:
        return super().configure(config)
    
    def start(self) -> int:
        return 0
    
    def stop(self, force: bool = False) -> int:
        return 0
    
    def deconfigure(self, config) -> None:
        return super().deconfigure(config)
    
    def status(self, status: MacStatus, clear: bool = False) -> None:
        return super().status(status, clear)
    
    