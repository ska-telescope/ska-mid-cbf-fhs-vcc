from __future__ import annotations

import json
import threading
import time
from typing import Callable
from ska_control_model import HealthState, ResultCode
from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface

class FhsLowLevelHealthMonitor(threading.Thread):
    def __init__(self: FhsLowLevelHealthMonitor, 
                 api: FhsBaseApiInterface, 
                 status_func: str, 
                 registers_to_check: str,
                 update_health_state_callback: Callable, 
                 check_registers_callback: Callable, 
                 poll_interval=1.0
                ):
        super().__init__()
        self.api = api
        self.status_func = status_func
        self.registers_to_check = registers_to_check
        self.update_health_state_callback = update_health_state_callback
        self.check_registers_callback = check_registers_callback
        self.poll_interval= poll_interval
        self.daemon = True
        self._stop_event = threading.Event()
        self._running = False
        self._register_statuses = {key: HealthState.UNKNOWN for key in registers_to_check}
        self._last_health_state = HealthState.UNKNOWN
        self._health_states = HealthState.__reversed__() # reverse the list so we start checking from worst case
    
    def run(self: FhsLowLevelHealthMonitor):
        if not self._running:
            while not self._stop_event.is_set():
                try:
                    time.sleep(self.poll_interval)
                    status_func = getattr(self.api, self.status_func)
                    status: tuple[ResultCode, str] = status_func()
                    statusJson = json.loads(status[1])
                    
                    for register in self.registers_to_check:
                        if register in statusJson:
                            value = statusJson[register]
                            health_state: HealthState = self.check_registers_callback(register, value)
                            
                            self._register_statuses[register] = health_state
                        else: 
                            print(f"WARN - Register {register} not found in received status dictionary")
                            
                    self._determine_health_state()
                                            
                except Exception as ex:
                    self.update_health_state_callback(HealthState.UNKNOWN)
                    self.stop()
                    print(f"Error - Unable to monitor health. {repr(ex)}")
        else:
            print("LowLevelHealthMonitor is already running")
            
    def stop(self):
        self._stop_event.set()
        
    def _determine_health_state(self):
        for health_state in self._health_states:
            if health_state in self._register_statuses.values():
                if health_state is not self._last_health_state:
                    print(f"{health_state.real}")
                    self._last_health_state = health_state
                    self.update_health_state_callback(health_state)
                break;