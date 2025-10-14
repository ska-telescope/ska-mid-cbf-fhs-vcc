from __future__ import annotations

import copy
import textwrap
from math import isnan
from threading import Event
from typing import Any, Callable, Optional

from ska_control_model import ResultCode, TaskStatus
from ska_mid_cbf_fhs_common import FtileEthernetManager, NonBlockingFunction, WidebandPowerMeterConfig, WidebandPowerMeterManager, calculate_gain_multiplier
from ska_mid_cbf_fhs_common.base_classes.device.controller.fhs_controller_component_manager_base import FhsControllerComponentManagerBase
from ska_mid_cbf_fhs_common.base_classes.ip_block.managers import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.api.pyro.pyro_client import PyroClient
from ska_mid_cbf_fhs_vcc.api.pyro.pyro_wib_client import PyroWibClient
from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_manager import (
    B123VccOsppfbChannelizerConfigureArgin,
    B123VccOsppfbChannelizerManager,
)
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_manager import FrequencySliceSelectionConfig, FrequencySliceSelectionManager
from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum, VCCBandGroup, freq_band_dict
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_manager import PacketValidationManager
from ska_mid_cbf_fhs_vcc.vcc_all_bands.schemas.configure_scan import vcc_all_bands_configure_scan_schema
from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_manager import VCCStreamMergeConfig, VCCStreamMergeConfigureArgin, VCCStreamMergeManager
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_manager import WidebandFrequencyShifterConfig, WidebandFrequencyShifterManager
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager import WidebandInputBufferConfig, WidebandInputBufferManager


