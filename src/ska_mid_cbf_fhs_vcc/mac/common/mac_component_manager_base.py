from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
import functools
from typing import Any

import numpy as np

from typing import Any, Callable, Optional

from ska_mid_cbf_fhs_vcc.common.fhs_component_manager_base import FhsComponentManageBase
from ska_control_model import (
    CommunicationStatus,
    HealthState,
    ResultCode,
    SimulationMode,
    TaskStatus
)


from ska_mid_cbf_fhs_vcc.api.mac_api_wrapper import MacApi
import tango

@dataclass
class MacConfig:
    rx_loopback_enable: bool


##
# status class that will be populated by the APIs and returned to provide the status of Mac
##
@dataclass
class MacStatus:
    class phy:
        rx_loopback: bool = False
        rx_freq_lock = []
        rx_word_lock = []
    class fec:
        rx_corrected_code_words: np.uint32
        rx_uncorrected_code_words: np.uint32
    class mac:
        rx_fragments: np.uint32
        rx_runt: np.uint32
        rx_64_bytes: np.uint32
        rx_65_to_127_bytes: np.uint32
        rx_128_to_255_bytes: np.uint32
        rx_256_to_511_bytes : np.uint32
        rx_512_to_1023_bytes : np.uint32
        rx_1024_to_1518_bytes : np.uint32
        rx_1519_to_max_bytes : np.uint32
        rx_oversize : np.uint32
        rx_frame_octets_ok : np.uint32
        rx_crcerr : np.uint32
        tx_fragments: np.uint32
        tx_runt : np.uint32
        tx_64_bytes: np.uint32
        tx_65_to_127_bytes: np.uint32
        tx_128_to_255_bytes: np.uint32
        tx_256_to_511_bytes : np.uint32
        tx_512_to_1023_bytes: np.uint32
        tx_1024_to_1518_bytes: np.uint32
        tx_1519_to_max_bytes: np.uint32
        tx_oversize : np.uint32
        tx_frame_octets_ok : np.uint32
        tx_crcerr : np.uint32


