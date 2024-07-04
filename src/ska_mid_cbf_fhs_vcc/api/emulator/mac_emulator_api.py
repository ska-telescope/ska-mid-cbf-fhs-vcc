import requests

from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.mac.common.mac_component_manager_base import MacStatus, MacConfig

class MacEmulatorApi(FhsBaseApiInterface):
    
    # TODO have a way to dynamically grab the emulator host / port values from the emulator config file
    def __init__(self, instance_name: str, hostName: str = "localhost", port: str = "5001") -> None:
        self._instance_name = instance_name
        self.base_url = f"{hostName}:{port}/{instance_name}"

        
    def recover(self) -> None:
        response = requests.post(f'{self.base_url}/recover')
    
    def configure(self, config: str) -> None:
        response = requests.post(f'{self.base_url}/configure', json=config)
    
    def start(self) -> int:
        response = requests.get(f'{self.base_url}/start')
    
    def stop(self, force: bool = False) -> int:
        response = requests.get(f'{self.base_url}/stop')
    
    def deconfigure(self, config: str) -> None:
        response = requests.post(f'{self.base_url}/deconfigure', json=config)
    
    def status(self, status: MacStatus, clear: bool = False) -> None:
        response = requests.get(f'{self.base_url}/status/clear={clear}')
    
    