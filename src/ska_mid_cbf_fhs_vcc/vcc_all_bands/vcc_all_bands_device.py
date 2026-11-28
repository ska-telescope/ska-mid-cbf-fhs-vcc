from __future__ import annotations

from collections.abc import Callable
from threading import Event

import tango
from ska_control_model import ResultCode, SimulationMode, TaskStatus
from ska_mid_cbf_fhs_common import FhsControllerBaseDevice, FhsState, FloatLike
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from tango.server import attribute, command

from ska_mid_cbf_fhs_vcc import release as release_info
from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum, VCCBandGroup
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_component_manager import VCCAllBandsComponentManager
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAveragedPowerMeasurement


class VCCAllBandsController(
    FhsControllerBaseDevice[VCCAllBandsComponentManager],
):
    """Tango device class for the VCC All Bands Controller."""

    def set_local_change_events(self) -> None:
        super().set_local_change_events()
        self.set_change_event("subarrayID", True)
        self.set_archive_event("subarrayID", True)
        self.set_change_event("configurationState", True)
        self.set_archive_event("configurationState", True)

    @property
    def component_manager_class(self) -> type[VCCAllBandsComponentManager]:
        """The component manager class associated with the VCC controller device."""
        return VCCAllBandsComponentManager

    @property
    def long_running_commands(self) -> list[tuple[str, str]]:
        """:obj:`list[tuple[str, str]]`: The list of all long-running commands defined on the VCC controller,
        each a tuple of the form ("TangoCommandName", "python_method_name").
        """
        return [
            ("ConfigureScan", "configure_scan"),
            ("GoToIdle", "go_to_idle"),
            ("Abort", "abort"),
            ("UpdateSubarrayMembership", "update_subarray_membership"),
            ("ConfigureVCCBite", "configure_vcc_bite"),
            ("DeconfigureVCCBite", "deconfigure_vcc_bite"),
        ]

    @attribute(
        dtype="DevFloat",
        doc="Device's bit error rate",
    )
    def bitErrorRate(self) -> float:
        """
        Read-only Tango attribute that reads the bit error rate from the Wideband Input Buffer's IP block manager.

        :return: BER from this VCC's WIB
        :rtype: float
        """

        return self.component_manager.wideband_input_buffer.bit_error_rate

    @attribute(
        dtype="DevEnum",
        enum_labels=[FhsState.NOT_CONFIGURED.name, FhsState.CONFIGURING.name, FhsState.CONFIGURED.name, FhsState.FAULT.name],
        doc="Device's configuration state",
    )
    def configurationState(self) -> FhsState:
        """
        Read-only Tango attribute that contains the FhsState value for this device.

        Returns:
            :obj:`FhsState`: the FhsState value for this device.
        """
        return self.component_manager.configuration_state

    @attribute(
        dtype=str,
    )
    def expectedDishId(self) -> str:
        """Read-only Tango attribute specifying the expected dish ID for this VCC.

        Returns:
            :obj:`str`: The expected dish ID.
        """
        return str(self.component_manager.expected_dish_id)

    @attribute(
        abs_change=1,
        dtype=tango.DevEnum,
        enum_labels=["1", "2", "3", "4", "5a", "5b"],
    )
    def frequencyBand(self) -> FrequencyBandEnum:
        """Read-only Tango attribute specifying the frequency band in which this VCC is operating.

        Returns:
            :obj:`FrequencyBandEnum`: the frequency band enum value.
        """
        return self.component_manager.frequency_band

    @attribute(
        dtype=tango.DevLong,
        dformat=tango.SPECTRUM,
        max_dim_x=2,
    )
    def frequencyBandOffset(self) -> list[int]:
        """Read-only Tango attribute specifying the frequency band offset(s) configured for this VCC.
        Contains two offset values, however the second value is only meaningful when operating in band 5.
        Only the first value is required in all other bands.

        Returns:
            :obj:`list[int]`: the frequency band offset(s).
        """
        return self.component_manager.frequency_band_offset

    @attribute(
        dtype=tango.DevULong64,
    )
    def inputSampleRate(self) -> int:
        """Read-only Tango attribute specifying the input sample rate of this VCC.

        Returns:
            :obj:`int`: The input sample rate.
        """
        return self.component_manager.input_sample_rate

    @attribute(
        dtype=tango.DevUShort,
        abs_change=1,
        min_value=0,
        max_value=16,
    )
    def subarrayID(self) -> int:
        """Read-only Tango attribute specifying the subarray ID currently assigned to this VCC.

        Returns:
            :obj:`int`: The assigned subarray ID.
        """
        return self.component_manager.subarray_id

    @attribute(
        dtype=((float,),),
        max_dim_x=3,
        max_dim_y=2,
        doc=(
            "Current average total power of the B123 or B45a power meter (depending on current band), in dB. "
            "Format: `[[polX_pwr_nd_off, polX_pwr_nd_on, polX_pwr_total], [polY_pwr_nd_off, polY_pwr_nd_on, polY_pwr_total]]`"
        ),
    )
    def widebandPower1(self) -> list[list[FloatLike]]:
        """Read-only Tango attribute specifying the current average total power of the B123 or B45a power meter
        (depending on current band), in dB, for both the X and Y polarization.

        Returns:
            :obj:`list[list[FloatLike]]`: The current average total power of the B123 or B45a power meter, in the format:
                `[[polX_pwr_nd_off, polX_pwr_nd_on, polX_pwr_total], [polY_pwr_nd_off, polY_pwr_nd_on, polY_pwr_total]]`.
        """
        if self.component_manager.frequency_band in (FrequencyBandEnum._1, FrequencyBandEnum._2):
            measurements = self.component_manager.current_power.get(VCCBandGroup.B123, None)
        else:
            measurements = self.component_manager.current_power.get(VCCBandGroup.B45A, None)
        if measurements is None:
            return self._get_default_wideband_power()
        return [
            [measurements.x.nd_off, measurements.x.nd_on, measurements.x.total],
            [measurements.y.nd_off, measurements.y.nd_on, measurements.y.total],
        ]

    @attribute(
        dtype=((float,),),
        max_dim_x=3,
        max_dim_y=2,
        doc=(
            "Current average total power of the B5b power meter, in dB. "
            "Format: `[[polX_pwr_nd_off, polX_pwr_nd_on, polX_pwr_total], [polY_pwr_nd_off, polY_pwr_nd_on, polY_pwr_total]]`"
        ),
    )
    def widebandPower2(self) -> list[list[FloatLike]]:
        """Read-only Tango attribute specifying the current average total power of the B5b power meter,
        in dB, for both the X and Y polarization.

        Returns:
            :obj:`list[list[FloatLike]]`: The current average total power of the B5b power meter, in the format:
                `[[polX_pwr_nd_off, polX_pwr_nd_on, polX_pwr_total], [polY_pwr_nd_off, polY_pwr_nd_on, polY_pwr_total]]`.
        """
        measurements = self.component_manager.current_power.get(VCCBandGroup.B5B, None)
        if measurements is None:
            return self._get_default_wideband_power()
        return [
            [measurements.x.nd_off, measurements.x.nd_on, measurements.x.total],
            [measurements.y.nd_off, measurements.y.nd_on, measurements.y.total],
        ]

    @attribute(
        dtype=(str,),
        max_dim_x=3,
        doc="Labels for the power measurements in widebandPower1 and widebandPower2.",
    )
    def widebandLabels(self) -> list[str]:
        """Read-only Tango attribute specifying labels for the power measurements in widebandPower1 and widebandPower2.

        Returns:
            :obj:`list[str]`: The labels.
        """
        return ["Noise Diode Off", "Noise Diode On", "Total"]

    @attribute(
        dtype=((float,),),
        max_dim_x=26,
        max_dim_y=2,
        doc="FS gains in dB for X and Y polarizations. Format: `[[fs1_gain_polX, fs2_gain_polX, ...], [fs1_gain_polY, fs2_gain_polY, ...]]`",
    )
    def vccGains(self) -> list[list[FloatLike]]:
        """Read-only Tango attribute specifying the configured FS gains in dB for both the X and Y polarization.

        Returns:
            :obj:`list[list[FloatLike]]`: The configured FS gains, in the format:
                `[[fs1_gain_polX, fs2_gain_polX, ...], [fs1_gain_polY, fs2_gain_polY, ...]]`.
        """
        return self.component_manager.fs_gains

    @attribute(
        dtype=((float,),),
        max_dim_x=26,
        max_dim_y=2,
        doc=("Current average total power of each FS power meter, in dB. Format: `[[fs1_pwr_polX, fs2_pwr_polX, ...], [fs1_pwr_polY, fs2_pwr_polY, ...]]`"),
    )
    def vccPower(self) -> list[list[FloatLike]]:
        """Read-only Tango attribute specifying the current average total power of each FS power meter,
        in dB, for both the X and Y polarization.

        Returns:
            :obj:`list[list[FloatLike]]`: The current average total power of each FS power meter, in the format:
                `[[fs1_pwr_polX, fs2_pwr_polX, ...], [fs1_pwr_polY, fs2_pwr_polY, ...]]`.
        """
        return self._generate_fs_power_attr(lambda power_measurement: power_measurement.total_backed_out)

    @attribute(
        dtype=((float,),),
        max_dim_x=26,
        max_dim_y=2,
        doc=(
            "Current average noise-diode-ON power of each FS power meter, in dB. "
            "Format: `[[fs1_pwr_polX, fs2_pwr_polX, ...], [fs1_pwr_polY, fs2_pwr_polY, ...]]`"
        ),
    )
    def ndOnPower(self) -> list[list[FloatLike]]:
        """Read-only Tango attribute specifying the current average noise-diode-ON power of each FS power meter,
        in dB, for both the X and Y polarization.

        Returns:
            :obj:`list[list[FloatLike]]`: The current average noise-diode-ON power of each FS power meter, in the format:
                `[[fs1_pwr_polX, fs2_pwr_polX, ...], [fs1_pwr_polY, fs2_pwr_polY, ...]]`.
        """
        return self._generate_fs_power_attr(lambda power_measurement: power_measurement.nd_on_backed_out)

    @attribute(
        dtype=((float,),),
        max_dim_x=26,
        max_dim_y=2,
        doc=(
            "Current average noise-diode-OFF power of each FS power meter, in dB. "
            "Format: `[[fs1_pwr_polX, fs2_pwr_polX, ...], [fs1_pwr_polY, fs2_pwr_polY, ...]]`"
        ),
    )
    def ndOffPower(self) -> list[list[FloatLike]]:
        """Read-only Tango attribute specifying the current average noise-diode-OFF power of each FS power meter,
        in dB, for both the X and Y polarization.

        Returns:
            :obj:`list[list[FloatLike]]`: The current average noise-diode-OFF power of each FS power meter, in the format:
                `[[fs1_pwr_polX, fs2_pwr_polX, ...], [fs1_pwr_polY, fs2_pwr_polY, ...]]`.
        """
        return self._generate_fs_power_attr(lambda power_measurement: power_measurement.nd_off_backed_out)

    @attribute(
        dtype=((float,),),
        max_dim_x=26,
        max_dim_y=2,
        doc=("Current headroom of each FS, in dB. Format: `[[fs1_hr_x, fs2_hr_x, ...], [fs1_hr_y, fs2_hr_y, ...]]`"),
    )
    def headrooms(self) -> list[list[FloatLike]]:
        """Read-only Tango attribute specifying the current headroom of each FS, in dB, for both the X and Y polarization.

        Returns:
            :obj:`list[list[FloatLike]]`: The current headroom of each FS, in the format:
                `[[fs1_hr_x, fs2_hr_x, ...], [fs1_hr_y, fs2_hr_y, ...]]`.
        """
        return self._generate_fs_power_attr(lambda power_measurement: power_measurement.headroom)

    @attribute(
        dtype=(str,),
        doc="Mappings from FS values to VLAN IDs",
        max_dim_x=61,
    )
    def vlanLookup(self) -> list[str]:
        # For now, convert to list and return
        mapping_list = []
        for fs in self.component_manager.vlan_lookup:
            mapping_list.append(str(fs) + ": " + str(self.component_manager.vlan_lookup[fs]))
        return mapping_list

    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="Configuration JSON.",
    )
    def ConfigureScan(self, config: str) -> DevVarLongStringArrayType:
        """Tango command to apply a received scan configuration in preparation for a scan.

        Args:
            config (:obj:`str`): The configuration JSON string.

        Returns:
            :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
            message indicating status. The message is for information purpose only.
        """
        command_handler = self.get_command_object(command_name="ConfigureScan")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, message = command_handler(argin=config)
        return [result_code], [message]

    @command(dtype_in="DevString", dtype_out="DevVarLongStringArray", doc_in="JSON string following the GoToIdle schema.")
    def GoToIdle(self, go_to_idle_argin: str) -> DevVarLongStringArrayType:
        """Tango command to return the device to IDLE state.

        Args:
            go_to_idle_argin (:obj:`str`): JSON string following the GoToIdle schema.

        Returns:
            :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
            message indicating status. The message is for information purpose only.
        """
        command_handler = self.get_command_object(command_name="GoToIdle")
        result_code, message = command_handler(argin=go_to_idle_argin)
        return [result_code], [message]

    @command(
        dtype_in="DevUShort",
        dtype_out="DevVarLongStringArray",
        doc_in="Subarray ID to assign to the VCC.",
    )
    def UpdateSubarrayMembership(self, subarray_id: int) -> DevVarLongStringArrayType:
        """Tango command to update the subarray currently assigned to this VCC.

        Args:
            subarray_id (:obj:`int`): The subarray ID to assign.

        Returns:
            :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
            message indicating status. The message is for information purpose only.
        """
        command_handler = self.get_command_object(command_name="UpdateSubarrayMembership")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=subarray_id)
        return [result_code], [command_id]

    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="JSON string following the ConfigureVCCBite schema.",
    )
    def ConfigureVCCBite(self: VCCAllBandsController, configure_vcc_bite_argin: str | None = None) -> DevVarLongStringArrayType:
        """Tango command to configure VCC Bite.

        Args:
            configure_vcc_bite_argin (:obj:`str`): JSON string following the ConfigureVCCBite schema.

        Returns:
            :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
            message indicating status. The message is for information purpose only.
        """
        command_handler = self.get_command_object(command_name="ConfigureVCCBite")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=configure_vcc_bite_argin)
        return [result_code], [command_id]

    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in="JSON string following the DeconfigureVCCBite schema.",
    )
    def DeconfigureVCCBite(self: VCCAllBandsController, deconfigure_vcc_bite_argin: str | None = None) -> DevVarLongStringArrayType:
        """Tango command to deconfigure VCC Bite.

        Args:
            deconfigure_vcc_bite_argin (:obj:`str`): JSON string following the DeconfigureVCCBite schema.

        Returns:
            :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
            message indicating status. The message is for information purpose only.
        """
        command_handler = self.get_command_object(command_name="DeconfigureVCCBite")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=deconfigure_vcc_bite_argin)
        return [result_code], [command_id]

    # TODO: Currently unused. Uncomment and refactor if needed for Transient Buffer; if determined unnecessary, delete entirely.
    # @command(
    #     dtype_in="DevString",
    #     dtype_out="DevVarLongStringArray",
    #     doc_in="JSON String following the AutoSetFilterGains schema.",
    # )
    # def AutoSetFilterGains(self: VCCAllBandsController, auto_set_filter_gains_argin: str | None = None) -> DevVarLongStringArrayType:
    #     """Tango command to start a scan operation.

    #     Args:
    #         auto_set_filter_gains_argin (:obj:`str`): JSON String following the AutoSetFilterGains schema.

    #     Returns:
    #         :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
    #         message indicating status. The message is for information purpose only.
    #     """
    #     command_handler = self.get_command_object(command_name="AutoSetFilterGains")
    #     # It is important that the argin keyword be provided, as the
    #     # component manager method will be overriden in simulation mode
    #     result_code, command_id = command_handler(argin=auto_set_filter_gains_argin)
    #     return [result_code], [command_id]

    @command(
        dtype_in="DevString",
        doc_in="JSON string conforming to the ska-mid-cbf-abort schema",
        dtype_out="DevVarLongStringArray",
        doc_out=("A tuple containing a return code and a string message indicating status. The message is for information purpose only."),
    )
    def Abort(self: VCCAllBandsController, argin: str) -> DevVarLongStringArrayType:
        """
        Abort the current observing process and move to ABORTED FhsState.

        Overrides base LRC mixin to trigger FhsState transitions and component
        manager abort task.

        Returns:
            :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
            message indicating status. The message is for information purpose only.
        """
        # TODO: argin currently unused

        # Trigger task executor shutdown before submitting component manager abort
        # task to immediately clear out any tasks in progress.
        abort_tasks_event = Event()
        status, message = self.component_manager.abort_tasks(
            task_callback=lambda status, result=None: abort_tasks_event.set() if status is TaskStatus.COMPLETED else None
        )

        # Abort command succeeds if the task executor is successfully shut down
        # and restarted.
        if status is not TaskStatus.IN_PROGRESS:
            return ([ResultCode.FAILED], [message])
        if not abort_tasks_event.wait(3):
            return ([ResultCode.FAILED], ["Failed to shut down TaskExecutor"])
        return ([ResultCode.OK], ["Abort command completed OK"])

    def init_device(self) -> None:
        """Initialize the Tango device after startup."""
        super().init_device()

        self._version_id = release_info.VERSION
        self._build_state = f"{release_info.NAME}, {release_info.VERSION}, {release_info.DESCRIPTION}"

    def create_component_manager(self) -> VCCAllBandsComponentManager:
        """Instantiate the component manager for this device.

        Returns:
            :obj:`FhsControllerComponentManagerT`: The instantiated component manager.
        """
        return self.component_manager_class(
            device=self,
            logger=self.logger,
            attr_change_callback=self.push_change_event,
            attr_archive_callback=self.push_archive_event,
            health_state_callback=self._update_health_state_wrapper,
            communication_state_callback=self._communication_state_changed,
            component_state_callback=self._component_state_changed,
            simulation_mode=SimulationMode(self.simulation_mode),
            emulation_mode=bool(self.emulation_mode),
            long_running_command_result_buffer_max_size=self.long_running_command_result_buffer_max_size,
        )

    def _get_default_wideband_power(self) -> list[list[FloatLike]]:
        return [[0.0] * 3] * 2

    def _generate_fs_power_attr(self, extract_fn: Callable[[VCCAveragedPowerMeasurement], FloatLike]) -> list[list[FloatLike]]:
        output: list[list[FloatLike]] = [[], []]
        for fs in range(1, 27):
            fs_power = self.component_manager.current_power.get(fs, None)
            if fs_power is None:
                output[0].append(0.0)
                output[1].append(0.0)
            else:
                output[0].append(extract_fn(fs_power.x))
                output[1].append(extract_fn(fs_power.y))
        return output


if __name__ == "__main__":
    VCCAllBandsController.run()
