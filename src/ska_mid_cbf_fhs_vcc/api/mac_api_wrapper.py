
from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_vcc.api.common.interfaces.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.api.emulator.mac_emulator_api import MacEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.mac_base_controller_simulator import MacBaseControllerSimulator

class MacApi(FhsBaseApiInterface):
    def __init__(self, instance_name: str, simulation_mode: SimulationMode, emulation_mode: bool) -> None:
        if(simulation_mode == SimulationMode.TRUE):
            self._mac_api = MacBaseControllerSimulator(instance_name)
        elif (simulation_mode == SimulationMode.FALSE and emulation_mode == True):
            self._mac_api = MacEmulatorApi(instance_name) 
        else:
            # TODO todo add FW API here no
            raise NotImplemented('FW Api not implemented')
        
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