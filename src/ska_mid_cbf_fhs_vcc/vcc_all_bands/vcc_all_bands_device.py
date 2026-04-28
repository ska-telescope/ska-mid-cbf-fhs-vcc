from __future__ import annotations

import tango
from ska_control_model import ObsState
from ska_mid_cbf_fhs_common import FhsControllerBaseDevice
from ska_mid_cbf_fhs_common.state_model.fhs_obs_state import FhsObsStateMachine, FhsObsStateModel
from ska_tango_base import SKAObsDevice
from ska_tango_base.base.base_device import DevVarLongStringArrayType
from tango.server import attribute, command

from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_component_manager import VCCAllBandsComponentManager


class VCCAllBandsController(
    FhsControllerBaseDevice[VCCAllBandsComponentManager],
    SKAObsDevice,
):
    """Tango device class for the VCC All Bands Controller."""

    def set_local_change_events(self) -> None:
        super().set_local_change_events()
        self.set_change_event("subarrayID", True)
        self.set_archive_event("subarrayID", True)

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
            ("Scan", "scan"),
            ("EndScan", "end_scan"),
            ("GoToIdle", "go_to_idle"),
            ("ObsReset", "obs_reset"),
            ("UpdateSubarrayMembership", "update_subarray_membership"),
            ("AutoSetFilterGains", "auto_set_filter_gains"),
        ]

    @attribute(
        dtype=str,
    )
    def expectedDishId(self) -> str:
        """Read-only Tango attribute specifying the expected dish ID for this VCC.

        Returns:
            :obj:`str`: The expected dish ID.
        """
        return self.component_manager.expected_dish_id

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
        abs_change=1,
        dtype=tango.DevEnum,
        enum_labels=["1", "2", "3", "4", "5a", "5b"],
    )
    def frequencyBand(self) -> FrequencyBandEnum:
        """Read-only Tango attribute specifying the frequency band in which this VCC is operating.

        Returns:
            :obj:`FrequencyBandEnum`: the frequency band (being observed by the current scan, one of
            ["1", "2", "3", "4", "5a", "5b"]).
        """
        return self.component_manager.frequency_band.value

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
        dtype=(float,),
        max_dim_x=26,
    )
    def requestedRFIHeadroom(self) -> list[float]:
        """Read-only Tango attribute specifying the requested headrooms from the most recent call to AutoSetFilterGains.

        Returns:
            :obj:`list[float]`: The requested headrooms.
        """
        return self.component_manager.last_requested_headrooms

    @attribute(
        dtype=(float,),
        max_dim_x=52,
    )
    def vccGains(self) -> list[float]:
        """Read-only Tango attribute specifying the currently applied gain multipliers for VCC coarse channels.

        Returns:
            :obj:`list[float]`: The VCC coarse channel gain multipliers, in the format
            [ch0_polX, ch1_polX, ..., chN_polX, ch0_polY, ch1_polY, ..., chN_polY].
        """
        return self.component_manager.vcc_gains

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
        return [[result_code], [command_id]]

    @command(
        dtype_in="DevString",
        dtype_out="DevVarLongStringArray",
        doc_in=(
            "String containing JSON following the AutoSetFliterGains schema."
            "Requested RFI Headroom, in decibels (dB). "
            "Must be a list containing either a single value to apply to all frequency slices, "
            "or a value per frequency slice to be applied separately."
        ),
    )
    def AutoSetFilterGains(self: VCCAllBandsController, auto_set_filter_gains_schema: str | None = None) -> DevVarLongStringArrayType:
        """Tango command to start a scan operation.

        Args:
            auto_set_filter_gains_schema (:obj:`str`): JSON String following the auto set filter gains command schema
                Requested RFI headroom, in decibels (dB).
                Must be a list containing either a single value to apply to all frequency slices,
                or a value per frequency slice to be applied separately.

        Returns:
            :obj:`tuple[list[ResultCode], list[str]]`: The Tango result code and a string
            message indicating status. The message is for information purpose only.
        """
        command_handler = self.get_command_object(command_name="AutoSetFilterGains")
        # It is important that the argin keyword be provided, as the
        # component manager method will be overriden in simulation mode
        result_code, command_id = command_handler(argin=auto_set_filter_gains_schema)
        return [[result_code], [command_id]]

    def init_device(self) -> None:
        """Initialize the Tango device after startup."""
        super().init_device()
        self._update_obs_state(ObsState.IDLE)

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
            health_state_callback=self._update_health_state,
            communication_state_callback=self._communication_state_changed,
            obs_command_running_callback=self._obs_command_running,
            component_state_callback=self._component_state_changed,
            obs_state_action_callback=self._obs_state_action,
            simulation_mode=self.simulation_mode,
            emulation_mode=self.emulation_mode,
        )

    def reset_obs_state(self):
        """Set the ObsState of the device back to IDLE."""
        if self._obs_state in [ObsState.FAULT, ObsState.ABORTED]:
            self.obs_state_model.perform_action(FhsObsStateMachine.GO_TO_IDLE)

    def _init_state_model(self) -> None:
        """Set up the state model for the device."""
        super()._init_state_model()

        # supplying the reduced observing state machine defined above
        self.obs_state_model = FhsObsStateModel(
            logger=self.logger,
            callback=self._update_obs_state,
            state_machine_factory=FhsObsStateMachine,
        )

    def _obs_command_running(self, hook: str, running: bool) -> None:
        """
        Callback provided to component manager to drive the obs state model into
        transitioning states during the relevant command's submitted thread.

        Args:
            hook (:obj:`str`): the observing command-specific hook
            running (:obj:`bool`): True when thread begins, False when thread completes
        """
        action = "invoked" if running else "completed"
        self.logger.info(f"Changing ObsState from running command, calling: {hook}_{action} ")
        self.obs_state_model.perform_action(f"{hook}_{action}")

    def _obs_state_action(self, action: str) -> None:
        """Perform an action on the ObsState model."""
        self.obs_state_model.perform_action(action)

    def _update_obs_state(self, obs_state: ObsState) -> None:
        """
        Perform Tango operations in response to a change in obsState within the state machine.

        This helper method is passed to the observation state model as a
        callback, so that the model can trigger actions in the Tango
        device.

        Overridden here to supply new ObsState value to component manager property

        Args:
            obs_state (:obj:`ObsState`): the new obs_state value
        """
        self.logger.debug(f"ObsState updating to {ObsState(obs_state).name}")

        super()._update_obs_state(obs_state=obs_state)

        # set the obstate in the component_manager
        if hasattr(self, "component_manager"):
            self.component_manager.obs_state = obs_state


if __name__ == "__main__":
    VCCAllBandsController.run()
