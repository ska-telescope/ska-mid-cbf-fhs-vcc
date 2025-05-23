from __future__ import annotations

from ska_mid_cbf_fhs_common import FhsLowLevelDeviceBase

from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_component_manager import VCCStreamMergeComponentManager


class VCCStreamMerge(FhsLowLevelDeviceBase):
    def create_component_manager(
        self: VCCStreamMerge,
    ) -> VCCStreamMergeComponentManager:
        return VCCStreamMergeComponentManager(
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

    def always_executed_hook(self: VCCStreamMerge) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: VCCStreamMerge) -> None:
        """Hook to delete device."""

    def init_command_objects(self: VCCStreamMerge) -> None:
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
    return VCCStreamMerge.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
