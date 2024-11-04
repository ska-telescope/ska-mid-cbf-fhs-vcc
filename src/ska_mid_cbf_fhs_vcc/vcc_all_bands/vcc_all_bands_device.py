from __future__ import annotations

import tango
from ska_control_model import ResultCode
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from tango.server import attribute, command, device_property

from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice, FhsFastCommand
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_component_manager import VCCAllBandsComponentManager


class VCCAllBandsController(FhsBaseDevice):
    mac_200_fqdn = device_property(dtype="str")
    packet_validation_fqdn = device_property(dtype="str")
    vcc123_channelizer_fqdn = device_property(dtype="str")
    vcc45_channelizer_fqdn = device_property(dtype="str")
    wideband_input_buffer_fqdn = device_property(dtype="str")
    wideband_frequency_shifter_fqdn = device_property(dtype="str")
    circuit_switch_fqdn = device_property(dtype="str")
    fs_selection_fqdn = device_property(dtype="str")

    @attribute
    def expectedDishId(self):
        return self.component_manager.expected_dish_id

    def create_component_manager(self: VCCAllBandsController) -> VCCAllBandsComponentManager:
        return VCCAllBandsComponentManager(
            vcc_id=self.device_id,
            mac_200_FQDN=self.mac_200_fqdn,
            packet_validation_FQDN=self.packet_validation_fqdn,
            vcc_123_channelizer_FQDN=self.vcc123_channelizer_fqdn,
            vcc_45_channelizer_FQDN=self.vcc45_channelizer_fqdn,
            wideband_input_buffer_FQDN=self.wideband_input_buffer_fqdn,
            wideband_frequency_shifter_FQDN=self.wideband_frequency_shifter_fqdn,
            circuit_switch_FQDN=self.circuit_switch_fqdn,
            fs_selection_FQDN=self.fs_selection_fqdn,
            logger=self.logger,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            obs_command_running_callback=self._obs_command_running,
            component_state_callback=self._component_state_changed,
        )

    def init_command_objects(self: VCCAllBandsController) -> None:
        commandsAndMethods = [
            ("GoToIdle", "go_to_idle"),  # replacement for Deconfigure
            ("ConfigureBand", "configure_band"),
            ("ConfigureScan", "configure_scan"),
            ("Scan", "scan"),
            ("EndScan", "end_scan"),
            ("ObsReset", "obs_reset"),  # TODO CIP-1850: has the potential to be left out if ticket is disgarded
            ("TestCmd", "test_cmd"),
        ]

        super().init_command_objects(commandsAndMethods)

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

    """
        Commands
    """

    @command(
        dtype_out="DevVarLongStringArray",
    )
    @tango.DebugIt()
    def TestCmd(self: VCCAllBandsController) -> DevVarLongStringArrayType:
        return (
            [ResultCode.OK],
            ["TEST CMD OKAY."],
        )

    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="Configuration json.",
    )
    def ConfigureScan(self: VCCAllBandsController, config: str) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="ConfigureScan")
        result_code, command_id = command_handler(config)
        return [[result_code], [command_id]]

    @command(
        dtype_in="DevULong",
        dtype_out="DevVarLongStringArray",
        doc_in="Configuration json.",
    )
    def Scan(self: VCCAllBandsController, scan_id: int) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Scan")
        result_code, command_id = command_handler(scan_id)
        return [[result_code], [command_id]]

    @command(dtype_out="DevVarLongStringArray")
    def EndScan(self: VCCAllBandsController) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="EndScan")
        result_code, command_id = command_handler()
        return [[result_code], [command_id]]

    @command(dtype_out="DevVarLongStringArray")
    def Abort(self: VCCAllBandsController) -> DevVarLongStringArrayType:
        command_handler = self.get_command_object(command_name="Abort")
        result_code, command_id = command_handler()
        return [[result_code], [command_id]]


def main(args=None, **kwargs):
    return VCCAllBandsController.run_server(args=args or None, **kwargs)


if __name__ == "__main__":
    main()
