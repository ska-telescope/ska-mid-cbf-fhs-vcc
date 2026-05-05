from __future__ import annotations

import copy
import functools
import json
import logging
import textwrap
from math import isnan
from threading import Event
from typing import Any, Callable, Optional

import jsonschema
from ska_control_model import CommunicationStatus, HealthState, ObsState, ResultCode, SimulationMode, TaskStatus
from ska_control_model.faults import StateModelError
from ska_mid_cbf_fhs_common import FtileEthernetManager, NonBlockingFunction, WidebandPowerMeterConfig, WidebandPowerMeterManager, calculate_gain_multiplier
from ska_mid_cbf_fhs_common.base_classes.device.controller.fhs_controller_base_dataclasses import FhsControllerBaseGoToIdleSchema, FhsControllerBaseScanSchema
from ska_mid_cbf_fhs_common.base_classes.device.controller.fhs_controller_component_manager_base import FhsControllerComponentManagerBase
from ska_mid_cbf_fhs_common.base_classes.ip_block.managers import BaseIPBlockManager
from ska_mid_cbf_fhs_common.helpers.constants import LONG_RUNNING_COMMAND_RESULT_BUFFER_DEFAULT_MAX_SIZE
from ska_mid_cbf_fhs_common.helpers.long_running_command_result_buffer import CommandType
from ska_mid_cbf_fhs_common.state_model.fhs_obs_state import FhsObsStateMachine
from ska_tango_base.base.base_component_manager import TaskCallbackType
from ska_tango_base.obs import ObsDeviceComponentManager

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_manager import (
    B123VccOsppfbChannelizerConfigureArgin,
    B123VccOsppfbChannelizerManager,
)
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_manager import FrequencySliceSelectionConfig, FrequencySliceSelectionManager
from ska_mid_cbf_fhs_vcc.helpers.frequency_band_enums import FrequencyBandEnum, VCCBandGroup, freq_band_dict
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_manager import PacketValidationManager
from ska_mid_cbf_fhs_vcc.vcc_all_bands.schemas.configure_scan import vcc_all_bands_configure_scan_schema
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_dataclasses import VCCAllBandsAutoSetFilterGainsSchema, VCCAllBandsConfigureScanConfig
from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_manager import VCCStreamMergeConfig, VCCStreamMergeConfigureArgin, VCCStreamMergeManager
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_manager import WidebandFrequencyShifterConfig, WidebandFrequencyShifterManager
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_manager import WidebandInputBufferConfig, WidebandInputBufferManager


