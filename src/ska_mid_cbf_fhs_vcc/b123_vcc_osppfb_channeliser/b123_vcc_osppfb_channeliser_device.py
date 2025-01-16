from __future__ import annotations

from ska_mid_cbf_fhs_common import FhsBaseDevice, FhsLowLevelDeviceBase

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channeliser.b123_vcc_osppfb_channeliser_component_manager import (
    B123VccOsppfbChanneliserComponentManager,
)


class B123VccOsppfbChanneliser(FhsLowLevelDeviceBase):
    def create_component_manager(
        self: B123VccOsppfbChanneliser,
    ) -> B123VccOsppfbChanneliserComponentManager:
        return B123VccOsppfbChanneliserComponentManager(
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

    def always_executed_hook(self: B123VccOsppfbChanneliser) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: B123VccOsppfbChanneliser) -> None:
        """Hook to delete device."""

    def init_command_objects(self: B123VccOsppfbChanneliser) -> None:
        super().init_command_objects()

        # init the fast commands
        commandsAndClasses = [
            ("Recover", FhsLowLevelDeviceBase.RecoverCommand),
            ("Configure", FhsLowLevelDeviceBase.ConfigureCommand),
            ("Deconfigure", FhsLowLevelDeviceBase.DeconfigureCommand),
            ("GetStatus", FhsLowLevelDeviceBase.GetStatusCommand),
            ("GoToIdle", FhsBaseDevice.GoToIdleCommand),
        ]

        super().init_fast_command_objects(commandsAndClasses)


def main(args=None, **kwargs):
    return B123VccOsppfbChanneliser.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
