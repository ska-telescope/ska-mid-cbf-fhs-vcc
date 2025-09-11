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
from tango.server import run, attribute
from queue import Queue

from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

__all__ = ["SimVCCAllBandsCM", "SimVCCAllBandsController"]

VCC_SIM_DEFAULT_ATTRIBUTE_VALUES = {
    "expectedDishId": "",
    "requestedRFIHeadroom": [0],
    "vccGains": [0],
    "frequencyBand": FrequencyBandEnum._1,
    "inputSampleRate": 0,
    "frequencyBandOffset": [0],
    "subarrayID": 0,
}
class OverridesQueue(Queue):
    def __init__(self, defaultOverride: dict):
        super().__init__()
        self.defaultOverride = defaultOverride
    def get(self):
        if self.qsize() < 1:
            return self.defaultOverride
        return super().get()


class OverridesQueueDict:
    def __init__(self, defaultOverrides: dict):
        self.defaultOverrides = defaultOverrides
        self.queueDict = self._buildQueues(defaultOverrides)
    def _buildQueues(self, defaultOverrides):
        queueDict = dict()
        for key, value in defaultOverrides.items():
            queueDict[key] = OverridesQueue(value)
        return queueDict
    def get(self, identifier: str):
        return self.queueDict[identifier].get()
    def update(self, identifier, override):
        self.queueDict[identifier].put(override)




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
        self.command_overrides_queue_dict = OverridesQueueDict(self.command_overrides)
        self.attribute_overrides_queue_dict = OverridesQueueDict(self.attribute_overrides)
        self.configure_scan = partial(self.sim_command, command_name="ConfigureScan")
        self.scan = partial(self.sim_command, command_name="Scan")
        self.end_scan = partial(self.sim_command, command_name="EndScan")
        self.obs_reset = partial(self.sim_command, command_name="ObsReset")
        self.update_subarray_membership = partial(self.sim_command, command_name="UpdateSubarrayMembership")
        self.auto_set_filter_gains = partial(self.sim_command, command_name="AutoSetFilterGains")

    def get_command_overrides(self: SimVCCAllBandsCM, command: str) -> str:
        return self.command_overrides_queue_dict.get(command)

    def set_command_overrides(self: SimVCCAllBandsCM, overrides: dict) -> str:
        for key, value in overrides:
            self.command_overrides_queue_dict.update(key, value)

    def get_attribute_overrides(self: SimVCCAllBandsCM, attribute: str) -> str:
        return self.attribute_overrides_queue_dict.get(attribute)

    def set_attribute_overrides(self: SimVCCAllBandsCM, overrides: dict) -> str:
        for key, value in overrides.items():
            self.attribute_overrides_queue_dict.update(key, value)

    @property
    def simOverrides2(self: SimVCCAllBandsCM):
        return super().simOverrides

    @simOverrides2.setter
    def simOverrides2(self: SimVCCAllBandsCM, overrides: dict):
        super().simOverrides = overrides
        for key, value in overrides.items():
            if key == "attributes":
                self.set_attribute_overrides(value)
            if key == "commands":
                self.set_command_overrides(value)

    @property
    def expected_dish_id(self: SimVCCAllBandsCM) -> str:
        return self.get_attribute_overrides("expectedDishId")

    @property
    def subarray_id(self: SimVCCAllBandsCM) -> int:
        return self.get_attribute_overrides("subarrayID")

    @property
    def frequency_band(self: SimVCCAllBandsCM) -> FrequencyBandEnum:
        return self.get_attribute_overrides("frequencyBand")

    @property
    def input_sample_rate(self: SimVCCAllBandsCM) -> int:
        return self.get_attribute_overrides("inputSampleRate")

    @property
    def frequency_band_offset(self: SimVCCAllBandsCM) -> list[int]:
        return self.get_attribute_overrides("frequencyBandOffset")

    @property
    def last_requested_headrooms(self: SimVCCAllBandsCM) -> list[int]:
        return self.get_attribute_overrides("requestedRFIHeadroom")

    @property
    def vcc_gains(self: SimVCCAllBandsCM) -> list[int]:
        return self.get_attribute_overrides("vccGains")


class SimVCCAllBandsController(VCCAllBandsController, FhsObsSimMode):
    def create_component_manager(self: SimVCCAllBandsController) -> SimVCCAllBandsCM:
        return SimVCCAllBandsCM(
            logger=self.logger,
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