class VCCAllBandsComponentManager(FhsControllerComponentManagerBase, ObsDeviceComponentManager):
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
        """The ConfigureScan input JSON schema for the VCC All Bands Controller."""
        return vcc_all_bands_configure_scan_schema

    @property
    def config_dataclass(self) -> type[VCCAllBandsConfigureScanConfig]:
        """The ConfigureScan input dataclass for the VCC All Bands Controller."""
        return VCCAllBandsConfigureScanConfig

    def __init__(
        self,
        *args: Any,
        device,
        logger: logging.Logger,
        simulation_mode: SimulationMode = SimulationMode.FALSE,
        attr_change_callback: Callable[[str, Any], None] | None = None,
        attr_archive_callback: Callable[[str, Any], None] | None = None,
        health_state_callback: Callable[[HealthState], None] | None = None,
        obs_state_action_callback: Callable[[str], None] | None = None,
        obs_command_running_callback: Callable[[str, bool], None] | None = None,
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
            attr_change_callback (:obj:`Callable[[str, Any], None] | None`, optional): Callback that is called when
                an attribute change event occurs. Default is None.
            attr_archive_callback (:obj:`Callable[[str, Any], None] | None`, optional): Callback that is called when
                an attribute archive event occurs. Default is None.
            health_state_callback (:obj:`Callable[[HealthState], None] | None`, optional): Callback that is called when
                a HealthState change occurs. Default is None.
            obs_state_action_callback (:obj:`Callable[[str, bool], None] | None`, optional): Callback that is called when
                the controller's observation state changes. Default is None.
            obs_command_running_callback (:obj:`Callable[[str, bool], None] | None`, optional): Callback that is called when
                an observing command starts running. Default is None.
            emulation_mode (:obj:`bool`, optional): Whether the controller is deployed
                in emulation mode or not. Default is False.
            create_log_file (:obj:`bool`, optional): Whether or not to create a log file for this controller. Default is True.
            **kwargs (:obj:`Any`): Any arbitrary keyword arguments to pass to the superclass init method.
        """
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

        self.log_info(f"Buffer: {self.long_running_command_result_buffer.transaction_id_to_command_result_map}")
        self.log_info(f"Buffer Size: {self.long_running_command_result_buffer.max_size}")

        self.obs_state = ObsState.IDLE
        """:obj:`ObsState`: The current observation state of this controller."""

        self._obs_state_action_callback = obs_state_action_callback if obs_state_action_callback is not None else self._default_callback
        self._obs_command_running_callback = obs_command_running_callback if obs_command_running_callback is not None else self._default_callback

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

        # vcc channels * number of polarizations
        self._num_fs = 0
        self._num_vcc_gains = 0

        self._fs_lanes = []

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

    def is_allowed(self, error_msg: str, obs_states: list[ObsState]) -> bool:
        """Determine whether the current ObsState is in the provided list of states,
        and log a warning message if not.

        Returns:
            :obj:`bool`: True if the current ObsState is in the list provided, False otherwise.
        """
        result = True

        if self.obs_state not in obs_states:
            self.logger.warning(error_msg)
            result = False

        return result

    def is_go_to_idle_allowed(self) -> bool:
        """Determine whether the GoToIdle command is allowed from the current ObsState.

        Returns:
            :obj:`bool`: True if the GoToIdle command is allowed, False otherwise.
        """
        self.logger.debug("Checking if gotoidle is allowed...")
        error_msg = f"go_to_idle not allowed in ObsState {self.obs_state}; " "must be in ObsState.READY"

        return self.is_allowed(error_msg, [ObsState.READY])

    def is_obs_reset_allowed(self) -> bool:
        """Determine whether the ObsReset command is allowed from the current ObsState.

        Returns:
            :obj:`bool`: True if the ObsReset command is allowed, False otherwise.
        """
        self.logger.debug("Checking if ObsReset is allowed...")
        error_msg = f"ObsReset not allowed in ObsState {self.obs_state}; \
            must be in ObsState.FAULT or ObsState.ABORTED"

        return self.is_allowed(error_msg, [ObsState.FAULT, ObsState.ABORTED])

    def scan(self, argin: str, task_callback: Optional[Callable] = None) -> tuple[TaskStatus, str]:
        """Submit the task to start running the Scan command implementation.

        Args:
            argin (:obj:`str`): The scan schema JSON string from the command's input argument.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="start",
                command_thread=self._scan,
            ),
            args=[argin],
            task_callback=task_callback,
        )

    def end_scan(
        self,
        argin: Optional[str] = None,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the EndScan command implementation.

        Args:
            argin (:obj:`str`): The Transaction id from the command's input argument, can be none
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="stop",
                command_thread=self._end_scan,
            ),
            args=[argin],
            task_callback=task_callback,
        )

    def go_to_idle(
        self,
        argin: str,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the GoToIdle command implementation.

        Args:
            argin (:obj:`str`): The go_to_idle schema JSON string from the command's input argument.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="deconfigure",
                command_thread=self._go_to_idle,
            ),
            args=[argin],
            task_callback=task_callback,
            is_cmd_allowed=self.is_go_to_idle_allowed,
        )

    def obs_reset(
        self,
        argin: Optional[str] = None,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the ObsReset command implementation.

        Args:
            argin (:obj:`str`): The Transaction id from the command's input argument, can be none
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="obsreset",
                command_thread=functools.partial(
                    self._obs_reset,
                    from_state=self.obs_state,
                ),
            ),
            args=[argin],
            task_callback=task_callback,
            is_cmd_allowed=self.is_obs_reset_allowed,
        )

    def abort_commands(
        self,
        task_callback: TaskCallbackType | None = None,
    ) -> tuple[TaskStatus, str]:
        """
        Run a task to abort all commands and stop any started IP blocks.

        Args:
            task_callback (:obj:`Optional[Callable]`, optional): A callback to pass to the superclass
                to be run when the task status changes. Default is None.

        Returns:
            :obj:`tuple[TaskStatus, str]`: The status of the task and an informative message string.
        """
        self._obs_state_action_callback(FhsObsStateMachine.ABORT_INVOKED)
        task_status, msg = super().abort_commands(task_callback)
        self._obs_state_action_callback(FhsObsStateMachine.ABORT_COMPLETED)
        return task_status, msg

    def _configure_scan(
        self,
        argin: str,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """Wrapper for the ConfigureScan command implementation for all controllers,
        to handle task and ObsState management as well as error handling.
        """
        try:
            self._obs_state_action_callback(FhsObsStateMachine.CONFIGURE_INVOKED)
            super()._configure_scan(argin, task_callback, task_abort_event)
            self._obs_state_action_callback(FhsObsStateMachine.CONFIGURE_COMPLETED)
        except StateModelError as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.CONFIGURESCAN, None)
            self.log_error("Attempted to call ConfigureScan command from an incorrect state", transaction_id)
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call ConfigureScan command from an incorrect state",
            )
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.CONFIGURESCAN, result_code=ResultCode.REJECTED, transaction_id=transaction_id
            )
        except jsonschema.ValidationError as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.CONFIGURESCAN, None)
            self.log_error("Invalid json provided for ConfigureScan", transaction_id)
            self.logger.exception(ex)
            self._obs_state_action_callback(FhsObsStateMachine.GO_TO_IDLE)
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for ConfigureScan")
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.CONFIGURESCAN, result_code=ResultCode.REJECTED, transaction_id=transaction_id
            )
        except Exception as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.CONFIGURESCAN, None)
            self.logger.exception(ex)
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            self._obs_state_action_callback(FhsObsStateMachine.GO_TO_IDLE)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during ConfigureScan: {ex}", width=400),
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.CONFIGURESCAN, result_code=ResultCode.FAILED, transaction_id=transaction_id)
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.CONFIGURESCAN] = None

    def _scan(
        self,
        argin: str,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """Wrapper for the Scan command implementation for all controllers,
        to handle task management as well as error handling.
        """
        try:
            super()._scan(argin, task_callback, task_abort_event)
        except StateModelError as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.SCAN, None)
            self.log_error("Attempted to call Scan command from an incorrect state", transaction_id)
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call Scan command from an incorrect state",
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.SCAN, result_code=ResultCode.REJECTED, transaction_id=transaction_id)
        except Exception as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.SCAN, None)
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during Scan: {ex}", width=400),
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.SCAN, result_code=ResultCode.FAILED, transaction_id=transaction_id)
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.SCAN] = None

    def _end_scan(
        self,
        transaction_id: Optional[str] = None,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """Wrapper for the EndScan command implementation for all controllers,
        to handle task management as well as error handling.
        """
        try:
            super()._end_scan(transaction_id, task_callback, task_abort_event)
        except StateModelError as ex:
            self.log_error("Attempted to call EndScan command from an incorrect state", transaction_id)
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call EndScan command from an incorrect state",
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.ENDSCAN, result_code=ResultCode.REJECTED, transaction_id=transaction_id)
        except Exception as ex:
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during EndScan: {ex}", width=400),
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.ENDSCAN, result_code=ResultCode.FAILED, transaction_id=transaction_id)
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.ENDSCAN] = None

    def _go_to_idle(
        self,
        argin: str = None,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """GoToIdle command implementation for all controllers."""
        try:
            super()._go_to_idle(argin, task_callback, task_abort_event)
        except StateModelError as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.GOTOIDLE, None)
            self.log_error("Attempted to call GoToIdle command from an incorrect state", transaction_id)
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call GoToIdle command from an incorrect state",
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.GOTOIDLE, result_code=ResultCode.REJECTED, transaction_id=transaction_id)
        except Exception as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.GOTOIDLE, None)
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during GoToIdle: {ex}", width=400),
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.GOTOIDLE, result_code=ResultCode.FAILED, transaction_id=transaction_id)
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.GOTOIDLE] = None

    def _obs_reset(
        self,
        transaction_id: Optional[str] = None,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
        from_state=ObsState.ABORTED,
    ) -> None:
        """ObsReset command implementation for all controllers."""
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)
            self.log_info("Received Command ObsReset", transaction_id)
            if self.task_abort_event_is_set("ObsReset", task_callback, task_abort_event):
                return

            # If in FAULT state, devices may still be running, so make sure they are stopped
            if from_state is ObsState.FAULT:
                self._stop_ip_blocks()

            self._reset()
            self._recover_all_ip_blocks()
            self.log_info("Command ObsReset Successful", transaction_id)

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ObsReset completed OK")
            self.long_running_command_result_buffer.insert(command_type=CommandType.OBSRESET, result_code=ResultCode.OK, transaction_id=transaction_id)
            return
        except StateModelError as ex:
            self.log_error(f"Attempted to call command from an incorrect state: {repr(ex)}", transaction_id)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call ObsReset command from an incorrect state",
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.OBSRESET, result_code=ResultCode.REJECTED, transaction_id=transaction_id)
        except Exception as ex:
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during ObsReset: {ex}", width=400),
            )
            self.long_running_command_result_buffer.insert(command_type=CommandType.OBSRESET, result_code=ResultCode.FAILED, transaction_id=transaction_id)
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.OBSRESET] = None

    def auto_set_filter_gains(
        self: VCCAllBandsComponentManager,
        argin: str,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        """Submit the task to start running the AutoSetFilterGains command implementation.

        Args:
            argin (:obj:`str`): JSON String following the auto set filter gains command schema
                Requested RFI headroom, in decibels (dB).
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

    def _configure_scan_controller_impl(
        self,
        configuration: VCCAllBandsConfigureScanConfig,
        task_callback: Optional[Callable] = None,
    ) -> None:
        """VCC-specific implementation for the ConfigureScan command.

        Args:
            configuration (:obj:`dict[str, Any]`): The configuration JSON string from the command's input argument.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
        """
        self._sample_rate = configuration.dish_sample_rate
        self._samples_per_frame = configuration.samples_per_frame
        self.frequency_band = freq_band_dict()[configuration.frequency_band]
        self.expected_dish_id = configuration.expected_dish_id
        self._config_id = configuration.config_id
        self.frequency_band_offset[0] = configuration.frequency_band_offset_stream_1
        self.frequency_band_offset[1] = configuration.frequency_band_offset_stream_2

        transaction_id = self.transaction_ids_per_command.get(CommandType.CONFIGURESCAN, None)

        self.log_info(f"Configuring VCC {self._vcc_id} - Config ID: {self._config_id}, Freq Band: {self.frequency_band.value}", transaction_id)

        # Only used if the configuration fails and go to idle deconfigure needs to be called
        # It is being initialised here so we dont need to initialise it in every if failed block
        failure_go_to_idle_schema = FhsControllerBaseGoToIdleSchema(subarray_id=self.subarray_id, transaction_id=transaction_id)

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

        self.vcc_gains = configuration.vcc_gain

        if len(self.vcc_gains) != self._num_vcc_gains:
            self._reset()
            raise ValueError(f"Incorrect number of gain values supplied: {self.vcc_gains} != {self._num_vcc_gains}")

        if not self.simulation_mode:
            # VCC123 Channelizer Configuration
            self.log_debug("VCC123 Channelizer Configuring..", transaction_id)
            if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                result = self.b123_vcc.configure(
                    B123VccOsppfbChannelizerConfigureArgin(sample_rate=self._sample_rate, gains=self.vcc_gains, transaction_id=transaction_id)
                )

                if result == 1:
                    self.log_error("Configuration of VCC123 Channelizer failed.", transaction_id)
                    self._go_to_idle_deconfigure(go_to_idle_schema=failure_go_to_idle_schema)
                    self._reset()
                    raise RuntimeError("Configuration of VCC123 failed.")

            else:
                # TODO: Implement routing to the 5 Channelizer once outlined
                self._reset()
                raise ValueError(f"ConfigureScan failed unsupported band specified: {self.frequency_band}")

            # WFS Configuration
            self.log_debug("Wideband Frequency Shifter Configuring..", transaction_id)
            result = self.wideband_frequency_shifter.configure(
                WidebandFrequencyShifterConfig(shift_frequency=self.frequency_band_offset[0], transaction_id=transaction_id)
            )
            if result == 1:
                self.log_error("Configuration of Wideband Frequency Shifter failed.", transaction_id)
                self._go_to_idle_deconfigure(go_to_idle_schema=failure_go_to_idle_schema)
                self._reset()
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
                self._go_to_idle_deconfigure(go_to_idle_schema=failure_go_to_idle_schema)
                self._reset()
                raise RuntimeError("Configuration of FS Selection failed.")

            # WIB Configuration
            self.log_debug("Wideband Input Buffer Configuring..", transaction_id)
            result = self.wideband_input_buffer.configure(
                WidebandInputBufferConfig(
                    transaction_id=transaction_id,
                    expected_sample_rate=self._sample_rate,
                    noise_diode_transition_holdoff_seconds=configuration.noise_diode_transition_holdoff_seconds,
                    expected_dish_band=self.frequency_band.value + 1,  # FW Drivers rely on integer indexes, that are 1-based
                )
            )

            if result == 1:
                self.log_error("Configuration of WIB failed.", transaction_id)
                self._go_to_idle_deconfigure(go_to_idle_schema=failure_go_to_idle_schema)
                self._reset()
                raise RuntimeError("Configuration of WIB failed.")

            self.wideband_input_buffer.expected_dish_id = self.expected_dish_id

            # Pre-channelizer WPM Configuration
            self.log_debug("Pre-channelizer Wideband Power Meters Configuring..", transaction_id)
            self._pre_channelizer_power_meter_configs = {
                VCCBandGroup.B123: configuration.b123_pwrm,
                VCCBandGroup.B45A: configuration.b45a_pwrm,
                VCCBandGroup.B5B: configuration.b5b_pwrm,
            }

            for band_group in VCCBandGroup:
                config = self._pre_channelizer_power_meter_configs.get(band_group)
                self.log_debug(f"Configuring {band_group.value} power meter with {config}", transaction_id)
                result = self.wideband_power_meters[band_group].configure(
                    WidebandPowerMeterConfig(
                        transaction_id=transaction_id,
                        averaging_time=config.averaging_time,
                        flagging=config.flagging,
                    )
                )
                if result == 1:
                    self.log_error(f"Configuration of {band_group.value} Wideband Power Meter failed.", transaction_id)
                    self._go_to_idle_deconfigure(go_to_idle_schema=failure_go_to_idle_schema)
                    self._reset()
                    raise RuntimeError(f"Configuration of {band_group.value} Wideband Power Meter failed.")

            # Post-channelizer WPM Configuration
            self.log_debug("Post-channelizer Wideband Power Meters Configuring..", transaction_id)
            self._fs_lanes = configuration.fs_lanes

            # Verify vlan_id is within range
            # ((config.vid >= 2 && config.vid <= 1001) || (config.vid >= 1006 && config.vid <= 4094))
            for config in self._fs_lanes:
                if not (2 <= config.vlan_id <= 1001 or 1006 <= config.vlan_id <= 4094):
                    raise ValueError(f"VLAN ID {config.vlan_id} is not within range")

            for config in self._fs_lanes:
                fs_id = int(config.fs_id)
                self.log_debug(f"Configuring FS {fs_id} power meter with {config}", transaction_id)
                result = self.wideband_power_meters[fs_id].configure(
                    WidebandPowerMeterConfig(
                        transaction_id=transaction_id,
                        averaging_time=config.averaging_time,
                        flagging=config.flagging,
                    )
                )
                if result == 1:
                    self.log_error(f"Configuration of FS {fs_id} Wideband Power Meter failed.", transaction_id)
                    self._go_to_idle_deconfigure(go_to_idle_schema=failure_go_to_idle_schema)
                    self._reset()
                    raise RuntimeError(f"Configuration of FS {fs_id} Wideband Power Meter failed.")

            # VCC Stream Merge Configuration
            self.log_debug("VCC Stream Merge Configuring..", transaction_id)
            for i in range(1, 3):
                result = self.vcc_stream_merges[i].configure(
                    VCCStreamMergeConfigureArgin(
                        transaction_id=transaction_id,
                        fs_lane_configs=[
                            VCCStreamMergeConfig(
                                vid=lane.vlan_id,
                                vcc_id=self._vcc_id,
                                fs_id=lane.fs_id,
                            )
                            for lane in self._fs_lanes[13 * (i - 1) : 13 * i]
                        ],
                    )
                )
                if result == 1:
                    self.log_error("Configuration of VCC Stream Merge failed.", transaction_id)
                    self._go_to_idle_deconfigure(go_to_idle_schema=failure_go_to_idle_schema)
                    self._reset()
                    raise RuntimeError("Configuration of VCC Stream Merge failed.")

        self.log_info(f"Sucessfully completed ConfigureScan for Config ID: {self._config_id}", transaction_id)

    def _scan_controller_impl(
        self,
        scan_schema: FhsControllerBaseScanSchema,
        task_callback: Optional[Callable] = None,
    ) -> None:
        """VCC-specific implementation for the Scan command.

        Args:
            scan_schema (:obj:`dict[str, Any]`): The scan schema JSON string from the command's input argument.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
        """
        self.scan_id = scan_schema.scan_id
        transaction_id = self.transaction_ids_per_command.get(CommandType.SCAN, None)

        self.log_info("Starting Scanning", transaction_id)

        if not self.simulation_mode:
            eth_start_result, pv_start_result, wib_start_result = NonBlockingFunction.await_all(
                self.ethernet_200g.start(),
                self.packet_validation.start(),
                self.wideband_input_buffer.start(),
            )
            if eth_start_result == 1 or pv_start_result == 1 or wib_start_result == 1:
                raise RuntimeError("Failed to start Ethernet, PV and/or WIB")

        self.log_info("Scan started", transaction_id)

    def _end_scan_controller_impl(
        self,
        task_callback: Optional[Callable] = None,
    ) -> None:
        """VCC-specific implementation for the EndScan command.

        Args:
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
        """
        transaction_id = self.transaction_ids_per_command.get(CommandType.ENDSCAN, None)
        self.log_info("Ending Scan", transaction_id)

        if not self.simulation_mode:
            eth_stop_result, pv_stop_result, wib_stop_result = NonBlockingFunction.await_all(
                self.ethernet_200g.stop(),
                self.packet_validation.stop(),
                self.wideband_input_buffer.stop(),
            )
            if eth_stop_result == 1 or pv_stop_result == 1 or wib_stop_result == 1:
                raise RuntimeError("Failed to stop Ethernet, PV and/or WIB")

        self.log_info("Scan ended", transaction_id)

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
                self._attr_change_callback("subarrayID", argin)
                self._attr_archive_callback("subarrayID", argin)
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
        argin: str | None = None,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """Calculate and apply optimal gain multipliers for VCC coarse channels.
        This is the implementation for the AutoSetFilterGains command.

        Args:
            argin (:obj:`str`): JSON String following the auto set filter gains command schema
                Requested RFI headroom, in decibels (dB).
                Must be a list containing either a single value to apply to all frequency slices,
                or a value per frequency slice to be applied separately.
            task_callback (:obj:`Optional[Callable]`, optional): A callback to run when the task status changes. Default is None.
            task_abort_event (:obj:`Optional[Event]`, optional): An event representing whether or not the task has aborted.
                Default is None.
        """
        try:
            headrooms = [3.0]
            transaction_id = None

            if argin:
                auto_set_filter_gains_schema_dict = json.loads(argin)
                transaction_id = auto_set_filter_gains_schema_dict.get("transaction_id", None)
                self.transaction_ids_per_command[CommandType.AUTOSETFILTERGAINS] = transaction_id
                auto_set_filter_gains_schema = VCCAllBandsAutoSetFilterGainsSchema.from_dict(auto_set_filter_gains_schema_dict)
                headrooms = auto_set_filter_gains_schema.headrooms

            self.log_info("Received Command AutoSetFilterGains", transaction_id)

            if (num_headrooms := len(headrooms)) not in [1, self._num_fs]:
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.REJECTED,
                    f"Cannot auto-set gains as the input headroom {headrooms} is invalid.",
                )
                self.long_running_command_result_buffer.insert(
                    command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.REJECTED, transaction_id=transaction_id
                )
                return

            new_gains = copy.copy(self.vcc_gains)

            # Read all power meters
            for i in range(self._num_fs):
                # Read power
                status = self.wideband_power_meters[i + 1].status()
                if status is None:
                    self._set_task_callback(
                        task_callback,
                        TaskStatus.COMPLETED,
                        ResultCode.FAILED,
                        (f"Failed to auto-set gains: Failed to retrieve status from the FS {i + 1} power meter."),
                    )
                    self.long_running_command_result_buffer.insert(
                        command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
                    )
                    return
                measured_power_pol_x = status.avg_power_pol_x
                measured_power_pol_y = status.avg_power_pol_y

                for power, pol in (measured_power_pol_x, "X"), (measured_power_pol_y, "Y"):
                    if not isinstance(power, (int, float)) or isinstance(power, bool) or isnan(power) or power <= 0 or power > 1:
                        self._set_task_callback(
                            task_callback,
                            TaskStatus.COMPLETED,
                            ResultCode.FAILED,
                            (f"Failed to auto-set gains: The FS {i + 1} power meter failed to provide a valid power measurement for polarization {pol}."),
                        )
                        self.long_running_command_result_buffer.insert(
                            command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
                        )
                        return

                headroom = headrooms[i % num_headrooms]

                # Convert to multiplier
                new_gains[i] = float(calculate_gain_multiplier(0.0, measured_power_pol_x, headroom))
                new_gains[i + self._num_fs] = float(calculate_gain_multiplier(0.0, measured_power_pol_y, headroom))

            # Reconfigure VCCs
            if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                result = self.b123_vcc.configure(
                    B123VccOsppfbChannelizerConfigureArgin(
                        transaction_id=transaction_id,
                        sample_rate=self._sample_rate,
                        gains=new_gains,
                    )
                )

                if result == 1:
                    self.log_error("Failed to reconfigure VCC123 Channelizer with new gain values.", transaction_id)
                    self.b123_vcc.configure(
                        B123VccOsppfbChannelizerConfigureArgin(
                            transaction_id=transaction_id,
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
                    self.long_running_command_result_buffer.insert(
                        command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
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
                self.long_running_command_result_buffer.insert(
                    command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
                )
                return
            # Update vccGains and publish change
            self.vcc_gains = new_gains
            self.last_requested_headrooms = headrooms

            self.log_info(f"Successfully set Autofilter gains with headrooms {headrooms}", transaction_id)

            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.OK,
                "AutoSetFilterGains completed OK",
            )
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.OK, transaction_id=transaction_id
            )
        except Exception as ex:
            transaction_id = self.transaction_ids_per_command.get(CommandType.AUTOSETFILTERGAINS, None)
            self.logger.exception(ex)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.FAILED,
                textwrap.shorten(f"An unexpected exception occurred during AutoSetFilterGains: {ex}", width=400),
            )
            self.long_running_command_result_buffer.insert(
                command_type=CommandType.AUTOSETFILTERGAINS, result_code=ResultCode.FAILED, transaction_id=transaction_id
            )
        finally:
            # Reset the ID so it's not used in a different Command call
            self.transaction_ids_per_command[CommandType.AUTOSETFILTERGAINS] = None

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
        self._fs_lanes = []

    def _go_to_idle_deconfigure(self, go_to_idle_schema: FhsControllerBaseGoToIdleSchema) -> None:
        """Deconfigure all ip blocks"""
        transaction_id = self.transaction_ids_per_command.get(CommandType.GOTOIDLE, None)

        # VCC123 Channelizer Deconfiguration
        b123_vcc_deconfigure_result = self.b123_vcc.deconfigure()
        if b123_vcc_deconfigure_result == 1:
            self.log_error("Deconfiguration of VCC123 Channelizer failed.", transaction_id)
            raise RuntimeError("Deconfiguration of VCC123 failed.")

        # WFS Deconfiguration
        wfs_deconfigure_result = self.wideband_frequency_shifter.deconfigure()
        if wfs_deconfigure_result == 1:
            self.log_error("Deconfiguration of Wideband Frequency Shifter failed.", transaction_id)
            raise RuntimeError("Deconfiguration of Wideband Frequency Shifter failed.")

        # FSS Deconfiguration
        fss_deconfigure_result = self.frequency_slice_selection.deconfigure()
        if fss_deconfigure_result == 1:
            self.log_error("Deconfiguration of FS Selection failed.", transaction_id)
            raise RuntimeError("Deconfiguration of FS Selection failed.")

        # WIB Deconfiguration
        wib_deconfigure_result = self.wideband_input_buffer.deconfigure()
        if wib_deconfigure_result == 1:
            self.log_error("Deconfiguration of WIB failed.", transaction_id)
            raise RuntimeError("Deconfiguration of WIB failed.")

        # Pre-channelizer WPM Deconfiguration
        for band_group in VCCBandGroup:
            pre_channelizer_wpm_deconfiguration_result = self.wideband_power_meters[band_group].deconfigure()
            if pre_channelizer_wpm_deconfiguration_result == 1:
                self.log_error(f"Deconfiguration of {band_group.value} Wideband Power Meter failed.", transaction_id)
                raise RuntimeError(f"Deconfiguration of {band_group.value} Wideband Power Meter failed.")

        # Post-channelizer WPM Deconfiguration
        for config in self._fs_lanes:
            fs_id = int(config.fs_id)
            post_channelizer_wpm_deconfiguration_result = self.wideband_power_meters[fs_id].deconfigure()
            if post_channelizer_wpm_deconfiguration_result == 1:
                self.log_error(f"Deconfiguration of FS {fs_id} Wideband Power Meter failed.", transaction_id)
                raise RuntimeError(f"Deconfiguration of FS {fs_id} Wideband Power Meter failed.")

        # VCC Stream Merge Deconfiguration
        for i in range(1, 3):
            vcc_stream_merge_deconfiguration_result = self.vcc_stream_merges[i].deconfigure()
            if vcc_stream_merge_deconfiguration_result == 1:
                self.log_error("Deconfiguration of VCC Stream Merge failed.", transaction_id)
                raise RuntimeError("Deconfiguration of VCC Stream Merge failed.")

        self.log_info("Sucessfully deconfigured all IP Blocks", transaction_id)

    def _recover_all_ip_blocks(self) -> None:
        """Call recover method of all ip blocks"""
        transaction_id = self.transaction_ids_per_command.get(CommandType.OBSRESET, None)

        # VCC123 Channelizer Recovery
        b123_vcc_recover_result = self.b123_vcc.recover()
        if b123_vcc_recover_result == 1:
            self.log_error("Recovery of VCC123 Channelizer failed.", transaction_id)
            raise RuntimeError("Recovery of VCC123 failed.")

        # WFS Recovery
        wfs_recovery_result = self.wideband_frequency_shifter.recover()
        if wfs_recovery_result == 1:
            self.log_error("Recovery of Wideband Frequency Shifter failed.", transaction_id)
            raise RuntimeError("Recovery of Wideband Frequency Shifter failed.")

        # FSS Recovery
        fss_recovery_result = self.frequency_slice_selection.recover()
        if fss_recovery_result == 1:
            self.log_error("Recovery of FS Selection failed.", transaction_id)
            raise RuntimeError("Recovery of FS Selection failed.")

        # WIB Recovery
        wib_recover_result = self.wideband_input_buffer.recover()
        if wib_recover_result == 1:
            self.log_error("Recovery of WIB failed.", transaction_id)
            raise RuntimeError("Recovery of WIB failed.")

        # Pre-channelizer WPM Recovery
        for band_group in VCCBandGroup:
            pre_channelizer_wpm_recover_result = self.wideband_power_meters[band_group].recover()
            if pre_channelizer_wpm_recover_result == 1:
                self.log_error(f"Recovery of {band_group.value} Wideband Power Meter failed.", transaction_id)
                raise RuntimeError(f"Recovery of {band_group.value} Wideband Power Meter failed.")

        # Post-channelizer WPM Recovery
        for config in self._fs_lanes:
            fs_id = int(config.fs_id)
            post_channelizer_wpm_recover_result = self.wideband_power_meters[fs_id].recover()
            if post_channelizer_wpm_recover_result == 1:
                self.log_error(f"Recovery of FS {fs_id} Wideband Power Meter failed.", transaction_id)
                raise RuntimeError(f"Recovery of FS {fs_id} Wideband Power Meter failed.")

        # VCC Stream Merge Recovery
        for i in range(1, 3):
            vcc_stream_merge_recover_result = self.vcc_stream_merges[i].recover()
            if vcc_stream_merge_recover_result == 1:
                self.log_error("Recovery of VCC Stream Merge failed.", transaction_id)
                raise RuntimeError("Recovery of VCC Stream Merge failed.")

        self.log_info("Sucessfully Recovered all IP Blocks", transaction_id)

    def _obs_command_with_callback(
        self,
        *args,
        command_thread: Callable[[Any], None],
        hook: str,
        **kwargs,
    ):
        """Wrap command thread with ObsStateModel-driving callbacks.

        Args:
            *args (:obj:`Any`): Any arbitrary positional arguments to pass to the _obs_command_running_callback function.
            command_thread (:obj:`Callable[[Any], None]`): actual command thread to be executed
            hook (:obj:`str`): hook for state machine action
            **kwargs (:obj:`Any`): Any arbitrary keyword arguments to pass to the _obs_command_running_callback function.
        """
        if self._obs_command_running_callback is not None:
            self._obs_command_running_callback(hook=hook, running=True)
            command_thread(*args, **kwargs)
            self._obs_command_running_callback(hook=hook, running=False)
        else:
            command_thread(*args, **kwargs)
