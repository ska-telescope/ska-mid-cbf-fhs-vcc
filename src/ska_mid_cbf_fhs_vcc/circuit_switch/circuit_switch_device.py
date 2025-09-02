from __future__ import annotations

from ska_mid_cbf_fhs_common import FhsLowLevelBaseDevice

from ska_mid_cbf_fhs_vcc.circuit_switch.circuit_switch_component_manager import (
    CircuitSwitchComponentManager,
)


class CircuitSwitch(FhsLowLevelBaseDevice):
    def create_component_manager(
        self: CircuitSwitch,
    ) -> CircuitSwitchComponentManager:
        return CircuitSwitchComponentManager(
            device=self,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            component_state_callback=self._component_state_changed,
            logger=self.logger,
        )

    def always_executed_hook(self: CircuitSwitch) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: CircuitSwitch) -> None:
        """Hook to delete device."""

    def init_command_objects(self: CircuitSwitch) -> None:
        super().init_command_objects()

        # init the fast commands
        commands_and_classes = [
            ("Recover", FhsLowLevelBaseDevice.RecoverCommand),
            ("Configure", FhsLowLevelBaseDevice.ConfigureCommand),
            ("Deconfigure", FhsLowLevelBaseDevice.DeconfigureCommand),
            ("GetStatus", FhsLowLevelBaseDevice.GetStatusCommand),
        ]
        super().init_fast_command_objects(commands_and_classes)


def main(args=None, **kwargs):
    return CircuitSwitch.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
