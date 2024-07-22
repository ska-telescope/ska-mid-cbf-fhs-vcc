from __future__ import annotations

from typing import Any, Optional, cast

import numpy as np
from ska_control_model import ObsState, PowerState, ResultCode, SimulationMode
from ska_tango_base import SKABaseDevice
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import SubmittedSlowCommand
from ska_tango_base.obs.obs_device import SKAObsDevice
from tango.server import attribute, command, device_property
from tango import DevState
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine, FhsObsStateModel
from ska_control_model import OpStateModel


class FhsBaseDevice(SKAObsDevice):
    
    # -----------------
    # Device Properties
    # -----------------
    device_id = device_property(dtype="str")
    device_version_num = device_property(dtype="str")
    device_gitlab_hash = device_property(dtype="str")
   
    
    @attribute(dtype=SimulationMode, memorized=True, hw_memorized=True)
    def simulationMode(self: FhsBaseDevice) -> SimulationMode:
        """
        Read the Simulation Mode of the device.

        :return: Simulation Mode of the device.
        """
        return self._simulation_mode


    @simulationMode.write
    def simulationMode(self: FhsBaseDevice, value: SimulationMode) -> None:
        """
        Set the simulation mode of the device.

        :param value: SimulationMode
        """
        self.logger.debug(f"Writing simulationMode to {value}")
        self._simulation_mode = value
        self.component_manager.simulation_mode = value
    
        
    @attribute(dtype=bool, memorized=True, hw_memorized=True)
    def emulationMode(self: FhsBaseDevice) -> bool:
        """
        Read the Simulation Mode of the device.

        :return: Simulation Mode of the device.
        """
        return self._emulation_mode


    @simulationMode.write
    def emulationMode(self: FhsBaseDevice, value: bool) -> None:
        """
        Set the simulation mode of the device.

        :param value: SimulationMode
        """
        self.logger.debug(f"Writing simulationMode to {value}")
        self._simulation_mode = value
        self.component_manager.emulation_mode = value
    
    
    def _init_state_model(self: FhsBaseDevice) -> None:
        """Set up the state model for the device."""
        super()._init_state_model()

        # supplying the reduced observing state machine defined above
        self.obs_state_model = FhsObsStateModel(
            logger=self.logger,
            callback=self._update_obs_state,
            state_machine_factory=FhsObsStateMachine,
        )
        

    def init_command_objects(self: FhsBaseDevice, commandsAndMethods: list[tuple]) -> None:
        """Set up the command objects."""
        super().init_command_objects()

        for command_name, method_name in commandsAndMethods:
            self.register_command_object(
                command_name,
                SubmittedSlowCommand(
                    command_name=command_name,
                    command_tracker=self._command_tracker,
                    component_manager=self.component_manager,
                    method_name=method_name,
                    logger=self.logger,
                ),
            )
            
    def reset_obs_state(self: FhsBaseDevice):
        if(self._obs_state in [ObsState.FAULT, ObsState.ABORTED]):
            self.obs_state_model.perform_action(FhsObsStateMachine.GO_TO_IDLE)

    def _obs_command_running(
        self: FhsBaseDevice, hook: str, running: bool
    ) -> None:
        """
        Callback provided to component manager to drive the obs state model into
        transitioning states during the relevant command's submitted thread.

        :param hook: the observing command-specific hook
        :param running: True when thread begins, False when thread completes
        """
        action = "invoked" if running else "completed"
        self.logger.log(f"Changing ObsState from running command, calling: {hook}_{action} ")
        self.obs_state_model.perform_action(f"{hook}_{action}")

    def _component_state_changed(self: FhsBaseDevice, 
                                 idle: bool | None = None, 
                                 configuring: bool | None = None,
                                 configured: bool | None = None,
                                 deconfiguring: bool | None = None,
                                 deconfigured: bool | None = None,
                                 starting: bool | None = None,
                                 running: bool | None = None,
                                 stopping: bool | None = None,
                                 stopped: bool | None = None,
                                 resetting: bool | None = None,
                                 reset: bool | None = None,
                                 fault: bool | None = None) -> None:
        
        if(idle is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.GO_TO_IDLE)
        
        if(configuring is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.CONFIGURE_INVOKED)
            
        if(configured is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.CONFIGURE_COMPLETED)
            
        if(deconfiguring is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.DECONFIGURE_INVOKED)
            
        if(deconfigured is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.DECONFIGURE_COMPLETED)
        
        if(starting is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.STARTING_INVOKED) 
        
        if(running is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.STARTING_COMPLETED)
            
        if(stopping is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.STOPPING_INVOKED)
            
        if(stopped is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.STOPPING_COMPLETED)
            
        if(resetting is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.RESET_INVOKED)
            
        if(reset is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.RESET_COMPLETED)

        if(fault is not None):
            self.obs_state_model.perform_action(FhsObsStateMachine.COMPONENT_OBSFAULT)
    
            
    def _update_obs_state(self: FhsBaseDevice, obs_state: ObsState) -> None:
        """
        Perform Tango operations in response to a change in obsState within the state machine.

        This helper method is passed to the observation state model as a
        callback, so that the model can trigger actions in the Tango
        device.

        Overridden here to supply new ObsState value to component manager property

        :param obs_state: the new obs_state value
        """
        self.logger.debug(f"ObsState updating to {ObsState(obs_state).name}")
        
        super()._update_obs_state(obs_state=obs_state)
        
        # set the obstate in the component_manager
        if hasattr(self, "component_manager"):
            self.component_manager.obs_state = obs_state
        

    class InitCommand(SKAObsDevice.InitCommand):
        # pylint: disable=protected-access  # command classes are friend classes
        """A class for the CbfObsDevice's init_device() "command"."""

        def do(
            self: FhsBaseDevice.InitCommand,
            *args: Any,
            **kwargs: Any,
        ) -> tuple[ResultCode, str]:
            """
            Stateless hook for device initialisation.

            :param args: positional arguments to this do method
            :param kwargs: keyword arguments to this do method

            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            """
            (result_code, msg) = super().do(*args, **kwargs)

            self._device._obs_state = ObsState.IDLE
            

            self._device._op_state = DevState.INIT

            return (result_code, msg)

            
# ----------
# Run server
# ----------


def main(*args: str, **kwargs: str) -> int:
    """
    Entry point for module.

    :param args: positional arguments
    :param kwargs: named arguments

    :return: exit code
    """
    return cast(int, FhsBaseDevice.run_server(args=args or None, **kwargs))


if __name__ == "__main__":
    main()
