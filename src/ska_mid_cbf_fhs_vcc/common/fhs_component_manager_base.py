from __future__ import annotations  # allow forward references in type hints


from typing import Any, Callable, Optional
from ska_control_model import HealthState
from ska_tango_base.executor.executor_component_manager import (
    TaskExecutorComponentManager,
)
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import ObsState

class FhsComponentManageBase(TaskExecutorComponentManager):
    def __init__(self: TaskExecutorComponentManager, 
                *args: Any, 
                name: str,
                attr_change_callback: Callable[[str, Any], None] | None = None,
                attr_archive_callback: Callable[[str, Any], None] | None = None,
                health_state_callback: Callable[[HealthState], None] | None = None,
                obs_command_running_callback: Callable[[str, bool], None],
                max_queue_size: int = 32, 
                **kwargs: Any) -> None:
        
        self._name = name

        self._component_state = {
            "starting": None,
            "stopping": None,
            "configured": None,
            "reset": None,
            "fault": None,
        }
        
        self.obs_state = ObsState.IDLE
        
        self._health_state = HealthState.UNKNOWN

        self.health_state_callback = health_state_callback
        self._obs_command_running_callback = obs_command_running_callback
        self._attr_change_callback = attr_change_callback
        self._attr_archive_callback = attr_archive_callback

        super().__init__(*args, max_queue_size=max_queue_size, **kwargs)
        
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
    
    