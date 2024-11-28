from __future__ import annotations

from ska_mid_cbf_fhs_vcc.vcc_osppfb_channeliser.vcc_osppfb_channelizer_component_manager import (
    VccOsppfbChanneliserComponentManager,
)
from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_device_base import FhsLowLevelDeviceBase
from tango.server import device_property


class VccOsppfbChanneliser(FhsLowLevelDeviceBase):
    channelizer_type = device_property(dtype="str")
    
    def create_component_manager(
        self: VccOsppfbChanneliser,
    ) -> VccOsppfbChanneliserComponentManager:
        return VccOsppfbChanneliserComponentManager(
            device=self,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            obs_command_running_callback=self._obs_command_running,
            component_state_callback=self._component_state_changed,
            obs_state_action_callback=self._obs_state_action,
            channelizer_type=self.channelizer_type,
            logger=self.logger,
        )

    def always_executed_hook(self: VccOsppfbChanneliser) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: VccOsppfbChanneliser) -> None:
        """Hook to delete device."""

    def init_command_objects(self: VccOsppfbChanneliser) -> None:
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
    return VccOsppfbChanneliser.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
