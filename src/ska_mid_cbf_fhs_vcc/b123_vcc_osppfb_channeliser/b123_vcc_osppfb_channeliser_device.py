from __future__ import annotations

from ska_mid_cbf_fhs_common import FhsBaseDevice, FhsLowLevelBaseDevice

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channeliser.b123_vcc_osppfb_channeliser_component_manager import (
    B123VccOsppfbChanneliserComponentManager,
)


class B123VccOsppfbChanneliser(FhsLowLevelBaseDevice):
    def create_component_manager(
        self: B123VccOsppfbChanneliser,
    ) -> B123VccOsppfbChanneliserComponentManager:
        return B123VccOsppfbChanneliserComponentManager(
            device=self,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            component_state_callback=self._component_state_changed,
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
            ("Recover", FhsLowLevelBaseDevice.RecoverCommand),
            ("Configure", FhsLowLevelBaseDevice.ConfigureCommand),
            ("Deconfigure", FhsLowLevelBaseDevice.DeconfigureCommand),
            ("GetStatus", FhsLowLevelBaseDevice.GetStatusCommand),
        ]

        super().init_fast_command_objects(commandsAndClasses)


def main(args=None, **kwargs):
    return B123VccOsppfbChanneliser.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
