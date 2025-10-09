# -*- coding: utf-8 -*-
#
# This file is part of the ska-mid-cbf-fhs-vcc project
#
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.
#
# Copyright (c) 2025 National Research Council of Canada

from __future__ import annotations

from functools import partial
from typing import Any

from ska_mid_cbf_fhs_common.testing.simulation import FhsObsSimMode, SimModeObsCMBase
from tango.server import run

from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

__all__ = ["SimVCCAllBandsCM", "SimVCCAllBandsController"]


# Default simulator attribute return values are initialized with this dict
VCC_SIM_DEFAULT_ATTRIBUTE_VALUES = {
    "expectedDishId": "",
    "requestedRFIHeadroom": [0],
    "vccGains": [0],
    "frequencyBand": FrequencyBandEnum._1,
    "inputSampleRate": 0,
    "frequencyBandOffset": [0],
    "subarrayID": 0,
}

# Add any attributes that are configured for change/archive events to these sets
VCC_SIM_CHANGE_EVENT_ATTRS = {
    "subarrayID",
}
VCC_SIM_ARCHIVE_EVENT_ATTRS = {
    "subarrayID",
}


class SimVCCAllBandsCM(SimModeObsCMBase):
    def __init__(
        self: SimVCCAllBandsCM,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a new SimVCCAllBandsCM instance.

        Links VCCAllBandsComponentManager attributes to attribute overrides and
        commands to simulated command task submit method.
        """
        super().__init__(*args, **kwargs)

        # Setup attribute read overrides
        self.enum_attrs.update({"frequencyBand": FrequencyBandEnum})
        self.attribute_overrides.update(VCC_SIM_DEFAULT_ATTRIBUTE_VALUES)
        self._change_event_attrs = VCC_SIM_CHANGE_EVENT_ATTRS
        self._archive_event_attrs = VCC_SIM_ARCHIVE_EVENT_ATTRS


        # Setup LRC method simulation
        self.command_overrides.update(
            {
                "Abort": {
                    "invoked_action": "ABORT_INVOKED",
                    "completed_action": "ABORT_COMPLETED",
                },
                "ConfigureScan": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "allowed_obs_states": ["IDLE", "READY"],
                    "result_code": "OK",
                    "message": "ConfigureScan completed OK",
                    "invoked_action": "CONFIGURE_INVOKED",
                    "completed_action": "CONFIGURE_COMPLETED",
                },
                "Scan": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "allowed_obs_states": ["READY"],
                    "result_code": "OK",
                    "message": "Scan completed OK",
                    "invoked_action": "START_INVOKED",
                    "completed_action": "START_COMPLETED",
                },
                "EndScan": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "allowed_obs_states": ["SCANNING"],
                    "result_code": "OK",
                    "message": "EndScan completed OK",
                    "invoked_action": "STOP_INVOKED",
                    "completed_action": "STOP_COMPLETED",
                },
                "ObsReset": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "allowed_obs_states": ["FAULT", "ABORTED"],
                    "result_code": "OK",
                    "message": "ObsReset completed OK",
                    "invoked_action": "OBSRESET_INVOKED",
                    "completed_action": "OBSRESET_COMPLETED",
                },
                "UpdateSubarrayMembership": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "allowed_obs_states": ["IDLE"],
                    "result_code": "OK",
                    "message": "UpdateSubarrayMembership completed OK",
                },
                "AutoSetFilterGains": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "allowed_obs_states": ["SCANNING"],
                    "result_code": "OK",
                    "message": "AutoSetFilterGains completed OK",
                },
            }
        )
        self.configure_scan = partial(self.sim_command, command_name="ConfigureScan")
        self.scan = partial(self.sim_command, command_name="Scan")
        self.end_scan = partial(self.sim_command, command_name="EndScan")
        self.obs_reset = partial(self.sim_command, command_name="ObsReset")
        self.update_subarray_membership = partial(self.sim_command, command_name="UpdateSubarrayMembership")
        self.auto_set_filter_gains = partial(self.sim_command, command_name="AutoSetFilterGains")

    @property
    def expected_dish_id(self: SimVCCAllBandsCM) -> str:
        return self.get_attribute_override("expectedDishId")

    @property
    def subarray_id(self: SimVCCAllBandsCM) -> int:
        return self.get_attribute_override("subarrayID")

    @property
    def frequency_band(self: SimVCCAllBandsCM) -> FrequencyBandEnum:
        return self.get_attribute_override("frequencyBand")

    @property
    def input_sample_rate(self: SimVCCAllBandsCM) -> int:
        return self.get_attribute_override("inputSampleRate")

    @property
    def frequency_band_offset(self: SimVCCAllBandsCM) -> list[int]:
        return self.get_attribute_override("frequencyBandOffset")

    @property
    def last_requested_headrooms(self: SimVCCAllBandsCM) -> list[int]:
        return self.get_attribute_override("requestedRFIHeadroom")

    @property
    def vcc_gains(self: SimVCCAllBandsCM) -> list[int]:
        return self.get_attribute_override("vccGains")


class SimVCCAllBandsController(VCCAllBandsController, FhsObsSimMode):
    def create_component_manager(self: SimVCCAllBandsController) -> SimVCCAllBandsCM:
        return SimVCCAllBandsCM(
            logger=self.logger,
            attr_archive_callback=self.push_archive_event,
            attr_change_callback=self.push_change_event,
            communication_state_callback=self._communication_state_changed,
            component_state_callback=partial(FhsObsSimMode._component_state_changed, self),
        )


def main(args=None, **kwargs):  # noqa: E302
    """Start VCCAllBandsController simulator."""
    return run(
        classes=(SimVCCAllBandsController,),
        args=args,
        **kwargs,
    )


if __name__ == "__main__":  # noqa: #E305
    main()
