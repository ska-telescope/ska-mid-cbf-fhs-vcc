from __future__ import annotations

import tango
from ska_control_model import SimulationMode
from ska_tango_base.base.base_component_manager import BaseComponentManager
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import FastCommand, SubmittedSlowCommand
from ska_tango_base.obs.obs_device import SKAObsDevice
from tango.server import attribute, command, device_property

from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice




class MacBase(FhsBaseDevice, SKAObsDevice):
    
    # -----------------
    # Device Properties
    # -----------------
    PacketValidationAddress = device_property(dtype="str")
    
    def recover():
        pass
    
    def configure():
        pass
    
    def start():
        pass
    
    def stop():
        pass
    
    def deconfigure():
        pass
    
    def status():
        pass