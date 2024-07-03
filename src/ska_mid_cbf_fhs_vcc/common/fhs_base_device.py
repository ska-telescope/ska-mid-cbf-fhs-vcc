from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import tango
from ska_control_model import SimulationMode
from ska_tango_base.base.base_component_manager import BaseComponentManager
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import FastCommand, SubmittedSlowCommand
from ska_tango_base.obs.obs_device import SKAObsDevice
from tango.server import attribute, command, device_property


class FhsBaseDevice(ABC, SKAObsDevice):
    
    
    
    @abstractmethod
    def recover(self) -> None:
        pass
    
    @abstractmethod
    def configure(self, config) -> None:
        pass
    
    @abstractmethod
    def start(self) -> int:
        pass
    
    @abstractmethod
    def stop(self) -> int:
        pass
    
    @abstractmethod
    def deconfigure(self, config) -> None:
        pass
    
    @abstractmethod
    def status(self, clear: bool, status) -> None:
        pass
    
    # def init_command_objects(self: FhsBaseDevice) -> None:
    #     """Set up the command objects."""
    #     super().init_command_objects()

    #     # overriding base On/Off SubmittedSlowCommand register with FastCommand objects
    #     self.register_command_object(
    #         "On",
    #         self.OnCommand(
    #             component_manager=self.component_manager, logger=self.logger
    #         ),
    #     )
    #     self.register_command_object(
    #         "Off",
    #         self.OffCommand(
    #             component_manager=self.component_manager, logger=self.logger
    #         ),
    #     )

    #     for command_name, method_name in [
    #         ("Recover", "recover"),
    #         ("Configure", "configure"),
    #         ("Start", "start"),
    #         ("Stop", "stop"),
    #         ("Deconfigure", "deconfigure"),
    #         ("Status", "status"),
    #     ]:
    #         self.register_command_object(
    #             command_name,
    #             SubmittedSlowCommand(
    #                 command_name=command_name,
    #                 command_tracker=self._command_tracker,
    #                 component_manager=self.component_manager,
    #                 method_name=method_name,
    #                 logger=self.logger,
    #             ),
    #         )