from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import enum
from typing import Any, Callable, Optional, cast

import numpy as np
import tango
from ska_control_model import ObsState, SimulationMode
from ska_tango_base.base.base_component_manager import BaseComponentManager
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import FastCommand, SubmittedSlowCommand
from ska_tango_base.obs.obs_device import SKAObsDevice
from tango.server import attribute, command, device_property
from transitions import Machine
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine, FhsObsStateModel


class FhsBaseDevice(ABC, SKAObsDevice):
    
    PacketValidationFqdn = device_property(dtype="str")

    def _init_state_model(self: FhsBaseDevice) -> None:
        """Set up the state model for the device."""
        super()._init_state_model()

        # supplying the reduced observing state machine defined above
        self.obs_state_model = FhsObsStateModel(
            logger=self.logger,
            callback=self._update_obs_state,
            state_machine_factory=FhsObsStateMachine,
        )
        

    def init_command_objects(self: FhsBaseDevice) -> None:
        """Set up the command objects."""
        super().init_command_objects()

        for command_name, method_name in [
            ("Recover", "recover"),
            ("Configure", "configure"),
            ("Start", "start"),
            ("Stop", "stop"),
            ("Deconfigure", "configure"),
            ("Status", "status"),
        ]:
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
        self.obs_state_model.perform_action(f"{hook}_{action}")

    
    def _component_state_changed(
        self: FhsBaseDevice,
        fault: Optional[bool] = None,
        configured: Optional[bool] = None
    ) -> None:

        if fault is not None:
            if fault:
                self.obs_state_model.perform_action("component_obsfault")
            # NOTE: to recover from obsfault, ObsReset or Restart must be invoked
            
            
    def _update_obs_state(self: FhsBaseDevice, obs_state: ObsState) -> None:
        """
        Perform Tango operations in response to a change in obsState.

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
