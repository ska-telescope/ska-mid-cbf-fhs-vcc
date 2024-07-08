from __future__ import annotations  # allow forward references in type hints


import gc
import json
import os
from typing import Iterator
from unittest.mock import Mock

import pytest
from ska_control_model import AdminMode, ObsState, ResultCode, SimulationMode
from ska_tango_testing import context
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup

from ska_mid_cbf_fhs_vcc.mac.mac_200gb_device import Mac200

class MacComponentManagerBaseTest():
    
    
    
    def InitTest(self: MacComponentManagerBaseTest):
        mac_device = Mac200("test", "test")
        mac_component_manager = mac_device.create_component_manager()
        
def main(*args: str, **kwargs: str) -> int:
    mac_component = MacComponentManagerBaseTest()
    
    mac_component.InitTest()


if __name__ == "__main__":
    main()

        
        
        