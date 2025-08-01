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

from ska_mid_cbf_fhs_common.testing.simulation import ObsCMSim

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_helpers import FrequencyBandEnum

__all__ = ["VccCMSim"]


class VccCMSim(ObsCMSim):
    def __init__(
        self: VccCMSim,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a new VccCMSim instance.

        Links VCCAllBandsComponentManager attributes to attribute overrides and
        commands to simulated command task submit method.
        """
        super().__init__(*args, **kwargs)

        # Setup attribute read overrides
        self.enum_attrs.update({"frequencyBand": FrequencyBandEnum})
        self.attribute_overrides.update(
            {
                "expectedDishId": "",
                "requestedRFIHeadroom": [0],
                "vccGains": [0],
                "frequencyBand": FrequencyBandEnum._1,
                "inputSampleRate": 0,
                "frequencyBandOffset": [0],
                "subarrayID": 0,
            }
        )

        # Setup LRC method simulation
        self.command_overrides.update(
            {
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
        self.configure_band = partial(self.sim_command, command_name="ConfigureBand")
        self.configure_scan = partial(self.sim_command, command_name="ConfigureScan")
        self.scan = partial(self.sim_command, command_name="Scan")
        self.end_scan = partial(self.sim_command, command_name="EndScan")
        self.obs_reset = partial(self.sim_command, command_name="ObsReset")
        self.update_subarray_membership = partial(self.sim_command, command_name="UpdateSubarrayMembership")
        self.auto_set_filter_gains = partial(self.sim_command, command_name="AutoSetFilterGains")

    @property
    def expected_dish_id(self: VccCMSim) -> str:
        return self.attribute_overrides["expectedDishId"]

    @property
    def subarray_id(self: VccCMSim) -> int:
        return self.attribute_overrides["subarrayID"]

    @property
    def frequency_band(self: VccCMSim) -> FrequencyBandEnum:
        return self.attribute_overrides["frequencyBand"]

    @property
    def input_sample_rate(self: VccCMSim) -> int:
        return self.attribute_overrides["inputSampleRate"]

    @property
    def frequency_band_offset(self: VccCMSim) -> list[int]:
        return self.attribute_overrides["frequencyBandOffset"]

    @property
    def last_requested_headrooms(self: VccCMSim) -> list[int]:
        return self.attribute_overrides["requestedRFIHeadroom"]

    @property
    def vcc_gains(self: VccCMSim) -> list[int]:
        return self.attribute_overrides["vccGains"]
