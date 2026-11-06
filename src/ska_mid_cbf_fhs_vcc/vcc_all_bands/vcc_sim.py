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

from ska_control_model import HealthState
from ska_mid_cbf_fhs_common import FhsSimMode, SimModeCMBase
from tango.server import run

from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

__all__ = ["SimVCCAllBandsCM", "SimVCCAllBandsController"]


# Default simulator attribute return values are initialized with this dict
VCC_SIM_DEFAULT_ATTRIBUTE_VALUES = {
    "healthState": HealthState.OK,  # healthState updated here on top of sim base for unit tests
    "healthInfo": "",
    "expectedDishId": "",
    "requestedRFIHeadroom": [0],
    "vccGains": [0],
    "vlanLookup": {},
    "frequencyBand": FrequencyBandEnum._1,
    "inputSampleRate": 0,
    "frequencyBandOffset": [0],
    "subarrayID": 0,
}

# Add any attributes that are configured for change/archive events to these sets
VCC_SIM_CHANGE_EVENT_ATTRS = {"healthState", "subarrayID", "healthInfo"}  # healthState updated here on top of sim base for unit tests
VCC_SIM_ARCHIVE_EVENT_ATTRS = {
    "healthState",  # healthState updated here on top of sim base for unit tests
    "subarrayID",
}


class SimVCCAllBandsCM(SimModeCMBase):
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
                "ConfigureScan": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "result_code": "OK",
                    "message": "ConfigureScan completed OK",
                },
                "GoToIdle": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "result_code": "OK",
                    "message": "GoToIdle completed OK",
                },
                "UpdateSubarrayMembership": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "result_code": "OK",
                    "message": "UpdateSubarrayMembership completed OK",
                    "attr_change_events": {
                        "subarrayID": None,
                    },
                },
                "AutoSetFilterGains": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "result_code": "OK",
                    "message": "AutoSetFilterGains completed OK",
                },
                "ConfigureVCCBite": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "result_code": "OK",
                    "message": "ConfigureVCCBite completed OK",
                },
                "DeconfigureVCCBite": {
                    "allowed": True,
                    "allowed_states": ["ON"],
                    "result_code": "OK",
                    "message": "DeconfigureVCCBite completed OK",
                },
            }
        )
        self.configure_scan = partial(self.sim_command, command_name="ConfigureScan", transaction_id="TEST_CS")
        self.go_to_idle = partial(self.sim_command, command_name="GoToIdle", transaction_id="TEST_GTI")
        self.update_subarray_membership = partial(self.sim_command, command_name="UpdateSubarrayMembership", transaction_id="TEST_USM")
        self.auto_set_filter_gains = partial(self.sim_command, command_name="AutoSetFilterGains", transaction_id="TEST_ASFG")
        self.configure_vcc_bite = partial(self.sim_command, command_name="ConfigureVCCBite", transaction_id="TEST_CVB")
        self.deconfigure_vcc_bite = partial(self.sim_command, command_name="DeconfigureVCCBite", transaction_id="TEST_DVB")

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

    @property
    def vlan_lookup(self: SimVCCAllBandsCM) -> dict:
        return self.get_attribute_override("vlanLookup")

    @property
    def health_info(self: SimVCCAllBandsCM) -> str:
        return self.get_attribute_override("healthInfo")


class SimVCCAllBandsController(VCCAllBandsController, FhsSimMode):
    change_event_attributes = VCC_SIM_CHANGE_EVENT_ATTRS
    archive_event_attributes = VCC_SIM_ARCHIVE_EVENT_ATTRS

    def read_healthState(self) -> HealthState:
        """
        Read the latest healthState override.

        :return HealthState:
        """
        return self.component_manager.attribute_overrides_queue_dict.peek("healthState")

    def create_component_manager(self: SimVCCAllBandsController) -> SimVCCAllBandsCM:
        return SimVCCAllBandsCM(
            logger=self.logger,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            communication_state_callback=self._communication_state_changed,
            component_state_callback=self._component_state_changed,
        )


def main(args=None, **kwargs):
    """Start VCCAllBandsController simulator."""
    return run(
        classes=(SimVCCAllBandsController,),
        args=args,
        **kwargs,
    )


if __name__ == "__main__":
    main()
