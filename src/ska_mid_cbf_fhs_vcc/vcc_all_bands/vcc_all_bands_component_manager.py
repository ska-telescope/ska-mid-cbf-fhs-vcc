from __future__ import annotations

import logging
import os
import textwrap
import time
from collections.abc import Callable
from math import lcm
from threading import Event
from typing import TYPE_CHECKING, Any

import yaml
from ska_control_model import CommunicationStatus, HealthState, ResultCode, SimulationMode, TaskStatus
from ska_mid_cbf_common.enums.command_type import CommandType
from ska_mid_cbf_fhs_common import (
    LONG_RUNNING_COMMAND_RESULT_BUFFER_DEFAULT_MAX_SIZE,
    BaseIPBlockManager,
    FhsControllerComponentManagerBase,
    FhsState,
    FhsValidationError,
    FloatLike,
    FtileEthernetConfig,
    FtileEthernetManager,
    PollingThread,
    WidebandPowerMeterConfig,
    WidebandPowerMeterManager,
    gain_linear_to_db,
)

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_manager import (
    B123VccOsppfbChannelizerConfigureArgin,
    B123VccOsppfbChannelizerManager,
)
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_manager import FrequencySliceSelectionConfig, FrequencySliceSelectionManager
from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum, VCCBandGroup, freq_band_dict
from ska_mid_cbf_fhs_vcc.helpers.power_measurement import VCCXYPowerAccumulator
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_manager import PacketValidationManager
from ska_mid_cbf_fhs_vcc.vcc_all_bands.schemas.configure_scan import vcc_all_bands_configure_scan_schema
from ska_mid_cbf_fhs_vcc.vcc_all_bands.schemas.configure_vcc_bite import vcc_all_bands_configure_vcc_bite_schema
from ska_mid_cbf_fhs_vcc.vcc_all_bands.utils.admin_online import VccAdminOnline
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import (
    VCCAllBandsConfigureScanArgin,
    VCCAllBandsConfigureVCCBiteArgin,
    VCCAllBandsDeconfigureVCCBiteArgin,
    VCCAllBandsGoToIdleArgin,
    VCCPowerMeasurement,
    VCCPowerMeasurementResponse,
    VCCXYAveragedPowerMeasurements,
    VCCXYPowerMeasurements,
)
from ska_mid_cbf_fhs_vcc.vcc_bite.vcc_bite_manager import VCCBiteManager, VCCSourceSelect
from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_manager import VCCStreamMergeConfig, VCCStreamMergeConfigureArgin, VCCStreamMergeManager
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_manager import WidebandFrequencyShifterConfig, WidebandFrequencyShifterManager
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager import WidebandInputBufferConfig, WidebandInputBufferManager

if TYPE_CHECKING:
    from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController


