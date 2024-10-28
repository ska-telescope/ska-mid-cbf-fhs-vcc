from __future__ import annotations

from logging import Logger
from typing import TypeVar, cast

import tango
from ska_control_model import HealthState, ObsState, PowerState, ResultCode, CommunicationStatus
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from ska_tango_base.commands import ArgumentValidator, FastCommand, SubmittedSlowCommand, _BaseCommand
from ska_tango_base.obs.obs_device import SKAObsDevice
from tango import DebugIt, DevState
from tango.server import attribute, command, device_property

from ska_mid_cbf_fhs_vcc.common.fhs_component_manager_base import FhsComponentManagerBase
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine, FhsObsStateModel

__all__ = ["FhsBaseDevice", "FhsFastCommand", "main"]

CompManager = TypeVar("CompManager", bound=FhsComponentManagerBase)


# -----------------------------------------------------
# FhsFastCommand class
#
# -----------------------------------------------------
class FhsFastCommand(FastCommand):
    def __init__(
        self: _BaseCommand,
        component_manager: CompManager,
        logger: Logger | None = None,
        validator: ArgumentValidator | None = None,
    ) -> None:
        super().__init__(logger, validator)
        self._component_manager = component_manager


# -----------------------------------------------------
# FhsBaseDevice class
#
# -----------------------------------------------------
class FhsBaseDevice(SKAObsDevice):
    # -----------------
    # Device Properties
    # -----------------
    device_id = device_property(dtype="int")
    config_location = device_property(dtype="str")
    simulation_mode = device_property(dtype="int")
    emulation_mode = device_property(dtype="int")
    device_version_num = device_property(dtype="str")
    device_gitlab_hash = device_property(dtype="str")

    # -----------------
    # Device Attributes
    # -----------------
    @attribute(dtype=CommunicationStatus)
    def communicationState(self: FhsBaseDevice) -> CommunicationStatus:
        return self.component_manager.communication_state

    ##############
    # Commands
    ##############
    @command(
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def GoToIdle(self: FhsBaseDevice) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="GoToIdle")
        result_code_message, command_id = command_handler()
        return [[result_code_message], [command_id]]

    ###############
    # Functions
    ###############
    def _init_state_model(self: FhsBaseDevice) -> None:
        """Set up the state model for the device."""
        super()._init_state_model()

        # supplying the reduced observing state machine defined above
        self.obs_state_model = FhsObsStateModel(
            logger=self.logger,
            callback=self._update_obs_state,
            state_machine_factory=FhsObsStateMachine,
        )

    def init_command_objects(self: FhsBaseDevice, commandsAndMethods: list[tuple] | None = None) -> None:
        """Set up the command objects."""
        super().init_command_objects()

        if commandsAndMethods:
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

    def init_fast_command_objects(self: FhsBaseDevice, commandsAndClasses: list[tuple]) -> None:
        for command_name, fast_command in commandsAndClasses:
            self.register_command_object(
                command_name,
                fast_command(
                    component_manager=self.component_manager,
                    logger=self.logger,
                ),
            )

    def reset_obs_state(self: FhsBaseDevice):
        if self._obs_state in [ObsState.FAULT, ObsState.ABORTED]:
            self.obs_state_model.perform_action(FhsObsStateMachine.GO_TO_IDLE)

    def _obs_command_running(self: FhsBaseDevice, hook: str, running: bool) -> None:
        """
        Callback provided to component manager to drive the obs state model into
        transitioning states during the relevant command's submitted thread.

        :param hook: the observing command-specific hook
        :param running: True when thread begins, False when thread completes
        """
        action = "invoked" if running else "completed"
        self.logger.info(f"Changing ObsState from running command, calling: {hook}_{action} ")
        self.obs_state_model.perform_action(f"{hook}_{action}")

    def _component_state_changed(
        self: FhsBaseDevice,
        idle: bool | None = None,
        configuring: bool | None = None,
        reset: bool | None = None,
        fault: bool | None = None,
        power: PowerState | None = None,
    ) -> None:
        super()._component_state_changed(fault=fault, power=power)

        if idle is not None:
            self.obs_state_model.perform_action(FhsObsStateMachine.GO_TO_IDLE)

        if configuring is not None:
            if configuring:
                self.obs_state_model.perform_action(FhsObsStateMachine.CONFIGURE_INVOKED)
            else:
                self.obs_state_model.perform_action(FhsObsStateMachine.CONFIGURE_COMPLETED)

        if reset is not None:
            if reset:
                self.obs_state_model.perform_action(FhsObsStateMachine.RESET_INVOKED)
            else:
                self.obs_state_model.perform_action(FhsObsStateMachine.RESET_COMPLETED)

        if fault is not None:
            self.obs_state_model.perform_action(FhsObsStateMachine.COMPONENT_FAULT)

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

    def _communication_state_changed(self: FhsBaseDevice, communication_state: CommunicationStatus) -> None:
        super()._communication_state_changed(communication_state=communication_state)
        self.push_change_event("communicationState", communication_state)

    def init_device(self: FhsBaseDevice) -> None:
        super().init_device()
        self.set_state(DevState.ON)
        self.set_status("ON")
        self._update_health_state(HealthState.OK)
        self._update_obs_state(obs_state=ObsState.IDLE)

    def get_dev_state(self: FhsBaseDevice) -> DevState:
        return self.dev_state()

    # ----------------------
    # Unimplemented Commands
    # ----------------------

    @command(dtype_out="DevVarLongStringArray")
    @DebugIt()
    def On(self: FhsBaseDevice) -> DevVarLongStringArrayType:
        """
        Turn device on.

        :return: A tuple containing a return code and a string
            message indicating status. The message is for
            information purpose only.
        """
        return (
            [ResultCode.REJECTED],
            ["On command rejected, as it is unimplemented for this device."],
        )

    @command(dtype_out="DevVarLongStringArray")
    @DebugIt()
    def Off(self: FhsBaseDevice) -> DevVarLongStringArrayType:
        """
        Turn device off.

        :return: A tuple containing a return code and a string
            message indicating status. The message is for
            information purpose only.
        """
        return (
            [ResultCode.REJECTED],
            ["Off command rejected, as it is unimplemented for this device."],
        )

    @command(dtype_out="DevVarLongStringArray")
    @DebugIt()
    def Standby(self: FhsBaseDevice) -> DevVarLongStringArrayType:
        """
        Put the device into standby mode; currently unimplemented in Mid.CBF

        :return: A tuple containing a return code and a string
            message indicating status. The message is for
            information purpose only.
        """
        return (
            [ResultCode.REJECTED],
            ["Standby command rejected; Mid.CBF does not currently implement standby state."],
        )

    @command(dtype_out="DevVarLongStringArray")
    @DebugIt()
    def Reset(self: FhsBaseDevice) -> DevVarLongStringArrayType:
        """
        Reset the device; currently unimplemented in Mid.CBF

        :return: A tuple containing a return code and a string
            message indicating status. The message is for
            information purpose only.
        """
        return (
            [ResultCode.REJECTED],
            ["Reset command rejected, as it is unimplemented for this device."],
        )

    class GoToIdleCommand(FhsFastCommand):
        def do(self) -> tuple[ResultCode, str]:
            return self._component_manager.go_to_idle()


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
