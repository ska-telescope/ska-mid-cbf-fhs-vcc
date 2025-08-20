from __future__ import annotations

import tango
from ska_mid_cbf_fhs_common import FhsObsBaseDevice
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from tango.server import attribute, command, device_property

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_component_manager import VCCAllBandsComponentManager


class VCCAllBandsController(FhsObsBaseDevice):
    component_manager: VCCAllBandsComponentManager  # type hint only

    ll_props = device_property(dtype=str)

    bitstream_path = device_property(dtype="str")
    bitstream_id = device_property(dtype="str")
    bitstream_version = device_property(dtype="str")
    emulator_id = device_property(dtype="str")
    emulator_base_url = device_property(dtype="str")

    @attribute(dtype=str)
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
    def frequencyBand(self: VCCAllBandsController) -> tango.DevEnum:
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
    def inputSampleRate(self: VCCAllBandsController) -> tango.DevULong64:
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
    def frequencyBandOffset(self: VCCAllBandsController) -> tango.DevVarLongArray:
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
    def requestedRFIHeadroom(self: VCCAllBandsController) -> tango.DevVarDoubleArray:
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
    def vccGains(self: VCCAllBandsController) -> tango.DevVarDoubleArray:
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
        doc="Test top-level attribute on LL class variable",
    )
    def wibprotoTest(self) -> int:
        return self.component_manager.wideband_input_buffer.test_attr_value

    @wibprotoTest.write
    def wibprotoTest(self, value: int) -> None:
        self.component_manager.wideband_input_buffer.test_attr_value = value
        self.push_change_event("wibprotoTest", value)

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
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="Configuration json.",
    )
    def ConfigureScan(self: VCCAllBandsController, config: str) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="ConfigureScan")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=config)
        return [[result_code], [command_id]]

    @command(
        dtype_in="DevULong",
        dtype_out="DevVarLongStringArray",
        doc_in="Configuration json.",
    )
    def Scan(self: VCCAllBandsController, scan_id: int) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Scan")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=scan_id)
        return [[result_code], [command_id]]

    @command(dtype_out="DevVarLongStringArray")
    def EndScan(self: VCCAllBandsController) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="EndScan")
        result_code, command_id = command_handler()
        return [[result_code], [command_id]]

    @command(dtype_out="DevVarLongStringArray")
    def ObsReset(self: VCCAllBandsController) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="ObsReset")
        result_code, command_id = command_handler()
        return [[result_code], [command_id]]

    @command(
        dtype_in="DevUShort",
        dtype_out="DevVarLongStringArray",
        doc_in="Subarray ID to assign to the VCC.",
    )
    def UpdateSubarrayMembership(self: VCCAllBandsController, subarray_id: int) -> DevVarLongStringArrayType:
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
    def AutoSetFilterGains(self: VCCAllBandsController, headroom: list[float] = [3.0]) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="AutoSetFilterGains")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=headroom)
        return [[result_code], [command_id]]

    def create_component_manager(self: VCCAllBandsController) -> VCCAllBandsComponentManager:
        return VCCAllBandsComponentManager(
            device=self,
            logger=self.logger,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            obs_command_running_callback=self._obs_command_running,
            component_state_callback=self._component_state_changed,
            obs_state_action_callback=self._obs_state_action,
            simulation_mode=self.simulation_mode,
            emulation_mode=self.emulation_mode,
        )

    def init_command_objects(self: VCCAllBandsController) -> None:
        commands_and_methods = [
            ("GoToIdle", "go_to_idle"),  # replacement for Deconfigure
            ("ConfigureBand", "configure_band"),
            ("ConfigureScan", "configure_scan"),
            ("Scan", "scan"),
            ("EndScan", "end_scan"),
            ("ObsReset", "obs_reset"),
            ("UpdateSubarrayMembership", "update_subarray_membership"),
            ("AutoSetFilterGains", "auto_set_filter_gains"),
        ]

        super().init_command_objects(commands_and_methods)


def main(args=None, **kwargs):
    return VCCAllBandsController.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