class VCCAllBandsComponentManager(FhsControllerComponentManagerBase):
    """Component manager for the VCC All Bands Controller device."""

    configuration_state: FhsState
    """:obj:`FhsState`: The string representation of the device's current FhsState."""

    subarray_id: int
    """:obj:`int`: The ID of the subarray assigned to this VCC."""

    expected_dish_id: str | None
    """:obj:`int`: The ID of the dish this VCC is expecting data from."""

    frequency_band: FrequencyBandEnum
    """:obj:`FrequencyBandEnum`: The frequency band in which this VCC is operating."""

    frequency_band_offset: list[int]
    """:obj:`list[int]`: The frequency band offset(s) configured for this VCC.
    Contains two offset values, however the second value is only meaningful when operating in band 5.
    Only the first value is required in all other bands.
    """

    input_sample_rate: int
    """:obj:`int`: The input sample rate of this VCC."""

    fs_gains: list[list[FloatLike]]
    """:obj:`list[list[FloatLike]]`: FS gains in dB for X and Y polarizations. Format: [[fs1_gain_x, fs2_gain_x, ...], [fs1_gain_y, fs2_gain_y, ...]]"""

    current_power: dict[VCCBandGroup | int, VCCXYAveragedPowerMeasurements]
    """:obj:`dict[VCCBandGroup | int, VCCXYAveragedPowerMeasurements]`: Current average power measurements for all power meters."""

    vlan_lookup: dict
    """dict containing the FS to VLAN mappings, parsed from the YAML file"""

    ethernet_200g: FtileEthernetManager
    """:obj:`FtileEthernetManager`: The IP block manager for the F-tile Ethernet block."""

    b123_vcc: B123VccOsppfbChannelizerManager
    """:obj:`B123VccOsppfbChannelizerManager`: The IP block manager for the B123 Channelizer."""

    frequency_slice_selection: FrequencySliceSelectionManager
    """:obj:`FrequencySliceSelectionManager`: The IP block manager for the Frequency Slice Selection block."""

    packet_validation: PacketValidationManager
    """:obj:`PacketValidationManager`: The IP block manager for the Packet Validation block."""

    wideband_frequency_shifter: WidebandFrequencyShifterManager
    """:obj:`WidebandFrequencyShifterManager`: The IP block manager for the Wideband Frequency Shifter."""

    wideband_input_buffer: WidebandInputBufferManager
    """:obj:`WidebandInputBufferManager`: The IP block manager for the Wideband Input Buffer."""

    vcc_stream_merges: dict[int, VCCStreamMergeManager]
    """:obj:`dict[int, VCCStreamMergeManager]`: Dictionary containing the IP block managers for the two VCC Stream Merge blocks, mapped by index (1 or 2)."""

    wideband_power_meters: dict[VCCBandGroup | int, WidebandPowerMeterManager]
    """:obj:`dict[VCCBandGroup | int, WidebandPowerMeterManager]`: Dictionary containing the IP block managers
    for all Wideband Power Meters, mapped by either band group (B123, etc) or FS index (1 to 26)."""

    vcc_bite_manager: VCCBiteManager
    """:obj:`VCCBiteManager`: The manager object for VCC Bite"""

    vcc_source_select: VCCSourceSelect
    """obj:`VCCSourceSelect`: The source of VCC data"""

    @property
    def config_schema(self) -> dict[str, Any]:
        """The ConfigureScan input JSON schema for the VCC All Bands Controller."""
        return vcc_all_bands_configure_scan_schema

    @property
    def config_dataclass(self) -> type[VCCAllBandsConfigureScanArgin]:
        """The ConfigureScan input dataclass for the VCC All Bands Controller."""
        return VCCAllBandsConfigureScanArgin

    def __init__(
        self,
        *args: Any,
        device: VCCAllBandsController,
        logger: logging.Logger,
        simulation_mode: SimulationMode = SimulationMode.FALSE,
        attr_change_callback: Callable[[str, Any], None] = lambda *_, **__: None,
        attr_archive_callback: Callable[[str, Any], None] = lambda *_, **__: None,
        health_state_callback: Callable[[HealthState, dict[str, HealthState]], None] = lambda *_, **__: None,
        emulation_mode: bool = False,
        create_log_file: bool = True,
        long_running_command_result_buffer_max_size=LONG_RUNNING_COMMAND_RESULT_BUFFER_DEFAULT_MAX_SIZE,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            *args (:obj:`Any`): Any arbitrary positional arguments to pass to the superclass constructor.
            device (:obj:`FhsBaseDevice`): A reference to the controller device instance.
            logger (:obj:`logging.Logger`): A logger instance to be used by this component manager.
            simulation_mode (:obj:`SimulationMode`, optional): Whether the controller is deployed
                in simulation mode (SimulationMode.TRUE) or not (SimulationMode.FALSE).
                Default is SimulationMode.FALSE.
            attr_change_callback (:obj:`Callable[[str, Any], None]`, optional): Callback that is called when
                an attribute change event occurs. Default is an empty function.
            attr_archive_callback (:obj:`Callable[[str, Any], None]`, optional): Callback that is called when
                an attribute archive event occurs. Default is an empty function.
            health_state_callback (:obj:`Callable[[HealthState, dict[str, HealthState]], None]`, optional): Callback that is called when
                a HealthState change occurs. Default is an empty function.
            emulation_mode (:obj:`bool`, optional): Whether the controller is deployed
                in emulation mode or not. Default is False.
            create_log_file (:obj:`bool`, optional): Whether or not to create a log file for this controller. Default is True.
            **kwargs (:obj:`Any`): Any arbitrary keyword arguments to pass to the superclass init method.
        """
        self.configuration_state = FhsState.NOT_CONFIGURED

        super().__init__(
            *args,
            device=device,
            logger=logger,
            simulation_mode=simulation_mode,
            attr_change_callback=attr_change_callback,
            attr_archive_callback=attr_archive_callback,
            health_state_callback=health_state_callback,
            emulation_mode=emulation_mode,
            create_log_file=create_log_file,
            long_running_command_result_buffer_max_size=long_running_command_result_buffer_max_size,
            **kwargs,
        )
        self.device = device
        self._vcc_id = self.device.device_id

        self.admin_mode_online_check = VccAdminOnline(
            logger=self.logger,
            simulation_mode=(self.simulation_mode is SimulationMode.TRUE),
            emulator_id=self.device.emulator_id,
            emulator_port=str(self.device.emulator_port),
            emulation_mode=self.emulation_mode,
        )

        self._config_id = ""
        self._scan_id = 0
        self.subarray_id = 0
        self.expected_dish_id = None

        self._sample_rate: int = 0
        self.input_sample_rate: int = 0

        self.frequency_band: FrequencyBandEnum = FrequencyBandEnum._1
        self.frequency_band_offset: list[int] = [0, 0]

        self._num_fs = 0
        self._num_coarse_channels = 0
        self._num_coarse_channel_gains = 0

        self._fs_lanes = []
        self._coarse_channel_gains: list[float] = []
        self.fs_gains: list[list[FloatLike]] = []

        self._power_meter_measurement_intervals: dict[VCCBandGroup | int, int] = {}
        self._power_meter_measurement_accums: dict[VCCBandGroup | int, VCCXYPowerAccumulator] = {}
        self._power_meter_poll_count = 0
        self._power_meter_poll_reset = 1

        self.current_power: dict[VCCBandGroup | int, VCCXYAveragedPowerMeasurements] = {}

        self._create_power_meter_polling_thread()

        self.vcc_bite_manager = VCCBiteManager(logger=logger)
        self.vcc_source_select = VCCSourceSelect.ETHERNET_200GB

        self.vlan_lookup = {}
        vlan_mapping_file = os.getenv("VCC_PRODUCT_PATH", "/app/mnt/vcc") + "/vcc-product-definitions.yaml"
        self._parse_vlan_mapping(vlan_mapping_file)

    def _post_start_communicating_hook(self) -> None:
        """Functionality to run immediately after start_communicating (regardless of simulation mode)."""
        self.ethernet_200g.configure(FtileEthernetConfig())
        self.ethernet_200g.start()

    def _post_stop_communicating_hook(self) -> None:
        """Functionality to run immediately after stop_communicating (regardless of simulation mode)."""
        self._stop_power_meter_polling()

    def _init_ip_block_managers(self) -> list[BaseIPBlockManager[Any, Any]]:
        """Instantiate all the IP block managers for the VCC controller."""

        self.ethernet_200g = FtileEthernetManager(**self._ip_block_props("Ethernet200Gb", additional_props=["ethernet_mode"]))
        self.b123_vcc = B123VccOsppfbChannelizerManager(**self._ip_block_props("B123VccOsppfbChannelizer"))
        self.frequency_slice_selection = FrequencySliceSelectionManager(**self._ip_block_props("FrequencySliceSelection"))
        self.packet_validation = PacketValidationManager(**self._ip_block_props("PacketValidation"))
        self.wideband_frequency_shifter = WidebandFrequencyShifterManager(**self._ip_block_props("WidebandFrequencyShifter"))
        self.wideband_input_buffer = WidebandInputBufferManager(**self._ip_block_props("WidebandInputBuffer"))
        self.vcc_stream_merges: dict[int, VCCStreamMergeManager] = {i: VCCStreamMergeManager(**self._ip_block_props(f"VCCStreamMerge{i}")) for i in range(1, 3)}
        self.wideband_power_meters: dict[VCCBandGroup | int, WidebandPowerMeterManager] = {
            **{band_group: WidebandPowerMeterManager(**self._ip_block_props(f"{band_group.value.upper()}WidebandPowerMeter")) for band_group in VCCBandGroup},
            **{i: WidebandPowerMeterManager(**self._ip_block_props(f"FS{i}WidebandPowerMeter")) for i in range(1, 27)},
        }

        return [
            self.ethernet_200g,
            self.b123_vcc,
            self.frequency_slice_selection,
            self.packet_validation,
            self.wideband_frequency_shifter,
            self.wideband_input_buffer,
            *self.vcc_stream_merges.values(),
            *self.wideband_power_meters.values(),
        ]

    def set_configuration_state_if_transition_is_allowed(self, dest_state: FhsState):
        allowed_transitions = {
            FhsState.NOT_CONFIGURED: [FhsState.NOT_CONFIGURED, FhsState.CONFIGURING, FhsState.FAULT],
            FhsState.CONFIGURING: [FhsState.NOT_CONFIGURED, FhsState.CONFIGURED, FhsState.FAULT],
            FhsState.CONFIGURED: [FhsState.NOT_CONFIGURED, FhsState.CONFIGURING, FhsState.FAULT],
            FhsState.FAULT: [FhsState.FAULT],
        }

        if dest_state not in allowed_transitions[self.configuration_state]:
            raise RuntimeError(f"Tried entering state {dest_state} from {self.configuration_state} which is not allowed")

        self.configuration_state = dest_state
        self._attr_change_callback("configurationState", dest_state)
        self._attr_archive_callback("configurationState", dest_state)

    def teardown(self) -> None:
        """Reset all IP blocks and stop all active polling/monitoring."""
        self.ethernet_200g.recover()
        self.b123_vcc.recover()
        self.frequency_slice_selection.recover()
        self.packet_validation.recover()
        self.wideband_frequency_shifter.recover()
        self.wideband_input_buffer.recover()

        for vcc_stream_merge in self.vcc_stream_merges.values():
            vcc_stream_merge.recover()

        for wideband_power_meter in self.wideband_power_meters.values():
            wideband_power_meter.recover()

        self._stop_power_meter_polling()

        self.log_info("Teardown complete.")

    def configure_scan(
        self,
        argin: str,
        task_callback: Callable,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the ConfigureScan command implementation.

        Args:
            argin (:obj:`str`): The configuration JSON string from the command's input argument.
            task_callback (:obj:`Callable`): A callback to run when the task status changes.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=self._configure_scan,
            args=[argin],
            task_callback=task_callback,
        )

    def go_to_idle(
        self,
        argin: str,
        task_callback: Callable,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the GoToIdle command implementation.

        Args:
            argin (:obj:`str`): The input JSON string to the GoToIdle command.
            task_callback (:obj:`Callable`): A callback to run when the task status changes.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=self._go_to_idle,
            args=[argin],
            task_callback=task_callback,
        )

    def update_subarray_membership(
        self: VCCAllBandsComponentManager,
        argin: int,
        task_callback: Callable,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the UpdateSubarrayMembership command implementation.

        Args:
            argin (:obj:`int`): The subarray ID.
            task_callback (:obj:`Callable`): A callback to run when the task status changes.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=self._update_subarray_membership,
            args=[argin],
            task_callback=task_callback,
        )

    # TODO: Currently unused. Uncomment and refactor if needed for Transient Buffer; if determined unnecessary, delete entirely.
    # def auto_set_filter_gains(
    #     self: VCCAllBandsComponentManager,
    #     argin: str,
    #     task_callback: Callable,
    # ) -> tuple[TaskStatus, str]:
    #     """Submit the task to start running the AutoSetFilterGains command implementation.

    #     Args:
    #         argin (:obj:`str`): JSON String following the auto set filter gains command schema
    #             Requested RFI headroom, in decibels (dB).
    #             Must be a list containing either a single value to apply to all frequency slices,
    #             or a value per frequency slice to be applied separately.
    #         task_callback (:obj:`Callable`): A callback to run when the task status changes.

    #     Returns:
    #         :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
    #     """
    #     return self.submit_task(
    #         func=self._auto_set_filter_gains,
    #         args=[argin],
    #         task_callback=task_callback,
    #     )

    def configure_vcc_bite(
        self,
        argin: str,
        task_callback: Callable,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the ConfigureVCCBite command implementation.

        Args:
            argin (:obj:`str`): The input JSON string to the ConfigureVCCBite command.
            task_callback (:obj:`Callable`): A callback to run when the task status changes.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=self._configure_vcc_bite,
            args=[argin],
            task_callback=task_callback,
        )

    def deconfigure_vcc_bite(
        self,
        argin: str,
        task_callback: Callable,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the DeconfigureVCCBite command implementation.

        Args:
            argin (:obj:`str`): The input JSON string to the DeconfigureVCCBite command.
            task_callback (:obj:`Callable`): A callback to run when the task status changes.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=self._deconfigure_vcc_bite,
            args=[argin],
            task_callback=task_callback,
        )

    def abort_tasks(
        self,
        task_callback: Callable,
    ) -> tuple[TaskStatus, str]:
        """
        Run a task to abort all commands and stop any started IP blocks.

        Args:
            task_callback (:obj:`Callable`): A callback to pass to the superclass
                to be run when the task status changes.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        task_status, msg = super().abort_tasks(task_callback)

        return task_status, msg

    def _configure_scan(
        self,
        argin: str,
        task_callback: Callable,
        task_abort_event: Event,
    ) -> None:
        """Wrapper for the ConfigureScan command implementation for all controllers,
        to handle task management as well as error handling.
        """
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)
            if self.task_abort_event_is_set("ConfigureScan", task_callback, task_abort_event):
                return

            # Note: We do manual JSON validation here as we have a dedicated schema for it
            self.set_configuration_state_if_transition_is_allowed(FhsState.CONFIGURING)
            configuration = self.config_dataclass.from_validated_json(argin, additional_schema=self.config_schema)
            transaction_id = configuration.transaction_id
            self.transaction_ids_per_command[CommandType.CONFIGURESCAN] = transaction_id

            # stop power meter polling if currently running to safely change power meter configs
            self._stop_power_meter_polling()

            # WIB must be stopped prior to reconfiguration if the sample rate changed
            wib_stop_required = configuration.dish_sample_rate != self._sample_rate and self._sample_rate != 0
            self._sample_rate = configuration.dish_sample_rate
            self.frequency_band = freq_band_dict()[configuration.frequency_band]
            self.expected_dish_id = configuration.expected_dish_id
            self._config_id = configuration.config_id
            self.frequency_band_offset[0] = configuration.frequency_band_offset_stream1
            self.frequency_band_offset[1] = configuration.frequency_band_offset_stream2

            self.log_info(f"Configuring VCC {self._vcc_id} - Config ID: {self._config_id}, Freq Band: {self.frequency_band.value}", transaction_id)

            match self.frequency_band:
                case FrequencyBandEnum._1 | FrequencyBandEnum._2:
                    self._num_fs = 10
                    self._num_coarse_channels = 10
                case FrequencyBandEnum._3 | FrequencyBandEnum._4:
                    self._reset_data()
                    raise ValueError("Bands 3/4 not implemented")
                    # self._num_fs = 15
                    # self._num_cc_gains = 30
                case _:
                    self._num_fs = 26
                    self._num_coarse_channels = 30
                    self._num_coarse_channel_gains = 60

            self._num_coarse_channel_gains = self._num_coarse_channels * 2
            if len(configuration.vcc_gains_stream_1) != self._num_coarse_channel_gains:
                self._reset_data()
                raise ValueError(f"Incorrect number of gain values supplied: {configuration.vcc_gains_stream_1} != {self._num_coarse_channel_gains}")

            cc_fs_idxs = range(self._num_fs)  # TODO: placeholder until coarse channel idx -> fs_id mapping is known
            self._coarse_channel_gains = configuration.vcc_gains_stream_1
            self.fs_gains = [
                [gain_linear_to_db(configuration.vcc_gains_stream_1[i]) for i in cc_fs_idxs],
                [gain_linear_to_db(configuration.vcc_gains_stream_1[self._num_coarse_channels + i]) for i in cc_fs_idxs],
            ]

            # VCC123 Channelizer Configuration
            self.log_debug("VCC123 Channelizer Configuring..", transaction_id)
            # TODO: simulation mode check temporary to allow certain unit testing until 30-channel VCC driver/emulator implemented
            if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2} or self.simulation_mode is SimulationMode.TRUE:
                result = self.b123_vcc.configure(
                    B123VccOsppfbChannelizerConfigureArgin(sample_rate=self._sample_rate, gains=self._coarse_channel_gains, transaction_id=transaction_id)
                )

                if result == 1:
                    self.log_error("Configuration of VCC123 Channelizer failed.", transaction_id)
                    self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                    self._reset_data()
                    raise RuntimeError("Configuration of VCC123 failed.")

            else:
                # TODO: Implement routing to the 5 Channelizer once outlined
                self._reset_data()
                raise ValueError(f"ConfigureScan failed unsupported band specified: {self.frequency_band}")

            # WFS Configuration
            self.log_debug("Wideband Frequency Shifter Configuring..", transaction_id)
            result = self.wideband_frequency_shifter.configure(
                WidebandFrequencyShifterConfig(shift_frequency=self.frequency_band_offset[0], transaction_id=transaction_id)
            )
            if result == 1:
                self.log_error("Configuration of Wideband Frequency Shifter failed.", transaction_id)
                self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                self._reset_data()
                raise RuntimeError("Configuration of Wideband Frequency Shifter failed.")

            # FSS Configuration
            result = self.frequency_slice_selection.configure(
                FrequencySliceSelectionConfig(
                    band_select=self.frequency_band.value + 1,
                    band_start_channel=[0, 1],
                    transaction_id=transaction_id,
                )
            )

            if result == 1:
                self.log_error("Configuration of FS Selection failed.", transaction_id)
                self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                self._reset_data()
                raise RuntimeError("Configuration of FS Selection failed.")

            # WIB Configuration
            if wib_stop_required and self.wideband_input_buffer.stop().await_result() == 1:
                self.log_error("ConfigureScan failed: WIB stop() failed.", transaction_id)
                self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                self._reset_data()
                raise RuntimeError("ConfigureScan failed: WIB stop() failed.")

            self.log_debug("Wideband Input Buffer Configuring..", transaction_id)
            result = self.wideband_input_buffer.configure(
                WidebandInputBufferConfig(
                    transaction_id=transaction_id,
                    expected_sample_rate=self._sample_rate,
                    noise_diode_transition_holdoff_count=configuration.noise_diode_transition_holdoff_count,
                    expected_dish_band=self.frequency_band.value + 1,  # FW Drivers rely on integer indexes, that are 1-based
                )
            )

            if result == 1:
                self.log_error("Configuration of WIB failed.", transaction_id)
                self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                self._reset_data()
                raise RuntimeError("Configuration of WIB failed.")

            self.wideband_input_buffer.expected_dish_id = self.expected_dish_id

            # Wideband Power Meter Configuration
            self.log_debug("Wideband Power Meters Configuring..", transaction_id)
            for band_group, config in (
                (VCCBandGroup.B123, configuration.b123_power_meter),
                (VCCBandGroup.B45A, configuration.b45_1_power_meter),
                (VCCBandGroup.B5B, configuration.b45_2_power_meter),
            ):
                self.log_debug(f"Configuring {band_group.value} power meter with {config}", transaction_id)
                self._power_meter_measurement_intervals[band_group] = config.averaging
                self._power_meter_measurement_accums[band_group] = VCCXYPowerAccumulator()  # all 0
                result = self.wideband_power_meters[band_group].configure(
                    WidebandPowerMeterConfig(
                        transaction_id=transaction_id,
                        averaging_time=1,
                        flagging=config.flagging,
                        sample_rate=self._sample_rate,
                    )
                )
                if result == 1:
                    self.log_error(f"Configuration of {band_group.value} Wideband Power Meter failed.", transaction_id)
                    self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                    self._reset_data()
                    raise RuntimeError(f"Configuration of {band_group.value} Wideband Power Meter failed.")

            # FS Power Meter Configuration
            self.log_debug("FS Power Meters Configuring..", transaction_id)
            self._fs_lanes = configuration.fs_lanes

            # Verify vlan_alias is within the provided keys and result is in range
            for config in self._fs_lanes:
                if config.vlan_alias in self.vlan_lookup:
                    if not (2 <= self.vlan_lookup[config.vlan_alias] <= 1001 or 1006 <= self.vlan_lookup[config.vlan_alias] <= 4094):
                        raise ValueError(f"VLAN ID {self.vlan_lookup[config.vlan_alias]} for alias {config.vlan_alias} is not within range")
                else:
                    raise KeyError(f"Could not find the requested vlan_alias ({config.vlan_alias}) in the VLAN mapping provided")

            for config in self._fs_lanes:
                fs_id = int(config.fs_id)
                self.log_debug(f"Configuring FS {fs_id} power meter with {config}", transaction_id)
                self._power_meter_measurement_intervals[fs_id] = config.power_meter.averaging
                self._power_meter_measurement_accums[fs_id] = VCCXYPowerAccumulator()
                result = self.wideband_power_meters[fs_id].configure(
                    WidebandPowerMeterConfig(
                        transaction_id=transaction_id,
                        averaging_time=1,
                        flagging=config.power_meter.flagging,
                        sample_rate=self._sample_rate,
                    )
                )
                if result == 1:
                    self.log_error(f"Configuration of FS {fs_id} Wideband Power Meter failed.", transaction_id)
                    self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                    self._reset_data()
                    raise RuntimeError(f"Configuration of FS {fs_id} Wideband Power Meter failed.")

            self._power_meter_poll_reset = lcm(*self._power_meter_measurement_intervals.values())

            # VCC Stream Merge Configuration
            self.log_debug("VCC Stream Merge Configuring..", transaction_id)
            for i in range(1, 3):
                result = self.vcc_stream_merges[i].configure(
                    VCCStreamMergeConfigureArgin(
                        transaction_id=transaction_id,
                        fs_lane_configs=[
                            VCCStreamMergeConfig(
                                mac_destination=0,  # TODO?
                                vid=self.vlan_lookup[lane.vlan_alias],
                                vcc_id=self._vcc_id,
                                fs_id=lane.fs_id,
                                fs_index=fs_index,
                            )
                            for fs_index, lane in enumerate(self._fs_lanes[13 * (i - 1) : 13 * i])
                        ],
                    )
                )  # fmt: skip
                if result == 1:
                    self.log_error("Configuration of VCC Stream Merge failed.", transaction_id)
                    self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
                    self._reset_data()
                    raise RuntimeError("Configuration of VCC Stream Merge failed.")

            self.wideband_input_buffer.start().await_result()
            self._start_power_meter_polling()

            self.set_configuration_state_if_transition_is_allowed(FhsState.CONFIGURED)
            self.log_info(f"Sucessfully completed ConfigureScan for Config ID: {self._config_id}", transaction_id)
            self.long_running_command_result_buffer.insert(command_type=CommandType.CONFIGURESCAN, result_code=ResultCode.OK, transaction_id=transaction_id)
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ConfigureScan completed OK")
        except FhsValidationError as exc:
            self.set_configuration_state_if_transition_is_allowed(FhsState.NOT_CONFIGURED)
            transaction_id = exc.data.get("transaction_id", None) or self.transaction_ids_per_command.get(CommandType.CONFIGURESCAN, None)
            self.log_exception("JSON validation failed for ConfigureScan", transaction_id)
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.CONFIGURESCAN, result_code=ResultCode.REJECTED, transaction_id=transaction_id
            )
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for ConfigureScan")
        except Exception as exc:
            self.set_configuration_state_if_transition_is_allowed(FhsState.NOT_CONFIGURED)
            transaction_id = self.transaction_ids_per_command.get(CommandType.CONFIGURESCAN, None)
            self.log_exception("An unexpected exception occurred during ConfigureScan.", transaction_id)
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            self.long_running_command_result_buffer.insert(command_type=CommandType.CONFIGURESCAN, result_code=ResultCode.FAILED, transaction_id=transaction_id)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during ConfigureScan: {exc}", width=400),
            )
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.CONFIGURESCAN] = None

    def _go_to_idle(
        self,
        argin: str,
        task_callback: Callable,
        task_abort_event: Event,
    ) -> None:
        """GoToIdle command implementation for all controllers."""
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)
            if self.task_abort_event_is_set("GoToIdle", task_callback, task_abort_event):
                return

            go_to_idle_argin = VCCAllBandsGoToIdleArgin.from_validated_json(argin)
            transaction_id = go_to_idle_argin.transaction_id
            self.transaction_ids_per_command[CommandType.GOTOIDLE] = transaction_id
            self.log_info("Received Command GoToIdle", transaction_id)

            self._stop_power_meter_polling()
            self._deconfigure_ip_blocks(self.subarray_id, transaction_id)
            self._reset_data()  # configurationState is set to NOT_CONFIGURED here

            self.log_info("Command GoToIdle Successful", transaction_id)
            self.long_running_command_result_buffer.insert(command_type=CommandType.GOTOIDLE, result_code=ResultCode.OK, transaction_id=transaction_id)
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "GoToIdle completed OK")
        except FhsValidationError as exc:
            transaction_id = exc.data.get("transaction_id", None) or self.transaction_ids_per_command.get(CommandType.GOTOIDLE, None)
            self.log_exception("JSON validation failed for GoToIdle", transaction_id)
            self.long_running_command_result_buffer.insert(command_type=CommandType.GOTOIDLE, result_code=ResultCode.REJECTED, transaction_id=transaction_id)
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for GoToIdle")
        except Exception as exc:
            transaction_id = self.transaction_ids_per_command.get(CommandType.GOTOIDLE, None)
            self.log_exception("An unexpected exception occurred during GoToIdle", transaction_id)
            self.long_running_command_result_buffer.insert(command_type=CommandType.GOTOIDLE, result_code=ResultCode.FAILED, transaction_id=transaction_id)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during GoToIdle: {exc}", width=400),
            )
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.GOTOIDLE] = None

    def _update_subarray_membership(
        self,
        argin: int,
        task_callback: Callable,
        task_abort_event: Event,
    ) -> None:
        """Update subarray membership for this VCC. This is the implementation for the UpdateSubarrayMembership command.

        Args:
            argin (:obj:`int`): Subarray ID to assign to this VCC. Set to 0 to unassign the currently assigned subarray.
            task_callback (:obj:`Callable | None`, optional): A callback to run when the task status changes. Default is None.
            task_abort_event (:obj:`Event | None`, optional): An event representing whether or not the task has aborted.
                Default is None.
        """
        try:
            if argin < 0 or argin > 16:
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.REJECTED,
                    f"Cannot update subarray membership as the provided ID {self.subarray_id} is not in the range 0-16.",
                )
            elif self.subarray_id > 0 and argin > 0:
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.REJECTED,
                    f"Cannot update subarray membership as this VCC is already assigned to subarray {self.subarray_id}.",
                )
            else:
                self.subarray_id = argin
                self._attr_change_callback("subarrayID", argin)
                self._attr_archive_callback("subarrayID", argin)
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.OK,
                    "UpdateSubarrayMembership completed OK",
                )
        except Exception as exc:
            self.log_exception("An unexpected exception occurred during UpdateSubarrayMembership.")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during UpdateSubarrayMembership: {exc}", width=400),
            )

    # TODO: Currently unused. Uncomment and refactor if needed for Transient Buffer; if determined unnecessary, delete entirely.
    # def _auto_set_filter_gains(
    #     self,
    #     argin: str,
    #     task_callback: Callable,
    #     task_abort_event: Event,
    # ) -> None:
    #     """Calculate and apply optimal gain multipliers for VCC coarse channels.
    #     This is the implementation for the AutoSetFilterGains command.

    #     Args:
    #         argin (:obj:`str`): JSON String following the auto set filter gains command schema
    #             Requested RFI headroom, in decibels (dB).
    #             Must be a list containing either a single value to apply to all frequency slices,
    #             or a value per frequency slice to be applied separately.
    #         task_callback (:obj:`Callable | None`, optional): A callback to run when the task status changes. Default is None.
    #         task_abort_event (:obj:`Event | None`, optional): An event representing whether or not the task has aborted.
    #             Default is None.
    #     """
    #     try:
    #         headrooms = [3.0]
    #         transaction_id = None

    #         if argin:
    #             auto_set_filter_gains_argin = VCCAllBandsAutoSetFilterGainsArgin.from_validated_json(argin)
    #             transaction_id = auto_set_filter_gains_argin.transaction_id
    #             self.transaction_ids_per_command[CommandType.AUTOSETFILTERGAINS] = transaction_id
    #             if auto_set_filter_gains_argin.headrooms is not None:
    #                 headrooms = auto_set_filter_gains_argin.headrooms

    #         self.log_info("Received Command AutoSetFilterGains", transaction_id)

    #         if (num_headrooms := len(headrooms)) not in [1, self._num_fs]:
    #             self._set_task_callback(
    #                 task_callback,
    #                 TaskStatus.COMPLETED,
    #                 ResultCode.REJECTED,
    #                 f"Cannot auto-set gains as the input headroom {headrooms} is invalid.",
    #             )
    #             self.long_running_command_result_buffer.insert(
    #                 command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.REJECTED, transaction_id=transaction_id
    #             )
    #             return

    #         new_gains = copy.copy(self.vcc_gains)

    #         # Read all power meters
    #         for i in range(self._num_fs):
    #             # Read power
    #             try:
    #                 status = self.wideband_power_meters[i + 1].status()
    #             except Exception:
    #                 msg = f"Failed to auto-set gains: Failed to retrieve status from the FS {i + 1} power meter."
    #                 self.log_exception(msg, transaction_id)
    #                 self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.FAILED, msg)
    #                 self.long_running_command_result_buffer.insert(
    #                     command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
    #                 )
    #                 return
    #             measured_power_pol_x = status.avg_power_pol_x
    #             measured_power_pol_y = status.avg_power_pol_y

    #             for power, pol in (measured_power_pol_x, "X"), (measured_power_pol_y, "Y"):
    #                 if not isinstance(power, (int, float)) or isinstance(power, bool) or isnan(power) or power <= 0 or power > 1:
    #                     self._set_task_callback(
    #                         task_callback,
    #                         TaskStatus.COMPLETED,
    #                         ResultCode.FAILED,
    #                         (f"Failed to auto-set gains: The FS {i + 1} power meter failed to provide a valid power measurement for polarization {pol}."),
    #                     )
    #                     self.long_running_command_result_buffer.insert(
    #                         command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
    #                     )
    #                     return

    #             headroom = headrooms[i % num_headrooms]

    #             # Convert to multiplier
    #             new_gains[i] = float(calculate_gain_multiplier(0.0, measured_power_pol_x, headroom))
    #             new_gains[i + self._num_fs] = float(calculate_gain_multiplier(0.0, measured_power_pol_y, headroom))

    #         # Reconfigure VCCs
    #         if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
    #             result = self.b123_vcc.configure(
    #                 B123VccOsppfbChannelizerConfigureArgin(
    #                     transaction_id=transaction_id,
    #                     sample_rate=self._sample_rate,
    #                     gains=new_gains,
    #                 )
    #             )

    #             if result == 1:
    #                 self.log_error("Failed to reconfigure VCC123 Channelizer with new gain values.", transaction_id)
    #                 self.b123_vcc.configure(
    #                     B123VccOsppfbChannelizerConfigureArgin(
    #                         transaction_id=transaction_id,
    #                         sample_rate=self._sample_rate,
    #                         gains=self.vcc_gains,
    #                     )
    #                 )
    #                 self._set_task_callback(
    #                     task_callback,
    #                     TaskStatus.COMPLETED,
    #                     ResultCode.FAILED,
    #                     "Failed to auto-set gains: failed to reconfigure VCC123 Channelizer with new gain values.",
    #                 )
    #                 self.long_running_command_result_buffer.insert(
    #                     command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
    #                 )
    #                 return

    #         else:
    #             # TODO: Implement routing to the 5 Channelizer once outlined
    #             self.long_running_command_result_buffer.insert(
    #                 command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
    #             )
    #             self._set_task_callback(
    #                 task_callback,
    #                 TaskStatus.COMPLETED,
    #                 ResultCode.FAILED,
    #                 "Failed to auto-set gains: currently selected frequency band is not supported.",
    #             )
    #             return
    #         # Update vccGains and publish change
    #         self.vcc_gains = new_gains
    #         self.last_requested_headrooms = headrooms

    #         self.log_info(f"Successfully set Autofilter gains with headrooms {headrooms}", transaction_id)

    #         self.long_running_command_result_buffer.insert(
    #             command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.OK, transaction_id=transaction_id
    #         )
    #         self._set_task_callback(
    #             task_callback,
    #             TaskStatus.COMPLETED,
    #             ResultCode.OK,
    #             "AutoSetFilterGains completed OK",
    #         )
    #     except FhsValidationError as exc:
    #         transaction_id = exc.data.get("transaction_id", None) or self.transaction_ids_per_command.get(CommandType.AUTOSETFILTERGAINS, None)
    #         self.log_exception("JSON validation failed for AutoSetFilterGains", transaction_id)
    #         self.long_running_command_result_buffer.insert(
    #             command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.REJECTED, transaction_id=transaction_id
    #         )
    #         self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for AutoSetFilterGains")
    #     except Exception as exc:
    #         transaction_id = self.transaction_ids_per_command.get(CommandType.AUTOSETFILTERGAINS, None)
    #         self.log_exception("An unexpected exception occurred during AutoSetFilterGains.", transaction_id)
    #         self.long_running_command_result_buffer.insert(
    #             command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
    #         )
    #         self._set_task_callback(
    #             task_callback,
    #             TaskStatus.COMPLETED,
    #             ResultCode.FAILED,
    #             textwrap.shorten(f"An unexpected exception occurred during AutoSetFilterGains: {exc}", width=400),
    #         )
    #     finally:
    #         # Reset the ID so it's not used in a different Command call
    #         self.transaction_ids_per_command[CommandType.AUTOSETFILTERGAINS] = None

    def _configure_vcc_bite(
        self,
        argin: str,
        task_callback: Callable,
        task_abort_event: Event,
    ) -> None:
        """ConfigureVCCBite command implementation for VCC All bands controller,
        to handle task management as well as error handling.
        """
        try:
            configure_vcc_bite_argin = VCCAllBandsConfigureVCCBiteArgin.from_validated_json(
                argin,
                additional_schema=vcc_all_bands_configure_vcc_bite_schema,
            )
            transaction_id = configure_vcc_bite_argin.transaction_id
            self.transaction_ids_per_command[CommandType.CONFIGUREVCCBITE] = transaction_id

            self.log_info("Received Command ConfigureVCCBite", transaction_id)

            self.vcc_bite_manager.configure(config=configure_vcc_bite_argin)
            self.vcc_source_select = VCCSourceSelect.VCC_BITE

            self.long_running_command_result_buffer.insert(command_type=CommandType.CONFIGUREVCCBITE, result_code=ResultCode.OK, transaction_id=transaction_id)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.OK,
                "ConfigureVCCBite completed OK",
            )
        except FhsValidationError as exc:
            transaction_id = exc.data.get("transaction_id", None) or self.transaction_ids_per_command.get(CommandType.CONFIGUREVCCBITE, None)
            self.log_exception("Invalid json provided for ConfigureVCCBite", transaction_id)
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.CONFIGUREVCCBITE, result_code=ResultCode.REJECTED, transaction_id=transaction_id
            )
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for ConfigureVCCBite")
        except Exception as exc:
            transaction_id = self.transaction_ids_per_command.get(CommandType.CONFIGUREVCCBITE, None)
            self.log_exception("An unexpected exception occurred during ConfigureVCCBite.", transaction_id)
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.CONFIGUREVCCBITE, result_code=ResultCode.FAILED, transaction_id=transaction_id
            )
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during ConfigureVCCBite: {exc}", width=400),
            )
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.CONFIGUREVCCBITE] = None

    def _deconfigure_vcc_bite(
        self,
        argin: str,
        task_callback: Callable,
        task_abort_event: Event,
    ) -> None:
        """DeconfigureVCCBite command implementation for VCC All bands controller,
        to handle task management as well as error handling.
        """
        try:
            deconfigure_vcc_bite_argin = VCCAllBandsDeconfigureVCCBiteArgin.from_validated_json(argin)
            transaction_id = deconfigure_vcc_bite_argin.transaction_id
            self.transaction_ids_per_command[CommandType.DECONFIGUREVCCBITE] = transaction_id

            self.log_info("Received Command DeconfigureVCCBite", transaction_id)

            self.vcc_bite_manager.deconfigure(config=deconfigure_vcc_bite_argin)
            self.vcc_source_select = VCCSourceSelect.ETHERNET_200GB

            self.long_running_command_result_buffer.insert(
                command_type=CommandType.DECONFIGUREVCCBITE, result_code=ResultCode.OK, transaction_id=transaction_id
            )
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.OK,
                "DeconfigureVCCBite completed OK",
            )
        except FhsValidationError as exc:
            transaction_id = exc.data.get("transaction_id", None) or self.transaction_ids_per_command.get(CommandType.DECONFIGUREVCCBITE, None)
            self.log_exception("Invalid json provided for DeconfigureVCCBite", transaction_id)
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.DECONFIGUREVCCBITE, result_code=ResultCode.REJECTED, transaction_id=transaction_id
            )
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for DeconfigureVCCBite")
        except Exception as exc:
            transaction_id = self.transaction_ids_per_command.get(CommandType.DECONFIGUREVCCBITE, None)
            self.log_exception("An unexpected exception occurred during DeconfigureVCCBite.", transaction_id)
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.DECONFIGUREVCCBITE, result_code=ResultCode.FAILED, transaction_id=transaction_id
            )
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during DeconfigureVCCBite: {exc}", width=400),
            )
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.DECONFIGUREVCCBITE] = None

    def _reset_data(self) -> None:
        """Reset all attributes and other data."""
        self.set_configuration_state_if_transition_is_allowed(FhsState.NOT_CONFIGURED)
        self._config_id = ""
        self._scan_id = 0
        self.frequency_band = FrequencyBandEnum._1
        self.frequency_band_offset = [0, 0]
        self._sample_rate = 0
        self._fs_lanes = []

    def _deconfigure_ip_blocks(self, subarray_id: int, transaction_id: str | None = None) -> None:
        """Deconfigure all ip blocks"""

        # VCC123 Channelizer Deconfiguration
        if self.b123_vcc.deconfigure() == 1:
            self.log_error("Deconfiguration of VCC123 Channelizer failed.", transaction_id)
            raise RuntimeError("Deconfiguration of VCC123 failed.")

        # WFS Deconfiguration
        if self.wideband_frequency_shifter.deconfigure() == 1:
            self.log_error("Deconfiguration of Wideband Frequency Shifter failed.", transaction_id)
            raise RuntimeError("Deconfiguration of Wideband Frequency Shifter failed.")

        # FSS Deconfiguration
        if self.frequency_slice_selection.deconfigure() == 1:
            self.log_error("Deconfiguration of FS Selection failed.", transaction_id)
            raise RuntimeError("Deconfiguration of FS Selection failed.")

        # WIB Deconfiguration
        if self.wideband_input_buffer.deconfigure() == 1:
            self.log_error("Deconfiguration of WIB failed.", transaction_id)
            raise RuntimeError("Deconfiguration of WIB failed.")

        # Pre-channelizer WPM Deconfiguration
        for band_group in VCCBandGroup:
            if self.wideband_power_meters[band_group].deconfigure() == 1:
                self.log_error(f"Deconfiguration of {band_group.value} Wideband Power Meter failed.", transaction_id)
                raise RuntimeError(f"Deconfiguration of {band_group.value} Wideband Power Meter failed.")

        # Post-channelizer WPM Deconfiguration
        for config in self._fs_lanes:
            fs_id = int(config.fs_id)
            if self.wideband_power_meters[fs_id].deconfigure() == 1:
                self.log_error(f"Deconfiguration of FS {fs_id} Wideband Power Meter failed.", transaction_id)
                raise RuntimeError(f"Deconfiguration of FS {fs_id} Wideband Power Meter failed.")

        # VCC Stream Merge Deconfiguration
        for i in range(1, 3):
            if self.vcc_stream_merges[i].deconfigure() == 1:
                self.log_error(f"Deconfiguration of VCC Stream Merge {i} failed.", transaction_id)
                raise RuntimeError(f"Deconfiguration of VCC Stream Merge {i} failed.")

        self.log_info("Sucessfully deconfigured all IP Blocks", transaction_id)

    def _create_power_meter_polling_thread(self) -> None:
        """Create the polling thread which retrieves power measurements from the various power meters."""
        self._power_meter_poll_count = 0
        self._power_meter_polling_thread = PollingThread(
            poll_interval=1.0,
            poll_body=self._power_meter_poll_body,
            poll_exc_body=self._power_meter_poll_exc_body,
            name="VCCPowerMeterPollingThread",
        )

    def _recreate_power_meter_polling_thread(self) -> None:
        """Recreate the polling thread which retrieves power measurements from the various power meters."""
        if self._power_meter_polling_thread.is_alive():
            self._power_meter_polling_thread.stop()
        self._create_power_meter_polling_thread()

    def _start_power_meter_polling(self) -> None:
        """Start the polling thread which retrieves power measurements from the various power meters."""
        self.logger.info("Starting power meter polling...")
        self._power_meter_polling_thread.start()

    def _stop_power_meter_polling(self) -> None:
        """Stop the polling thread which retrieves power measurements from the various power meters."""
        if self._power_meter_polling_thread.is_alive():
            self.logger.info("Stopping power meter polling...")
            self._power_meter_polling_thread.stop()
        self._recreate_power_meter_polling_thread()

    def _power_meter_poll_body(self) -> bool | None:
        """Retrieve power measurements from the various power meters."""
        if self.configuration_state is not FhsState.CONFIGURED:
            return

        if self.emulation_mode or self.simulation_mode is SimulationMode.TRUE:
            power_measurements_response = self._read_simulated_emulated_power()
        else:
            # TODO: placeholder, get from gRPC
            power_measurements_response: VCCPowerMeasurementResponse = VCCPowerMeasurementResponse(
                b123=VCCXYPowerMeasurements(
                    x=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                    y=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                    weight=1.0,
                ),
                b45a=VCCXYPowerMeasurements(
                    x=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                    y=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                    weight=1.0,
                ),
                b5b=VCCXYPowerMeasurements(
                    x=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                    y=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                    weight=1.0,
                ),
                fs={
                    1: VCCXYPowerMeasurements(
                        x=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                        y=VCCPowerMeasurement(total=1.0, nd_off=1.0, nd_on=1.0),
                        weight=1.0,
                    ),
                },
                timestamp=int(time.time()),
            )

        # increment counter BEFORE using it so that the averaging is not triggered on the very first measurement (except PMs with itvl=1)
        self._power_meter_poll_count = (self._power_meter_poll_count + 1) % self._power_meter_poll_reset

        self._accumulate_power(VCCBandGroup.B123, power_measurements_response.b123)
        self._accumulate_power(VCCBandGroup.B45A, power_measurements_response.b45a)
        self._accumulate_power(VCCBandGroup.B5B, power_measurements_response.b5b)
        for fs_id in range(1, self._num_fs + 1):
            self._accumulate_power(fs_id, power_measurements_response.fs[fs_id])

    def _power_meter_poll_exc_body(self, exception: Exception) -> None:
        """Log an error if an exception occurs during power meter polling."""
        self.log_exception("An unexpected exception occurred during power meter polling.")

    def _accumulate_power(self, power_meter_id: VCCBandGroup | int, power_measurements: VCCXYPowerMeasurements):
        """Accumulate power measurements for a single power meter."""
        if self.configuration_state is not FhsState.CONFIGURED:
            raise RuntimeError("Cannot calculate power before the VCC has been configured.")

        itvl = self._power_meter_measurement_intervals[power_meter_id]
        if power_meter_id not in range(8, 30):
            self.logger.error(
                f"ACCUMULATING POWER FOR METER: {power_meter_id} - ITVL={itvl}, "
                f"MEAS_X_TOTAL={round(power_measurements.x.total, 8)}, "
                f"MEAS_X_ON={round(power_measurements.x.nd_on, 8)}, "
                f"MEAS_X_OFF={round(power_measurements.x.nd_off, 8)}, "
                f"MEAS_Y_TOTAL={round(power_measurements.y.total, 8)}, "
                f"MEAS_Y_ON={round(power_measurements.y.nd_on, 8)}, "
                f"MEAS_Y_OFF={round(power_measurements.y.nd_off, 8)}, "
                f"WEIGHT={round(power_measurements.weight, 8)}"
            )
        accumulator = self._power_meter_measurement_accums[power_meter_id]
        accumulator.accumulate_from_measurements(power_measurements)

        if not self._power_meter_poll_count % itvl:
            xy_avg_power_db = accumulator.average_and_reset(convert_to_db=True)
            if power_meter_id not in range(8, 30):
                self.logger.error(
                    f"AVERAGED POWER FOR METER: {power_meter_id} - ITVL={itvl}, COUNT={self._power_meter_poll_count}, "
                    f"AVG_X_TOTAL={round(xy_avg_power_db.x.total, 8)}, "
                    f"AVG_X_ON={round(xy_avg_power_db.x.nd_on, 8)}, "
                    f"AVG_X_OFF={round(xy_avg_power_db.x.nd_off, 8)}, "
                    f"AVG_Y_TOTAL={round(xy_avg_power_db.y.total, 8)}, "
                    f"AVG_Y_ON={round(xy_avg_power_db.y.nd_on, 8)}, "
                    f"AVG_Y_OFF={round(xy_avg_power_db.y.nd_off, 8)}"
                )
            if not isinstance(power_meter_id, VCCBandGroup):
                xy_avg_power_db.apply_gain(self.fs_gains[0][power_meter_id - 1], self.fs_gains[1][power_meter_id - 1])
            self.current_power[power_meter_id] = xy_avg_power_db

    def _read_simulated_emulated_power(self) -> VCCPowerMeasurementResponse:
        """Read power measurements from all power meter simulators or emulators.

        Note that while this should technically also work when using FW,
        the gRPC controller has a built-in `read_power()` method which does the same thing
        and should be used instead to minimize the number of required gRPC calls.

        This method also currently does NOT ensure that the timestamps of every power measurement match;
        it simply uses the maximum retrieved timestamp across all measurements.
        """
        resp_dict: dict[str, Any] = {"fs": {}}
        ts = -1
        for id, power_meter in self.wideband_power_meters.items():
            pm_status = power_meter.status()
            ts = max(ts, pm_status.timestamp)
            xy_power_measurements = VCCXYPowerMeasurements(
                x=VCCPowerMeasurement(
                    total=pm_status.avg_power_pol_x,
                    nd_on=pm_status.nd_on_power_pol_x,
                    nd_off=pm_status.nd_off_power_pol_x,
                ),
                y=VCCPowerMeasurement(
                    total=pm_status.avg_power_pol_y,
                    nd_on=pm_status.nd_on_power_pol_y,
                    nd_off=pm_status.nd_off_power_pol_y,
                ),
                weight=pm_status.measured_sample_fraction,
            )
            match id:
                case VCCBandGroup.B123:
                    resp_dict["b123"] = xy_power_measurements
                case VCCBandGroup.B45A:
                    resp_dict["b45a"] = xy_power_measurements
                case VCCBandGroup.B5B:
                    resp_dict["b5b"] = xy_power_measurements
                case _:
                    resp_dict["fs"][id] = xy_power_measurements
        resp_dict["timestamp"] = ts
        return VCCPowerMeasurementResponse.from_dict(resp_dict)

    def _parse_vlan_mapping(self, vlan_file_loc):
        """
        Given the location of a VLAN mapping YAML file, gets the vlan mappings from the file for the VCC id and and adds it to the vlan_lookup dict in the object.
        """
        if not os.path.isfile(vlan_file_loc):
            self.log_error("VLAN mapping file not found at: " + vlan_file_loc)
            raise RuntimeError("VLAN mapping file not found at: " + vlan_file_loc)
        with open(vlan_file_loc) as f:
            def_data = yaml.safe_load(f)
        target_id = "vcc_" + str(self._vcc_id).zfill(3)
        if target_id in def_data:
            filtered_data = def_data[target_id]
            self.log_info("Adding VLAN mapping for " + target_id)
            for switch in filtered_data:
                self.vlan_lookup[switch] = filtered_data[switch]["vlan"]
        else:
            self.log_error("Mapping not added for " + target_id)
            raise KeyError(f"Could not find the requested VCC ({target_id}) in the VLAN mapping provided")
