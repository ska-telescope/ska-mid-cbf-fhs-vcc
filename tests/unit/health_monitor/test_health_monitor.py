

import asyncio
from dataclasses import dataclass
import logging
import time
from dataclasses_json import dataclass_json
import pytest
from ska_control_model import HealthState, ResultCode
from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.common.fhs_health_monitor import FhsHealthMonitor

@dataclass_json
@dataclass
class TestStatus:
    test_reg_1: int
    test_reg_2: int

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

    def _handle_register_errors(self, status_str:str) -> HealthState:
        
        status_obj:TestStatus = TestStatus.schema().loads(status_str)
        
        health_statuses = {}
                
        if status_obj.test_reg_1 != 123:
            print(f"register test_reg_1 has invalid value {status_obj.test_reg_1}")
            health_statuses['test_reg_1'] = HealthState.FAILED
        
        return health_statuses
    
    def get_health_state(self):
        return pytest.health_state

    def test_register_polling(self):
        pytest.health_state = HealthState.OK
        
        api = MockApi()
        
        hm: FhsHealthMonitor = FhsHealthMonitor(
                logger=logging.Logger('test'),
                api=api,
                get_device_health_state=self.get_health_state,
                update_health_state_callback=self._update_health_state,
                check_registers_callback=self._handle_register_errors
            )
        
        hm.start_polling()
        
        for i in range(10):
            time.sleep(1)
            if i == 5:
                api.updateRegSet('{"test_reg_1": 456, "test_reg_2": 345}')

                
        hm.stop_polling()
        
        assert(pytest.health_state is HealthState.FAILED)

        
    def test_add_failed_health_state(self):
        pytest.health_state = HealthState.OK
        api = MockApi()
        
        hm: FhsHealthMonitor = FhsHealthMonitor(
                logger=logging.Logger('test'),
                api=api,
                get_device_health_state=self.get_health_state,
                update_health_state_callback=self._update_health_state,
                check_registers_callback=self._handle_register_errors
            )
        
        hm.start_polling()
        
        for i in range(10):
            time.sleep(1)
            if i == 5:
                hm.add_health_state("UNKNOWN_EXCEPTION", HealthState.FAILED)
        
        hm.stop_polling()
        assert(pytest.health_state is HealthState.FAILED)
        