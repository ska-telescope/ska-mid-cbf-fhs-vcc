from __future__ import annotations

import tango
from overrides import override
from ska_mid_cbf_fhs_common import FhsControllerBaseDevice
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from tango.server import attribute, command

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_component_manager import VCCAllBandsComponentManager


class VCCAllBandsController(FhsControllerBaseDevice[VCCAllBandsComponentManager]):
    @property
    @override(check_signature=False)
    def component_manager_class(self) -> type[VCCAllBandsComponentManager]:
        """The component manager class associated with this controller device."""
        return VCCAllBandsComponentManager

    @property
    @override
    def extra_lrcs(self) -> list[tuple[str, str]]:
        """Any extra long-running commands defined on this device."""
        return [
            ("UpdateSubarrayMembership", "update_subarray_membership"),
            ("AutoSetFilterGains", "auto_set_filter_gains"),
        ]

    @attribute(
        dtype=str,
        doc="The expected dish ID.",
    )
    def expectedDishId(self):
        return self.component_manager.expected_dish_id

    @attribute(
        dtype=tango.DevUShort,
        doc="The subarray ID assigned to this VCC.",
        min_value=0,
        max_value=16,
    )
    def subarrayID(self):
        return self.component_manager.subarray_id

    @attribute(
        abs_change=1,
        dtype=tango.DevEnum,
        enum_labels=["1", "2", "3", "4", "5a", "5b"],
        doc="Frequency band; an int in the range [0, 5]",
    )
    def frequencyBand(self) -> tango.DevEnum:
        """
        Read the frequencyBand attribute.

        :return: the frequency band (being observed by the current scan, one of
            ["1", "2", "3", "4", "5a", "5b"]).
        :rtype: tango.DevEnum
        """
        return self.component_manager.frequency_band.value

    @attribute(
        dtype=tango.DevULong64,
        doc="The given input sample rate",
    )
    def inputSampleRate(self) -> tango.DevULong64:
        """
        Read the frequencyBand attribute.

        :return: the frequency band (being observed by the current scan, one of
            ["1", "2", "3", "4", "5a", "5b"]).
        :rtype: tango.DevEnum
        """
        return self.component_manager.input_sample_rate

    @attribute(
        dtype=tango.DevLong,
        dformat=tango.SPECTRUM,
        max_dim_x=2,
        doc="The given input sample rate",
    )
    def frequencyBandOffset(self) -> tango.DevVarLongArray:
        """
        Read the frequency band offset k, a spectrum max(len) = 2

        :return: the frequency band (being observed by the current scan, one of
            ["1", "2", "3", "4", "5a", "5b"]).
        :rtype: tango.DevLong
        """
        return self.component_manager.frequency_band_offset

    @attribute(
        dtype=(float,),
        max_dim_x=26,
        doc="The most recent requested RFI headroom values provided to AutoSetFilterGains.",
    )
    def requestedRFIHeadroom(self) -> tango.DevVarDoubleArray:
        """
        Read the requestedRFIHeadroom attribute.

        :return: the most recent requested RFI headroom values provided to AutoSetFilterGains.
        :rtype: tango.DevVarDoubleArray
        """
        return self.component_manager.last_requested_headrooms

    @attribute(
        dtype=(float,),
        max_dim_x=52,
        doc="The currently applied gain multipliers for VCC coarse channels.",
    )
    def vccGains(self) -> tango.DevVarDoubleArray:
        """
        Read the vccGains attribute.

        :return: the VCC coarse channel gain multipliers, in the format
            [ch0_polX, ch1_polX, ..., chN_polX, ch0_polY, ch1_polY, ..., chN_polY].
        :rtype: tango.DevVarDoubleArray
        """
        return self.component_manager.vcc_gains

    @attribute(
        abs_change=1,
        min_alarm=5,
        dtype=int,
        doc="Expected sample rate of the WIB",
    )
    def wibExpectedSampleRate(self) -> int:
        return self.component_manager.wideband_input_buffer.expected_sample_rate

    @wibExpectedSampleRate.write
    def wibExpectedSampleRate(self, value: int) -> None:
        self.component_manager.wideband_input_buffer.expected_sample_rate = value
        self.push_change_event("wibExpectedSampleRate", value)

    @attribute(
        dtype=str,
        doc="Expected dish ID of the WIB",
    )
    def wibExpectedDishId(self) -> str:
        return self.component_manager.wideband_input_buffer.expected_dish_id

    @wibExpectedDishId.write
    def wibExpectedDishId(self, value: str) -> None:
        self.component_manager.wideband_input_buffer.expected_dish_id = value
        self.push_change_event("wibExpectedDishId", value)

    @command(
        dtype_in="DevUShort",
        dtype_out="DevVarLongStringArray",
        doc_in="Subarray ID to assign to the VCC.",
    )
    def UpdateSubarrayMembership(self, subarray_id: int) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="UpdateSubarrayMembership")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=subarray_id)
        return [[result_code], [command_id]]

    @command(
        dtype_in=(float,),
        dtype_out="DevVarLongStringArray",
        doc_in=(
            "Requested RFI Headroom, in decibels (dB). "
            "Must be a list containing either a single value to apply to all frequency slices, "
            "or a value per frequency slice to be applied separately."
        ),
    )
    def AutoSetFilterGains(self, headroom: list[float] = [3.0]) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="AutoSetFilterGains")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=headroom)
        return [[result_code], [command_id]]


if __name__ == "__main__":
    VCCAllBandsController.run()
