

import asyncio
import time
import pytest
from ska_control_model import HealthState, ResultCode
from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_health_monitor import FhsLowLevelHealthMonitor

class MockApi(FhsBaseApiInterface):
    def __init__(self) -> None:
        self.regSet = '{"test_reg_1": 123, "test_reg_2": 345}'

    def recover(self) -> tuple[ResultCode, str]:
        raise NotImplementedError()

    def configure(self, config: dict = None) -> tuple[ResultCode, str]:
        raise NotImplementedError()

    def start(self) -> tuple[ResultCode, str]:
        raise NotImplementedError()

    def stop(self, force: bool = False) -> tuple[ResultCode, str]:
        raise NotImplementedError()

    def deconfigure(self, config: dict) -> tuple[ResultCode, str]:
        raise NotImplementedError()

    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        return ResultCode.OK, self.regSet
    
    def updateRegSet(self, regSet: str):
        self.regSet = regSet


class TestFhsLowLevelHealthMonitor():
    
    pytest.health_state = HealthState.OK    
    
    def _update_health_state(self, updatedHealthState: HealthState):
        print("Updated health state")
        pytest.health_state = updatedHealthState

    def _handle_register_errors(self, register, value) -> HealthState:
        if register == 'test_reg_1' and value != 123:
            print(f"register {register} has invalid value {value}")
            return HealthState.FAILED
        
        return HealthState.OK

    def test_register_polling(self):
        
        register_to_check = ["test_reg_1", "test_reg_2"]
        
        api = MockApi()
        
        hm: FhsLowLevelHealthMonitor = FhsLowLevelHealthMonitor(
                api, 
                "status", 
                register_to_check, 
                self._update_health_state, 
                self._handle_register_errors, 
                1.0
            )
        
        hm.start()
        
        for i in range(10):
            time.sleep(1)
            if i == 5:
                api.updateRegSet('{"test_reg_1": 456, "test_reg_2": 345}')

        
        assert(pytest.health_state is HealthState.FAILED)
        
        hm.stop()