class MacComponentManagerBase(FhsComponentManageBase):

    
    def __init__(
        self: MacComponentManagerBase, 
        *args: Any, 
        mac_id: str,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        **kwargs: Any
    ) -> None:
        
        self._mac_id = mac_id
        
        self.simulation_mode = simulation_mode
        self.emulation_mode = emulation_mode
        
        #TODO add way to get host / port info
        self._mac_api = MacApi(instance_name=mac_id, simulation_mode=simulation_mode, emulation_mode=emulation_mode)
        
        super().__init__(*args, **kwargs)
        
    ##
    # Public Commands
    ##
        
    # TODO Determine what needs to be communicated with here
    def start_communicating(self: MacComponentManagerBase) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return
        # try:
        #     pass
        #     # self._talon_lru_proxy = context.DeviceProxy(
        #     #     # Unsure what im connecting to here? 
        #     # )
        # except tango.DevFailed:
        #     self._update_communication_state(
        #         communication_state=CommunicationStatus.NOT_ESTABLISHED
        #     )
        #     self.logger.error(
        #         f"Error in Mac {self._mac_id} proxy connection"
        #     )
        #     return

        super().start_communicating()
        # self._update_component_state(power=self._get_power_state())
        


    #####
    # Command Functions
    #####
    
    def test_cmd(
        self: MacComponentManagerBase,
        task_callback: Optional[Callable] = None
    ) -> tuple[TaskStatus, str]:
        return [TaskStatus.COMPLETED, 'Test Complete']
    
    def recover(
        self: MacComponentManagerBase,
        argin: str,
        task_callback: Optional[Callable] = None
    ) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.component_state}")
        return self.submit_task(
            self._recover,
            args=[argin],
            is_cmd_allowed=self.is_recover_allowed,
            task_callback=task_callback
        )
    
    def configure(
        self: MacComponentManagerBase,
        argin: str,
        task_callback: Optional[Callable] = None
    ) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.component_state}")
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="configure",
                command_thread=self._configure,
            ),
            args=[argin, False],
            is_cmd_allowed=self.is_configure_allowed,
            task_callback=task_callback
        )
        
    def start(
        self: MacComponentManagerBase,
        task_callback: Optional[Callable] = None
    ) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.communication_state}")
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="starting",
                command_thread=self._start,
            ),
            is_cmd_allowed = self.is_start_allowed,
            task_callback=task_callback
        )
    
    def stop(
        self: MacComponentManagerBase,
        force: bool,
        task_callback: Optional[Callable] = None
    ) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.communication_state}")
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="stopping",
                command_thread=self._stop,
            ),
            is_cmd_allowed = self.is_stop_allowed,
            task_callback=task_callback
        )

    def deconfigure(
        self: MacComponentManagerBase,
        argin: str,
        task_callback: Optional[Callable] = None
    ) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.component_state}")
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="deconfigure",
                command_thread=self._configure,
            ),
            args=[argin, True],
            is_cmd_allowed=self.is_deconfigure_allowed,
            task_callback=task_callback
        )

    def status(
        self: MacComponentManagerBase,
        argin: str,
        clear: bool = False,
        task_callback: Optional[Callable] = None 
    ) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.communication_state}")
        return self.submit_task(
            self._status,
            args=[argin, clear],
            is_cmd_allowed = self.is_status_allowed,
            task_callback=task_callback
        )

    ###
    #  Private Commands
    ###
    
    def _testCmd(        
        self: MacComponentManagerBase,
        task_callback: Optional[Callable] = None) -> None:
        # Assume configure fails at the start
        resultCode = ResultCode.FAILED
        taskStatus = TaskStatus.FAILED
        
        try:
            resultCode = (ResultCode.OK, "Configure Mac completed OK")
            taskStatus = TaskStatus.COMPLETED
        except Exception as ex:
            resultCode = (ResultCode.FAILED, f"Unable to recover mac: {str(ex)}")
            self.setFaultAndFailed()
        
        task_callback(
            result = resultCode,
            status=taskStatus,
        )
        return
    
    def _recover(
        self: MacComponentManagerBase,
        argin: str,
        task_callback: Optional[Callable] = None,
    ) -> None:
        # Assume configure fails at the start
        resultCode = ResultCode.FAILED
        taskStatus = TaskStatus.FAILED
        
        try:
            self._component_state()
            self._mac_api.recover()
        except Exception as ex:
            resultCode = (ResultCode.FAILED, f"Unable to recover mac: {str(ex)}")
            self.setFaultAndFailed()
            
        task_callback(
            result = resultCode,
            status=taskStatus,
        )
        return
    
    def _configure(
        self: MacComponentManagerBase,
        argin: str,
        deconfigure: bool = False,
        task_callback: Optional[Callable] = None,
    ) -> None:

        # Assume configure fails at the start
        resultCode = ResultCode.FAILED
        taskStatus = TaskStatus.FAILED

        task_callback(status=TaskStatus.IN_PROGRESS)
        
        try:
            #TODO add schema validation
            configuration = MacConfig(argin)
            if not deconfigure:
                self._mac_api.configure(configuration)
                resultCode = (ResultCode.OK, "Configure Mac completed OK")
            else:
                self._mac_api.deconfigure(configuration)
                resultCode = (ResultCode.OK, "Deconfigure Mac completed OK")
            
            # set the result code and status to OK / Completed on successful configuration
            taskStatus = TaskStatus.COMPLETED
        except Exception as ex:
            resultCode = (ResultCode.FAILED, f"Unable to configure mac: {str(ex)}")
            self.setFaultAndFailed()
            
        task_callback(
            result = resultCode,
            status=taskStatus,
        )
        return
    
    def _start(
        self: MacComponentManagerBase,
        task_callback: Optional[Callable] = None,
    ) -> None:
        # Assume configure fails at the start
        resultCode = ResultCode.FAILED
        taskStatus = TaskStatus.FAILED
        
        try:
            self._mac_api.start()
            resultCode = (ResultCode.OK, "Start Mac completed OK")
        except Exception as ex:
            resultCode = (ResultCode.FAILED, f"Unable to start mac: {str(ex)}")
            self.setFaultAndFailed()
        
        task_callback(
            result = resultCode,
            status=taskStatus,
        )
        return
    
    def _stop(
        self: MacComponentManagerBase,
        force: bool,
        task_callback: Optional[Callable] = None,
    ) -> None:
        # Assume configure fails at the start
        resultCode = ResultCode.FAILED
        taskStatus = TaskStatus.FAILED
        
        try:
            self._mac_api.stop(force)
            resultCode = (ResultCode.OK, "Stop Mac completed OK")
        except Exception as ex:
            resultCode = (ResultCode.FAILED, f"Unable to stop mac: {str(ex)}")
            self.setFaultAndFailed()
        
        task_callback(
            result = resultCode,
            status=taskStatus,
        )
        return
    
    def _status(
        self: MacComponentManagerBase,
        clear: bool = False,
        task_callback: Optional[Callable] = None,
    ) -> None:
        # Assume configure fails at the start
        resultCode = ResultCode.FAILED
        taskStatus = TaskStatus.FAILED
        
        try:
            status = MacStatus()
            resultStr = self._mac_api.status(status, clear)
            resultCode = (ResultCode.OK, f"Start Mac completed OK\nStatus : \n{resultStr}")

        except Exception as ex:
            resultCode = (ResultCode.FAILED, f"Unable to get status fo mac: {str(ex)}")
            self.setFaultAndFailed()
        
        task_callback(
            result = resultCode,
            status=taskStatus,
        )
        return
