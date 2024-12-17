from __future__ import annotations

from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_device_base import FhsLowLevelDeviceBase
from ska_mid_cbf_fhs_vcc.wideband_power_meter.wideband_power_meter_component_manager import WidebandPowerMeterComponentManager


class WidebandPowerMeter(FhsLowLevelDeviceBase):
    def create_component_manager(
        self: WidebandPowerMeter,
    ) -> WidebandPowerMeterComponentManager:
        return WidebandPowerMeterComponentManager(
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

    async def always_executed_hook(self: WidebandPowerMeter) -> None:
        """Hook to be executed before any commands."""

    async def delete_device(self: WidebandPowerMeter) -> None:
        """Hook to delete device."""

    def init_command_objects(self: WidebandPowerMeter) -> None:
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
    return WidebandPowerMeter.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
