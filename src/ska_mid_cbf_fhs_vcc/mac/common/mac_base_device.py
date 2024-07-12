from __future__ import annotations

from ska_mid_cbf_fhs_vcc.mac.common.mac_component_manager_base import MacComponentManagerBase
import tango
from ska_control_model import SimulationMode
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import SubmittedSlowCommand
from tango.server import command

from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice




class MacBase(FhsBaseDevice):
    

    
    
    def create_component_manager(self: MacBase) -> MacComponentManagerBase:
        # NOTE: using component manager default of SimulationMode.TRUE,
        # as self._simulation_mode at this point during init_device()
        # SimulationMode.FALSE
        return MacComponentManagerBase(
            mac_id=self.device_id,
            logger=self.logger,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            obs_command_running_callback=self._obs_command_running,
            component_state_callback=self._component_state_changed,
        )
    
    def always_executed_hook(self: MacBase) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: MacBase) -> None:
        """Hook to delete device."""
        
    def init_command_objects(self: FhsBaseDevice) -> None:
        """Set up the command objects."""
        super().init_command_objects()

        self.register_command_object(
                "TestCmd",
                SubmittedSlowCommand(
                    command_name="TestCmd",
                    command_tracker=self._command_tracker,
                    component_manager=self.component_manager,
                    method_name="test_cmd",
                    logger=self.logger,
                ),
            )
            
            
    @command(
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def TestCmd(self: MacBase) -> DevVarLongStringArrayType:
        self.logger.log('TEST CMD RUNNING')
        command_handler = self.get_command_object(command_name="TestCmd")
        result_code_message, command_id  = command_handler()
        return [[result_code_message], [command_id]] 
    
    # @command(
    #     dtype_out="DevVarLongStringArray",
    # )
    # @tango.DebugIt()
    # def recover(self: MacBase) -> DevVarLongStringArrayType:
    #     command_handler = self.get_command_object(command_name="Recover")
    #     result_code_message, command_id = command_handler()
    #     return [[result_code_message], [command_id]]
    
    # @command(
    #     dtype_in="DevString",
    #     dtype_out="DevVarLongStringArray",
    #     doc_in="Configuration json.",
    # )
    # @tango.DebugIt()
    # def configure(self: MacBase, config: str) -> DevVarLongStringArrayType:
    #     command_handler = self.get_command_object(command_name="Configure")
    #     result_code_message, command_id = command_handler(config)
    #     return [[result_code_message], [command_id]]
    
    # @command(
    #     dtype_out="DevVarLongStringArray",
    # )
    # @tango.DebugIt()
    # def start(self: MacBase) -> DevVarLongStringArrayType:
    #     pass
    
    # @command(
    #     dtype_out="DevVarLongStringArray",
    # )
    # @tango.DebugIt()
    # def stop(self: MacBase) -> DevVarLongStringArrayType:
    #     pass
    
    # @command(
    #     dtype_in="DevString",
    #     dtype_out="DevVarLongStringArray",
    #     doc_in="Configuration json.",
    # )
    # @tango.DebugIt()
    # def deconfigure(self: MacBase, config: str) -> DevVarLongStringArrayType:
    #     command_handler = self.get_command_object(command_name="Deconfigure")
    #     result_code_message, command_id = command_handler(config)
    #     return [[result_code_message], [command_id]]
    
    # @command(
    #     dtype_in="DevString",
    #     dtype_out="DevVarLongStringArray",
    #     doc_in="Mac configuration.",
    # )
    # @tango.DebugIt()
    # def status(self: MacBase, clear: bool) -> DevVarLongStringArrayType:
    #     command_handler = self.get_command_object(command_name="Status")
    #     result_code_message, command_id = command_handler(clear)
    #     return [[result_code_message], [command_id]]
    
    class InitCommand(FhsBaseDevice.InitCommand):
        """
        A class for the Vcc's init_device() "command".
        """

        def do(
            self: MacBase.InitCommand,
            *args: any,
            **kwargs: any,
        ) -> DevVarLongStringArrayType:
            """
            Stateless hook for device initialisation.

            :return: A tuple containing a return code and a string
                message indicating status. The message is for
                information purpose only.
            :rtype: (ResultCode, str)
            """
            (result_code, msg) = super().do(*args, **kwargs)

            return (result_code, msg)
        
def main(args=None, **kwargs):
    return MacBase.run_server(args=args or None, **kwargs)

if __name__ == "__main__":
    main()
