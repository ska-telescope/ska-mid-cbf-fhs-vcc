from __future__ import annotations

import tango
from ska_control_model import ResultCode
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from tango.server import command

from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice, FhsFastCommand


class FhsLowLevelDeviceBase(FhsBaseDevice):
    @command(
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def TestCmd(self: FhsLowLevelDeviceBase) -> DevVarLongStringArrayType:
        return (
            [ResultCode.OK],
            ["TEST CMD OKAY."],
        )

    @command(
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def recover(self: FhsLowLevelDeviceBase) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Recover")
        result_code_message, command_id = command_handler()
        return [[result_code_message], [command_id]]

    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="Configuration json.",
    )
    @tango.DebugIt()
    def configure(self: FhsLowLevelDeviceBase, config: str) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Configure")
        result_code_message, command_id = command_handler(config)
        return [[result_code_message], [command_id]]

    @command(
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def start(self: FhsLowLevelDeviceBase) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Start")
        result_code_message, command_id = command_handler()
        return [[result_code_message], [command_id]]

    @command(
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def stop(self: FhsLowLevelDeviceBase) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Stop")
        result_code_message, command_id = command_handler()
        return [[result_code_message], [command_id]]

    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="Configuration json.",
    )
    @tango.DebugIt()
    def deconfigure(self: FhsLowLevelDeviceBase, config: str) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Deconfigure")
        result_code_message, command_id = command_handler(config)
        return [[result_code_message], [command_id]]

    @command(
        dtype_in="DevBoolean",
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def status(self: FhsLowLevelDeviceBase, clear: bool) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Status")
        result_code_message, command_id = command_handler(clear)
        return [[result_code_message], [command_id]]

    # -------------------
    # Fast Commands
    # -------------------

    class RecoverCommand(FhsFastCommand):
        def do(self) -> tuple[ResultCode, str]:
            return self._component_manager.recover()

    class ConfigureCommand(FhsFastCommand):
        def do(self, argin: str) -> tuple[ResultCode, str]:
            return self._component_manager.configure(argin=argin)

    class DeconfigureCommand(FhsFastCommand):
        def do(self, argin: str) -> tuple[ResultCode, str]:
            return self._component_manager.deconfigure(argin=argin)

    class StatusCommand(FhsFastCommand):
        def do(self, clear: bool = False) -> tuple[ResultCode, str]:
            return self._component_manager.status(clear=clear)