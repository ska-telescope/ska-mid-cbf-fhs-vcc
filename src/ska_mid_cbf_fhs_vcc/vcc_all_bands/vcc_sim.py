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

import json
from dataclasses import asdict, is_dataclass
from functools import partial
from typing import Any

from ska_control_model import HealthState, ResultCode
from ska_mid_cbf_fhs_common.helpers.long_running_command_result_buffer import LongRunningCommandResult, LongRunningCommandResultBuffer
from ska_mid_cbf_fhs_common.testing.simulation import FhsObsSimMode, SimModeObsCMBase
from tango.server import attribute, run

from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

__all__ = ["SimVCCAllBandsCM", "SimVCCAllBandsController"]


# Default simulator attribute return values are initialized with this dict
VCC_SIM_DEFAULT_ATTRIBUTE_VALUES = {
    "expectedDishId": "",
    "healthState": HealthState.OK,
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
    "healthState",
}
VCC_SIM_ARCHIVE_EVENT_ATTRS = {
    "subarrayID",
    "healthState",
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

        self.enum_attrs.update({"healthState": HealthState})
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
                    "attr_change_events": {
                        "subarrayID": None,
                    },
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
        self.configure_scan = partial(self.sim_command, command_name="ConfigureScan", transaction_id="TEST_CS")
        self.scan = partial(self.sim_command, command_name="Scan", transaction_id="TEST_S")
        self.end_scan = partial(self.sim_command, command_name="EndScan", transaction_id="TEST_ES")
        self.obs_reset = partial(self.sim_command, command_name="ObsReset", transaction_id="TEST_OBS")
        self.update_subarray_membership = partial(self.sim_command, command_name="UpdateSubarrayMembership", transaction_id="TEST_USM")
        self.auto_set_filter_gains = partial(self.sim_command, command_name="AutoSetFilterGains", transaction_id="TEST_ASFG")
        self.long_running_command_result_buffer = LongRunningCommandResultBuffer(max_size=1000)

    def get_long_running_command_result(self, transaction_id: Optional[str] = None) -> tuple[ResultCode, dict[str, LongRunningCommandResult | None]]:
        """Fetch the result(s) for the LRC with the specified transaction_id.
        If the provided transaction_id is None, fetch all the stored results.
        This is the implementation for the GetLongRunningCommandResult command.

        Args:
            transaction_id (:obj:`str`): The transaction_id of the LRC.

        Returns:
            :obj:`tuple[ResultCode, dict[str, LongRunningCommandResult | None]]`: The Tango result code, and a dictionary containing
            the result(s) of the LRCs.
        """
        search_result_found, search_result = self.long_running_command_result_buffer.search(transaction_id=transaction_id)
        if search_result_found:
            command_result_code = ResultCode.OK
        else:
            command_result_code = ResultCode.UNKNOWN

        for transaction_id, lrc_result in search_result.items():
            if is_dataclass(lrc_result):
                search_result[transaction_id] = asdict(lrc_result)

        return command_result_code, search_result

    @property
    def _health_state(self: SimVCCAllBandsCM) -> HealthState:
        return self.get_attribute_override("healthState")

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
    # the below simOverrides attribute overrides the methods declared in
    # FhsSimMode from FHS Common.
    # These overrides are required to simulate attribute change event pushing,
    # which cannot be done using the base simOverrides from FhsSimMode because
    # it does not have access to the change callbacks that are only available with
    # FSPCorrController.
    # Note: Changing FhsSimMode's constructor to pass on the callbacks won't work
    # as it causes issues with Boost template matching and throws errors
    @attribute(
        dtype=str,
        doc="Attribute value overrides (JSON dict)",
    )  # type: ignore[misc]
    def simOverrides(self) -> str:
        """Read the current override configuration.

        Returns:
            :obj:`str`: JSON-encoded dictionary
        """
        return json.dumps(
            {
                "attributes": self.component_manager.attribute_overrides_queue_dict.get_all_overrides(),
                "commands": self.component_manager.command_overrides_queue_dict.get_all_overrides(),
            }
        )

    @simOverrides.write  # type: ignore[no-redef, misc]
    def simOverrides(self, value_str: str) -> None:
        """Write new override configuration. Uses `pydantic.v1.utils.deep_update` to
        only update behaviour specified in the provided dictionary.

        Args:
            value_str (:obj:`str`): JSON-encoded dict of overrides
        """
        if not self.simulation_mode:
            self.logger.error("Cannot override device behaviour in SimulationMode.FALSE.")
            return

        self.logger.info(f"Received new value for simOverrides: {value_str}")

        try:
            value_dict = json.loads(value_str)
        except json.JSONDecodeError as je:
            self.logger.error(f"{je}")
            return

        if "commands" in value_dict:
            value = value_dict["commands"]
            self.component_manager.command_overrides_queue_dict.update_all(value_dict["commands"])
        else:
            self.logger.info("No command overrides provided")

        if "attributes" in value_dict:
            for attr_name, value in value_dict["attributes"].items():
                # Convert to enum value if enum attribute
                if attr_name in self.component_manager.enum_attrs and isinstance(value, str):
                    value = self.component_manager.enum_attrs[attr_name][value]

                if isinstance(value, dict):
                    value = json.dumps(value)

                # Update attribute if value has changed
                if self.component_manager.attribute_overrides_queue_dict.peek(attr_name) != value:
                    self.component_manager.attribute_overrides_queue_dict.update(attr_name, value)
                    if attr_name in VCC_SIM_CHANGE_EVENT_ATTRS:
                        self.logger.info(f"simOverride: Pushed attribute change for {attr_name} : {value}")
                        self.push_change_event(attr_name, value)
                    if attr_name in VCC_SIM_ARCHIVE_EVENT_ATTRS:
                        self.logger.info(f"simOverride: Pushed attribute archive for {attr_name} : {value}")
                        self.push_archive_event(attr_name, value)

        else:
            self.logger.info("No attribute overrides provided")

    def create_component_manager(self: SimVCCAllBandsController) -> SimVCCAllBandsCM:
        return SimVCCAllBandsCM(
            logger=self.logger,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
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
