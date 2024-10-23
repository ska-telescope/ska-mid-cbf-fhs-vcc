from __future__ import annotations

from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_device_base import FhsLowLevelDeviceBase
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_component_manager import (
    FrequencySliceSelectionComponentManager,
)


class FrequencySliceSelection(FhsLowLevelDeviceBase):
    def create_component_manager(
        self: FrequencySliceSelection,
    ) -> FrequencySliceSelectionComponentManager:
        return FrequencySliceSelectionComponentManager(
            device_id=self.device_id,
            config_location=self.config_location,
            simulation_mode=self.simulation_mode,
            emulation_mode=self.emulation_mode,
            emulator_ip_block_id=self.emulator_ip_block_id,
            emulator_id=self.emulator_id,
            firmware_ip_block_id=self.firmware_ip_block_id,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            obs_command_running_callback=self._obs_command_running,
            component_state_callback=self._component_state_changed,
            logger=self.logger,
        )

    def always_executed_hook(self: FrequencySliceSelection) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: FrequencySliceSelection) -> None:
        """Hook to delete device."""

    def init_command_objects(self: FrequencySliceSelection) -> None:
        super().init_command_objects()

        # init the fast commands
        commandsAndClasses = [
            ("Recover", FhsLowLevelDeviceBase.RecoverCommand),
            ("Configure", FhsLowLevelDeviceBase.ConfigureCommand),
            ("Deconfigure", FhsLowLevelDeviceBase.DeconfigureCommand),
            ("GetStatus", FhsLowLevelDeviceBase.GetStatusCommand),
        ]
        super().init_fast_command_objects(commandsAndClasses)


def main(args=None, **kwargs):
    return FrequencySliceSelection.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
