from __future__ import annotations

from typing import Any

# Tango imports
import tango
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import ResultCode, SubmittedSlowCommand
from ska_tango_base.control_model import SimulationMode
from ska_tango_base.obs.obs_device import SKAObsDevice
from tango.server import attribute, command, device_property
from ska_mid_cbf_fhs_vcc.mac.mac_component_manager import Mac200GbComponentManager

__all__ = ["Mac200", "main"]


class Mac200(SKAObsDevice):
    
    test = 0
    
    # def recover():
    #     pass
    
    # def configure():
    #     pass
    
    # def start():
    #     pass
    
    # def stop():
    #     pass
    
    # def deconfigure():
    #     pass
    
    # def status():
    #     pass
    
    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="Band config string.",
    )
    @tango.DebugIt()
    def test_cmd(
        self: Mac200
    ) -> DevVarLongStringArrayType:
        return 'test command working!'
    
    def create_component_manager(self: Mac200) -> Mac200GbComponentManager:
        # NOTE: using component manager default of SimulationMode.TRUE,
        # as self._simulation_mode at this point during init_device()
        # SimulationMode.FALSE
        return Mac200GbComponentManager(
            logger=self.logger
        )

    def always_executed_hook(self: Mac200) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: Mac200) -> None:
        """Hook to delete device."""
        
def main(args=None, **kwargs):
    return Mac200.run_server(args=args or None, **kwargs)

if __name__ == "__main__":
    main()
