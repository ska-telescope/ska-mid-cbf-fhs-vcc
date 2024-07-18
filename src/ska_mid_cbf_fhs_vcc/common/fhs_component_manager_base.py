from __future__ import annotations  # allow forward references in type hints


from threading import Lock
from typing import Any, Callable, Optional, cast
from ska_control_model import HealthState, SimulationMode
from ska_mid_cbf_fhs_vcc.common.fhs_state import FhsState
from ska_tango_base.executor.executor_component_manager import (
    TaskExecutorComponentManager,
)
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import ObsState

class FhsComponentManageBase(TaskExecutorComponentManager):
    
    
    @property
    def faulty(self: FhsComponentManageBase) -> Optional[bool]:
        """
        Return whether this component manager is currently experiencing a fault.

        :return: whether this component manager is currently
            experiencing a fault.
        """
        return cast(bool, self._component_state["fault"])
    
    
    def __init__(self: TaskExecutorComponentManager, 
                *args: Any, 
                attr_change_callback: Callable[[str, Any], None] | None = None,
                attr_archive_callback: Callable[[str, Any], None] | None = None,
                health_state_callback: Callable[[HealthState], None] | None = None,
                obs_command_running_callback: Callable[[str, bool], None],
                max_queue_size: int = 32, 
                simulation_mode: SimulationMode = SimulationMode.TRUE,
                emulation_mode: bool = False,
                **kwargs: Any) -> None:
        
        self.obs_state = ObsState.IDLE

        self._obs_command_running_callback = obs_command_running_callback
        self._attr_change_callback = attr_change_callback
        self._attr_archive_callback = attr_archive_callback
        self.simulation_mode = simulation_mode
        self.emulation_mode = emulation_mode
        
        self._device_health_state_callback = health_state_callback
        self._health_state_lock = Lock()
        self._health_state = HealthState.UNKNOWN

        super().__init__(*args, max_queue_size=max_queue_size, **kwargs)
        
        
    def update_device_health_state(
        self: FhsComponentManageBase,
        health_state: HealthState,
    ) -> None:
        """
        Handle a health state change.
        This is a helper method for use by subclasses.
        :param state: the new health state of the
            component manager.
        """
        with self._health_state_lock:
            if self._health_state != health_state:
                self._health_state = health_state
                if self._device_health_state_callback is not None:
                    self._device_health_state_callback(health_state)
                    
                    
    def _update_component_state(self: FhsComponentManageBase, fhsState: FhsState):
        
        self._component_state_callback(fhsState)
                    
                    
    def setFaultAndFailed(self: FhsComponentManageBase) -> None:
        """_summary_
        Set the component state to faulty and update its health to failed
        
        This is to be called when an exception occurs in the component manager
        """
        self._push_component_state_update(FhsState.FAULT)
        self.update_device_health_state(health_state=HealthState.FAILED)
                    

        
    ####
    # Allowance Functions
    ####

    def is_recover_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Recover is allowed.")
        errorMsg = f"Mac recover not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE or READY or ABORTED or RESETTING"
        return self.is_allowed(self, errorMsg, [ObsState.IDLE, ObsState.FAULT, ObsState.READY])


    def is_configure_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Configure is allowed.")
        errorMsg = f"Mac Configure not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE or READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE])
    
    
    def is_start_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Start is allowed.")
        errorMsg = f"Mac Start not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE or READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE])
    
    def is_stop_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Stop is allowed.")
        errorMsg = f"Mac stop not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE, READY or ABORTED"
                    
        return self.is_allowed(self, errorMsg, [ObsState.READY])
    
    def is_deconfigure_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Stop is allowed.")
        errorMsg = f"Mac deconfigure not allowed in ObsState {self.obs_state}; must be in ObsState.READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE])
    
    def is_status_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC status is allowed.")
        errorMsg = f"Mac status not allowed in ObsState {self.obs_state}; must be in ObsState.READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE, ObsState.READY, ObsState.FAULT])
    
    def is_reset_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC status is allowed.")
        errorMsg = f"Mac reset not allowed in ObsState {self.obs_state}; must be in ObsState.FAULT"
                    
        return self.is_allowed(self, errorMsg, [ObsState.FAULT])
    
    
    def is_allowed(self: FhsComponentManageBase, error_msg: str, obsStates: list[ObsState]) -> bool:       
        result = True
        
        if self.obs_state not in obsStates:
            self.logger.warning(
                error_msg
            )
            result = False
        return result
    
    ###
    # Command functions
    ###
    
    def _obs_command_with_callback(
        self: FhsComponentManageBase,
        *args,
        command_thread: Callable[[Any], None],
        hook: str,
        **kwargs,
    ):
        """
        Wrap command thread with ObsStateModel-driving callbacks.

        :param command_thread: actual command thread to be executed
        :param hook: hook for state machine action
        """
        self._obs_command_running_callback(hook=hook, running=True)
        command_thread(*args, **kwargs)
        return self._obs_command_running_callback(hook=hook, running=False)
    
    