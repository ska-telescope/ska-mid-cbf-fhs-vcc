
from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.api.emulator.mac_emulator_api import MacEmulatorApi

class MacApi(FhsBaseApiInterface):
    def __init__(self, instance_name: str) -> None:
        self._mac_api = MacEmulatorApi(instance_name) #TODO add the FW api instantiation here once made
        
    def recover(self) -> None:
        self._mac_api.recover()
        
    def configure(self, config) -> int:
        self._mac_api.configure(config)
        
    def start(self) -> int:
        return self._mac_api.start()
        
    def stop(self, force: bool = False) -> None:
        return self._mac_api.stop(force)
    
    def deconfigure(self, config) -> None:
        return self._mac_api().deconfigure(config)
    
    def status(self, status, clear: bool = False) -> str:
        raise self._mac_api.status(status, clear);