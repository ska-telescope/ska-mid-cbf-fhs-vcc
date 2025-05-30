# -*- coding: utf-8 -*-
#
# This file is part of the SKA Mid CBF FHS VCC project With inspiration gathered from the Mid.CBF MCS project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE.txt for more info.


from __future__ import annotations

from ska_mid_cbf_fhs_common import FhsLowLevelDeviceBase
from tango.server import device_property

from ska_mid_cbf_fhs_vcc.mac.mac_component_manager import MacComponentManager


class Mac200(FhsLowLevelDeviceBase):
    MacType = device_property(dtype="str")

    def create_component_manager(self: Mac200) -> MacComponentManager:
        return MacComponentManager(
            device=self,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            component_state_callback=self._component_state_changed,
            logger=self.logger,
        )

    def always_executed_hook(self: Mac200) -> None:
        """Hook to be executed before any commands."""

    def delete_device(self: Mac200) -> None:
        """Hook to delete device."""

    def init_command_objects(self: Mac200) -> None:
        # init the LRC
        commandsAndMethods = [
            ("Start", "start"),
            ("Stop", "stop"),
            ("TestCmd", "test_cmd"),
        ]
        super().init_command_objects(commandsAndMethods)

        # init the fast commands
        commandsAndClasses = [
            ("Recover", FhsLowLevelDeviceBase.RecoverCommand),
            ("Configure", FhsLowLevelDeviceBase.ConfigureCommand),
            ("Deconfigure", FhsLowLevelDeviceBase.DeconfigureCommand),
            ("GetStatus", FhsLowLevelDeviceBase.GetStatusCommand),
            ("GoToIdle", FhsLowLevelDeviceBase.GoToIdleCommand),
        ]

        super().init_fast_command_objects(commandsAndClasses)


def main(args=None, **kwargs):
    return Mac200.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
