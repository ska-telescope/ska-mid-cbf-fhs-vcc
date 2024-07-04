from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional, cast

import numpy as np
import tango
from ska_control_model import SimulationMode
from ska_tango_base.base.base_component_manager import BaseComponentManager
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import FastCommand, SubmittedSlowCommand
from ska_tango_base.obs.obs_device import SKAObsDevice
from tango.server import attribute, command, device_property
from transitions import Machine


class CbfSubElementObsStateMachine(Machine):
    """
    The observation state machine used by a generic FHS base class sub-element ObsDevice.

    NOTE: entirely taken from ska-mid-cbd-mcs which in turn was taken from ska-csp-lmc-base CspSubElementObsStateMachine,
    to decouple FSH-VCC from their ska-tango-base version dependency

    """

    def __init__(
        self, callback: Optional[Callable] = None, **extra_kwargs: Any
    ) -> None:
        """
        Initialise the model.

        :param callback: A callback to be called when the state changes
        :param extra_kwargs: Additional keywords arguments to pass to super class
            initialiser (useful for graphing)
        """
        self._callback = callback

        states = [
            "IDLE",
            "CONFIGURING",  # device CONFIGURING but component is unconfigured
            "DECONFIGURING",  # device CONFIGURING but component is unconfigured
            "STARTING",
            "ACCEPTING_DATA",
            "STOPPING",
            "RESETTING",
            "RESET",
            "FAULT",
        ]
        transitions = [
            {
                "source": "*",
                "trigger": "component_obsfault",
                "dest": "FAULT",
            },
            {
                "source": "IDLE",
                "trigger": "configure_invoked",
                "dest": "CONFIGURING",
            },                
            {
                "source": "IDLE",
                "trigger": "unconfigure_invoked",
                "dest": "UNCONFIGURING",
            },
            {
                "source": "CONFIGURING",
                "trigger": "configure_completed",
                "dest": "IDLE",
            },
            {
                "source": "UNCONFIGURING",
                "trigger": "unconfigure_completed",
                "dest": "IDLE",
            },
            {
                "source": "IDLE",
                "trigger": "starting_invoked",
                "dest": "STARTING",
            },
            {
                "source": "STARTING",
                "trigger": "starting_invoked",
                "dest": "ACCEPTING_DATA",
            },
            {
                "source": "ACCEPTING_DATA",
                "trigger": "stopping_invoked",
                "dest": "STOPPING",
            },
            {
                "source": "STOPPING",
                "trigger": "stopping_invoked",
                "dest": "IDLE",
            }
        ]
        super().__init__(
            states=states,
            initial="IDLE",
            transitions=transitions,
            after_state_change=self._state_changed,
            **extra_kwargs,
        )
        self._state_changed()

    def _state_changed(self) -> None:
        """
        State machine callback that is called every time the obs_state changes.

        Responsible for ensuring that callbacks are called.
        """
        if self._callback is not None:
            self._callback(self.state)

class FhsBaseDevice(ABC, SKAObsDevice):
    
    PacketValidationFqdn = device_property(dtype="str")

    
    # @abstractmethod
    # def recover(self) -> None:
    #     pass
    
    # @abstractmethod
    # def configure(self, config) -> None:
    #     pass
    
    # @abstractmethod
    # def start(self) -> int:
    #     pass
    
    # @abstractmethod
    # def stop(self) -> int:
    #     pass
    
    # @abstractmethod
    # def deconfigure(self, config) -> None:
    #     pass
    
    # @abstractmethod
    # def status(self, clear: bool, status) -> None:
    #     pass
    
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
