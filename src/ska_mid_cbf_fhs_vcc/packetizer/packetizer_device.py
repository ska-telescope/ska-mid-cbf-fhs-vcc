from __future__ import annotations

from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_device_base import FhsLowLevelDeviceBase
from ska_mid_cbf_fhs_vcc.packetizer.packetizer_component_manager import PacketizerComponentManager


class Packetizer(FhsLowLevelDeviceBase):
    def create_component_manager(
        self: Packetizer,
    ) -> PacketizerComponentManager:
        return PacketizerComponentManager(
            device=self,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            obs_command_running_callback=self._obs_command_running,
            component_state_callback=self._component_state_changed,
            obs_state_action_callback=self._obs_state_action,
            logger=self.logger,
        )

    def always_executed_hook(self: Packetizer) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: Packetizer) -> None:
        """Hook to delete device."""

    def init_command_objects(self: Packetizer) -> None:
        commandsAndMethods = [
            ("Start", "start"),
            ("Stop", "stop"),
            ("TestCmd", "test_cmd"),
        ]
        super().init_command_objects(commandsAndMethods)

        # init the fast commands
        commandsAndClasses = [
            ("Configure", FhsLowLevelDeviceBase.ConfigureCommand),
            ("Recover", FhsLowLevelDeviceBase.RecoverCommand),
            ("GetStatus", FhsLowLevelDeviceBase.GetStatusCommand),
            ("GoToIdle", FhsLowLevelDeviceBase.GoToIdleCommand),
        ]

        super().init_fast_command_objects(commandsAndClasses)


def main(args=None, **kwargs):
    return Packetizer.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
