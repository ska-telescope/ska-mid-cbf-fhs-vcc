from __future__ import annotations  # allow forward references in type hints


from typing import Any, Callable
from ska_control_model import HealthState, ObsState
from ska_tango_base.executor.executor_component_manager import (
    TaskExecutorComponentManager,
)

class FhsComponentManageBase(TaskExecutorComponentManager):
    def __init__(self: TaskExecutorComponentManager, 
                *args: Any, 
                name: str,
                attr_change_callback: Callable[[str, Any], None] | None = None,
                attr_archive_callback: Callable[[str, Any], None] | None = None,
                health_state_callback: Callable[[HealthState], None] | None = None,
                max_queue_size: int = 32, 
                **kwargs: Any) -> None:
        
        self._name = name

        self._component_state = {
            "configured": None,
            "reset": None,
            "fault": None,
            "init": None,
            "standby": None,
        }
        
        self._health_state = HealthState.UNKNOWN

        self.health_state_callback = health_state_callback

        super().__init__(*args, max_queue_size=max_queue_size, **kwargs)
        
    ####
    # Allowance Functions
    ####

    def is_recover_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Recover     is allowed.")
        errorMsg = f"Mac recover not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE or READY or ABORTED or RESETTING"
        return self.is_allowed(self, errorMsg, [ObsState.IDLE, ObsState.READY, ObsState.ABORTED, ObsState.RESETTING])


    def is_configure_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Configure is allowed.")
        errorMsg = f"Mac Configure not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE or READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE, ObsState.READY])
    
    
    def is_start_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Start is allowed.")
        errorMsg = f"Mac Start not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE or READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE, ObsState.READY])
    
    def is_stop_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Stop is allowed.")
        errorMsg = f"Mac stop not allowed in ObsState {self.obs_state}; must be in ObsState.IDLE, READY or ABORTED"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE, ObsState.READY, ObsState.ABORTED])
    
    def is_deconfigure_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC Stop is allowed.")
        errorMsg = f"Mac deconfigure not allowed in ObsState {self.obs_state}; must be in ObsState.READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.READY])
    
    def is_status_allowed(self: FhsComponentManageBase) -> bool:
        self.logger.debug("Checking if MAC status is allowed.")
        errorMsg = f"Mac StaStoprt not allowed in ObsState {self.obs_state}; must be in ObsState.READY"
                    
        return self.is_allowed(self, errorMsg, [ObsState.IDLE, ObsState.READY])
    
    
    def is_allowed(self: FhsComponentManageBase, error_msg: str, obsStates: list[ObsState]) -> bool:       
        result = True
        
        if self.obs_state not in obsStates:
            self.logger.warning(
                error_msg
            )
            result = False
        return result
    
    