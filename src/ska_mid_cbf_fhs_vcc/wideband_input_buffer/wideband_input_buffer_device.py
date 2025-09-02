from __future__ import annotations

from ska_mid_cbf_fhs_common import FhsLowLevelBaseDevice
from tango.server import attribute

from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_component_manager import (
    WidebandInputBufferComponentManager,
)


class WidebandInputBuffer(FhsLowLevelBaseDevice):
    @attribute(dtype="str")
    def expectedDishId(self: WidebandInputBuffer) -> str:
        return self.component_manager.expected_dish_id

    @expectedDishId.write
    def expectedDishId(self: WidebandInputBuffer, value: str) -> None:
        self.component_manager.expected_dish_id = value

    def create_component_manager(
        self: WidebandInputBuffer,
    ) -> WidebandInputBufferComponentManager:
        return WidebandInputBufferComponentManager(
            device=self,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            component_state_callback=self._component_state_changed,
            logger=self.logger,
        )

    def always_executed_hook(self: WidebandInputBuffer) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: WidebandInputBuffer) -> None:
        """Hook to delete device."""

    def init_command_objects(self: WidebandInputBuffer) -> None:
        commands_and_methods = [
            ("Start", "start"),
            ("Stop", "stop"),
        ]
        super().init_command_objects(commands_and_methods)

        # init the fast commands
        commands_and_classes = [
            ("Recover", FhsLowLevelBaseDevice.RecoverCommand),
            ("Configure", FhsLowLevelBaseDevice.ConfigureCommand),
            ("GetStatus", FhsLowLevelBaseDevice.GetStatusCommand),
        ]

        super().init_fast_command_objects(commands_and_classes)


def main(args=None, **kwargs):
    return WidebandInputBuffer.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