class VCCAllBandsComponentManager(FhsControllerComponentManagerBase):
    """Component manager for the VCC All Bands Controller device."""

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

    vcc_gains: list[float]
    """:obj:`list[float]`: The currently applied gain multipliers for VCC coarse channels."""

    last_requested_headrooms: list[float]
    """:obj:`list[float]`: The requested headrooms from the most recent call to AutoSetFilterGains."""

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

    @property
    def config_schema(self) -> dict[str, Any]:
        """The ConfigureScan input JSON schema for this controller."""
        return vcc_all_bands_configure_scan_schema

    def _controller_specific_setup(self) -> None:
        """Set up initial members/attributes/etc specific to the controller subclass. Executed as part of __init__."""
        self._vcc_id = self.device.device_id
        self._config_id = ""
        self._scan_id = 0

        self.subarray_id = 0
        self.expected_dish_id = None

        self.frequency_band: FrequencyBandEnum = FrequencyBandEnum._1
        self.frequency_band_offset: list[int] = [0, 0]

        self.input_sample_rate: int = 0

        self._fsps = []
        self._maximum_fsps = 10

        # vcc channels * number of polarizations
        self._num_fs = 0
        self._num_vcc_gains = 0

        self.vcc_gains: list[float] = []
        self.last_requested_headrooms: list[float] = []

    def _init_ip_block_managers(self) -> list[BaseIPBlockManager]:
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

    def update_subarray_membership(
        self: VCCAllBandsComponentManager,
        argin: int,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the UpdateSubarrayMembership command implementation.

        Args:
            argin (:obj:`int`): The subarray ID.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=self._update_subarray_membership,
            args=[argin],
            task_callback=task_callback,
        )

    def auto_set_filter_gains(
        self: VCCAllBandsComponentManager,
        argin: list[float],
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the AutoSetFilterGains command implementation.

        Args:
            argin (:obj:`list[float]`): Requested RFI headroom, in decibels (dB).
                Must be a list containing either a single value to apply to all frequency slices,
                or a value per frequency slice to be applied separately.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=self._auto_set_filter_gains,
            args=[argin],
            task_callback=task_callback,
        )

    def test_host_communication(
        self: VCCAllBandsComponentManager,
        argin,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=self._test_host_communication,
            args=[argin],
            task_callback=task_callback,
        )

    def test_wib_config(
        self: VCCAllBandsComponentManager,
        argin,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=self._test_wib_config,
            args=[argin],
            task_callback=task_callback,
        )

    def test_wib_status(
        self: VCCAllBandsComponentManager,
        argin,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=self._test_wib_status,
            args=[argin],
            task_callback=task_callback,
        )

    def _test_wib_status(
        self,
        argin,
        task_abort_event: Event,
        task_callback: Optional[Callable] = None,
    ) -> None:
        task_callback(status=TaskStatus.IN_PROGRESS)

        self.logger.info("::: Getting WIB status from Terabox Server :::")
        pyro_wib_client = PyroWibClient(self.logger, argin[0])
        pyro_wib_client.status()

        task_callback(status=TaskStatus.COMPLETED, result=(ResultCode.OK, "WIB Status Recieved on Terabox OK"))

    def _test_wib_config(
        self,
        argin,
        task_abort_event: Event,
        task_callback: Optional[Callable] = None,
    ) -> None:
        task_callback(status=TaskStatus.IN_PROGRESS)

        self.logger.info("::: Configured WIB on Terabox Server :::")
        pyro_wib_client = PyroWibClient(self.logger, argin[0])
        pyro_wib_client.configure(argin[1])

        task_callback(status=TaskStatus.COMPLETED, result=(ResultCode.OK, "WIB Configured on Terabox OK"))

    def _test_host_communication(
        self,
        argin,
        task_abort_event: Event,
        task_callback: Optional[Callable] = None,
    ) -> None:
        pyro_client = PyroClient(self.logger)

        task_callback(status=TaskStatus.IN_PROGRESS)

        if self.task_abort_event_is_set("TestHostCommunication", task_callback, task_abort_event):
            return

        self.logger.info("Checking connection to nameserver....")
        self.logger.info(f"::::: Getting NS_HOST: {pyro_client.get_host_ip()}")
        pyro_client.ping()
        self.logger.info("[SUCCESS] Ping completed....")

        self.logger.info(f":::::: Calling status function on driver {argin[0]}")
        pyro_client.get_driver_status(argin[0])

        task_callback(status=TaskStatus.COMPLETED, result=(ResultCode.OK, "Host Communication OK"))

    def _configure_scan_controller_impl(
        self,
        configuration: dict[str, Any],
        task_callback: Optional[Callable] = None,
    ) -> None:
        """VCC-specific implementation for the ConfigureScan command.

        Args:
            configuration (:obj:`dict[str, Any]`): The configuration JSON string from the command's input argument.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
        """
        self._sample_rate = configuration["dish_sample_rate"]
        self._samples_per_frame = configuration["samples_per_frame"]
        self.frequency_band = freq_band_dict()[configuration["frequency_band"]]
        self.expected_dish_id = configuration["expected_dish_id"]
        self._config_id = configuration["config_id"]
        self.logger.info(f"Configuring VCC {self._vcc_id} - Config ID: {self._config_id}, Freq Band: {self.frequency_band.value}")

        if "frequency_band_offset_stream_1" in configuration:
            self.frequency_band_offset[0] = configuration["frequency_band_offset_stream_1"]

        if "frequency_band_offset_stream_2" in configuration:
            self.frequency_band_offset[1] = configuration["frequency_band_offset_stream_2"]

        match self.frequency_band:
            case FrequencyBandEnum._1 | FrequencyBandEnum._2:
                self._num_fs = 10
            case FrequencyBandEnum._3 | FrequencyBandEnum._4:
                self._reset()
                raise ValueError("Bands 3/4 not implemented")
                # self._num_fs = 15
            case _:
                self._reset()
                raise ValueError("Bands 5A/B not implemented")
                # self._num_fs = 26

        # number of channels * number of polarizations
        self._num_vcc_gains = self._num_fs * 2

        self.vcc_gains = configuration["vcc_gain"]

        if len(self.vcc_gains) != self._num_vcc_gains:
            self._reset()
            raise ValueError(f"Incorrect number of gain values supplied: {self.vcc_gains} != {self._num_vcc_gains}")

        if not self.simulation_mode:
            # VCC123 Channelizer Configuration
            self.logger.debug("VCC123 Channelizer Configuring..")
            if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                result = self.b123_vcc.configure(B123VccOsppfbChannelizerConfigureArgin(sample_rate=self._sample_rate, gains=self.vcc_gains))

                if result == 1:
                    self.logger.error("Configuration of VCC123 Channelizer failed.")
                    self._reset()
                    raise RuntimeError("Configuration of VCC123 failed.")

            else:
                # TODO: Implement routing to the 5 Channelizer once outlined
                self._reset()
                raise ValueError(f"ConfigureScan failed unsupported band specified: {self.frequency_band}")

            # WFS Configuration
            self.logger.debug("Wideband Frequency Shifter Configuring..")
            result = self.wideband_frequency_shifter.configure(WidebandFrequencyShifterConfig(shift_frequency=self.frequency_band_offset[0]))
            if result == 1:
                self.logger.error("Configuration of Wideband Frequency Shifter failed.")
                raise RuntimeError("Configuration of Wideband Frequency Shifter failed.")

            # FSS Configuration
            result = self.frequency_slice_selection.configure(
                FrequencySliceSelectionConfig(
                    band_select=self.frequency_band.value + 1,
                    band_start_channel=[0, 1],
                )
            )

            if result == 1:
                self.logger.error("Configuration of FS Selection failed.")
                raise RuntimeError("Configuration of FS Selection failed.")

            # WIB Configuration
            self.logger.debug("Wideband Input Buffer Configuring..")
            result = self.wideband_input_buffer.configure(
                WidebandInputBufferConfig(
                    expected_sample_rate=self._sample_rate,
                    noise_diode_transition_holdoff_seconds=configuration["noise_diode_transition_holdoff_seconds"],
                    expected_dish_band=self.frequency_band.value + 1,  # FW Drivers rely on integer indexes, that are 1-based
                )
            )

            if result == 1:
                self.logger.error("Configuration of WIB failed.")
                raise RuntimeError("Configuration of WIB failed.")

            self.wideband_input_buffer.expected_dish_id = self.expected_dish_id

            # Pre-channelizer WPM Configuration
            self.logger.debug("Pre-channelizer Wideband Power Meters Configuring..")
            self._b123_pwrm = configuration["b123_pwrm"]
            self._b45a_pwrm = configuration["b45a_pwrm"]
            self._b5b_pwrm = configuration["b5b_pwrm"]

            for band_group in VCCBandGroup:
                config = configuration[f"{band_group.value}_pwrm"]
                self.logger.debug(f"Configuring {band_group.value} power meter with {config}")
                result = self.wideband_power_meters[band_group].configure(
                    WidebandPowerMeterConfig(
                        averaging_time=config["averaging_time"],
                        flagging=config["flagging"],
                    )
                )
                if result == 1:
                    self.logger.error(f"Configuration of {band_group.value} Wideband Power Meter failed.")
                    raise RuntimeError(f"Configuration of {band_group.value} Wideband Power Meter failed.")

            # Post-channelizer WPM Configuration
            self.logger.debug("Post-channelizer Wideband Power Meters Configuring..")
            self._fs_lanes = configuration["fs_lanes"]

            # Verify vlan_id is within range
            # ((config.vid >= 2 && config.vid <= 1001) || (config.vid >= 1006 && config.vid <= 4094))
            for config in self._fs_lanes:
                if not (2 <= config["vlan_id"] <= 1001 or 1006 <= config["vlan_id"] <= 4094):
                    raise ValueError(f"VLAN ID {config['vlan_id']} is not within range")

            for config in self._fs_lanes:
                fs_id = int(config["fs_id"])
                self.logger.debug(f"Configuring FS {fs_id} power meter with {config}")
                result = self.wideband_power_meters[fs_id].configure(
                    WidebandPowerMeterConfig(
                        averaging_time=config["averaging_time"],
                        flagging=config["flagging"],
                    )
                )
                if result == 1:
                    self.logger.error(f"Configuration of FS {fs_id} Wideband Power Meter failed.")
                    raise RuntimeError(f"Configuration of FS {fs_id} Wideband Power Meter failed.")

            # VCC Stream Merge Configuration
            self.logger.debug("VCC Stream Merge Configuring..")
            for i in range(1, 3):
                result = self.vcc_stream_merges[i].configure(
                    VCCStreamMergeConfigureArgin(
                        fs_lane_configs=[
                            VCCStreamMergeConfig(
                                vid=lane["vlan_id"],
                                vcc_id=self._vcc_id,
                                fs_id=lane["fs_id"],
                            )
                            for lane in self._fs_lanes[13 * (i - 1) : 13 * i]
                        ]
                    )
                )
                if result == 1:
                    self.logger.error("Configuration of VCC Stream Merge failed.")
                    raise RuntimeError("Configuration of VCC Stream Merge failed.")

        self.logger.info(f"Sucessfully completed ConfigureScan for Config ID: {self._config_id}")

    def _scan_controller_impl(
        self,
        scan_id: int,
        task_callback: Optional[Callable] = None,
    ) -> None:
        """VCC-specific implementation for the Scan command.

        Args:
            scan_id (:obj:`int`): ID of the scan
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
        """
        if not self.simulation_mode:
            eth_start_result, pv_start_result, wib_start_result = NonBlockingFunction.await_all(
                self.ethernet_200g.start(),
                self.packet_validation.start(),
                self.wideband_input_buffer.start(),
            )
            if eth_start_result == 1 or pv_start_result == 1 or wib_start_result == 1:
                raise RuntimeError("Failed to start Ethernet, PV and/or WIB")

    def _end_scan_controller_impl(
        self,
        task_callback: Optional[Callable] = None,
    ) -> None:
        """VCC-specific implementation for the EndScan command.

        Args:
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
        """
        if not self.simulation_mode:
            eth_stop_result, pv_stop_result, wib_stop_result = NonBlockingFunction.await_all(
                self.ethernet_200g.stop(),
                self.packet_validation.stop(),
                self.wideband_input_buffer.stop(),
            )
            if eth_stop_result == 1 or pv_stop_result == 1 or wib_stop_result == 1:
                raise RuntimeError("Failed to stop Ethernet, PV and/or WIB")

    def _update_subarray_membership(
        self,
        argin: int,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """Update subarray membership for this VCC. This is the implementation for the UpdateSubarrayMembership command.

        Args:
            argin (:obj:`int`): Subarray ID to assign to this VCC. Set to 0 to unassign the currently assigned subarray.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
            task_abort_event (:obj:`Optional[Event]`, optional): An event representing whether or not the task has aborted.
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
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.OK,
                    "UpdateSubarrayMembership completed OK",
                )
        except Exception as ex:
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during UpdateSubarrayMembership: {ex}", width=400),
            )

    def _auto_set_filter_gains(
        self,
        argin: list[float] | None = None,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """Calculate and apply optimal gain multipliers for VCC coarse channels.
        This is the implementation for the AutoSetFilterGains command.

        Args:
            argin (:obj:`list[float]`): Requested RFI headroom, in decibels (dB).
                Must be a list containing either a single value to apply to all frequency slices,
                or a value per frequency slice to be applied separately.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
            task_abort_event (:obj:`Optional[Event]`, optional): An event representing whether or not the task has aborted.
                Default is None.
        """
        if argin is None:
            argin = [3.0]
        try:
            if (num_headrooms := len(argin)) not in [1, self._num_fs]:
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.REJECTED,
                    f"Cannot auto-set gains as the input headroom {argin} is invalid.",
                )
                return

            new_gains = copy.copy(self.vcc_gains)

            # Read all power meters
            for i in range(self._num_fs):
                # Read power
                status = self.wideband_power_meters[i + 1].status()
                measured_power_pol_x: float = status.get("avg_power_pol_x", None)
                measured_power_pol_y: float = status.get("avg_power_pol_y", None)

                for power, pol in (measured_power_pol_x, "X"), (measured_power_pol_y, "Y"):
                    if not isinstance(power, (int, float)) or isinstance(power, bool) or isnan(power) or power <= 0 or power > 1:
                        self._set_task_callback(
                            task_callback,
                            TaskStatus.COMPLETED,
                            ResultCode.FAILED,
                            (f"Failed to auto-set gains: The FS {i + 1} power meter failed to provide a valid power measurement for polarization {pol}."),
                        )
                        return

                headroom = argin[i % num_headrooms]

                # Convert to multiplier
                new_gains[i] = float(calculate_gain_multiplier(0.0, measured_power_pol_x, headroom))
                new_gains[i + self._num_fs] = float(calculate_gain_multiplier(0.0, measured_power_pol_y, headroom))

            # Reconfigure VCCs
            if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                result = self.b123_vcc.configure(
                    B123VccOsppfbChannelizerConfigureArgin(
                        sample_rate=self._sample_rate,
                        gains=new_gains,
                    )
                )

                if result == 1:
                    self.logger.error("Failed to reconfigure VCC123 Channelizer with new gain values.")
                    self.b123_vcc.configure(
                        B123VccOsppfbChannelizerConfigureArgin(
                            sample_rate=self._sample_rate,
                            gains=self.vcc_gains,
                        )
                    )
                    self._set_task_callback(
                        task_callback,
                        TaskStatus.COMPLETED,
                        ResultCode.FAILED,
                        "Failed to auto-set gains: failed to reconfigure VCC123 Channelizer with new gain values.",
                    )
                    return

            else:
                # TODO: Implement routing to the 5 Channelizer once outlined
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.FAILED,
                    "Failed to auto-set gains: currently selected frequency band is not supported.",
                )
                return

            # Update vccGains and publish change
            self.vcc_gains = new_gains
            self.last_requested_headrooms = argin

            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.OK,
                "AutoSetFilterGains completed OK",
            )
        except Exception as ex:
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during AutoSetFilterGains: {ex}", width=400),
            )

    def _stop_ip_blocks(self) -> int:
        """Stop all IP blocks."""
        eth_stop_result, pv_stop_result, wib_stop_result = NonBlockingFunction.await_all(
            self.ethernet_200g.stop(),
            self.packet_validation.stop(),
            self.wideband_input_buffer.stop(),
        )
        if eth_stop_result == 1 or pv_stop_result == 1 or wib_stop_result == 1:
            self.logger.error("Ethernet/PV/WIB STOP FAILURE (TODO)")
            return 1
        return 0

    def _reset(self) -> None:
        """Reset all attributes and other data."""
        self._config_id = ""
        self._scan_id = 0
        self.frequency_band = FrequencyBandEnum._1
        self.frequency_band_offset = [0, 0]
        self._sample_rate = 0
        self._samples_per_frame = 0
        self._fsps = []
