from __future__ import annotations

import functools
import json
import logging
import time
from threading import Event
from typing import Any, Callable, Optional

import jsonschema
import tango
from ska_control_model import CommunicationStatus, HealthState, ObsState, ResultCode, SimulationMode, TaskStatus
from ska_control_model.faults import StateModelError
from ska_tango_base.base.base_component_manager import TaskCallbackType
from ska_tango_testing import context
from tango import EventData, EventType

from ska_mid_cbf_fhs_vcc.common.fhs_component_manager_base import FhsComponentManagerBase
from ska_mid_cbf_fhs_vcc.common.fhs_health_monitor import FhsHealthMonitor
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_helpers import FrequencyBandEnum, freq_band_dict

from .vcc_all_bands_config import schema


class VCCAllBandsComponentManager(FhsComponentManagerBase):
    def __init__(
        self: VCCAllBandsComponentManager,
        *args: Any,
        vcc_id: str,
        mac_200_FQDN: str,
        vcc_123_channelizer_FQDN: str,
        vcc_45_channelizer_FQDN: str,
        wideband_input_buffer_FQDN: str,
        wideband_frequency_shifter_FQDN: str,
        packet_validation_FQDN: str,
        circuit_switch_FQDN: str,
        fs_selection_FQDN: str,
        logger: logging.Logger,
        simulation_mode: SimulationMode = SimulationMode.FALSE,
        attr_change_callback: Callable[[str, Any], None] | None = None,
        attr_archive_callback: Callable[[str, Any], None] | None = None,
        health_state_callback: Callable[[HealthState], None] | None = None,
        obs_command_running_callback: Callable[[str, bool], None],
        emulation_mode: bool = False,
        **kwargs: Any,
    ) -> None:
        self._vcc_id = vcc_id

        self.frequency_band = FrequencyBandEnum._1

        self._mac_200_fqdn = mac_200_FQDN
        self._config_id = ""
        self._scan_id = 0
        self._packet_validation_fqdn = packet_validation_FQDN
        self._vcc_123_fqdn = vcc_123_channelizer_FQDN
        self._vcc_45_fqdn = vcc_45_channelizer_FQDN
        self._wib_fqdn = wideband_input_buffer_FQDN
        self._wfs_fqdn = wideband_frequency_shifter_FQDN
        # self._circuit_switch_fqdn = circuit_switch_FQDN
        self._fss_fqdn = fs_selection_FQDN

        self.simulation_mode = simulation_mode
        self.emulation_mode = emulation_mode

        self.input_sample_rate = 0

        self._proxies: dict[str, context.DeviceProxy] = {}

        self._proxies[mac_200_FQDN] = None
        self._proxies[packet_validation_FQDN] = None
        self._proxies[wideband_input_buffer_FQDN] = None
        self._proxies[wideband_frequency_shifter_FQDN] = None
        self._proxies[vcc_123_channelizer_FQDN] = None
        self._proxies[vcc_45_channelizer_FQDN] = None
        self._proxies[fs_selection_FQDN] = None
        # self._circuit_switch_proxy = None

        # vcc channels * number of polarizations
        self._num_vcc_gains = 0

        self._fsps = []
        self._maximum_fsps = 10

        self.frequency_band_offset = [0, 0]

        self.expected_dish_id = None

        # store the subscription event_ids here with a key (fqdn for deviceproxies)
        self.subscription_event_ids: dict[str, set[int]] = {}

        self.fhs_health_monitor = FhsHealthMonitor(
            logger=logger,
            get_device_health_state=self.get_device_health_state,
            update_health_state_callback=health_state_callback,
        )

        self.lrc_results = {}

        super().__init__(
            *args,
            logger=logger,
            attr_change_callback=attr_change_callback,
            attr_archive_callback=attr_archive_callback,
            health_state_callback=health_state_callback,
            obs_command_running_callback=obs_command_running_callback,
            max_queue_size=32,
            simulation_mode=simulation_mode,
            emulation_mode=emulation_mode,
            **kwargs,
        )

    def start_communicating(self: VCCAllBandsComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        try:
            if not self.simulation_mode:
                if self._communication_state == CommunicationStatus.ESTABLISHED:
                    self.logger.info("Already communicating.")
                    return

                self.logger.info("Establishing Communication with low-level proxies")

                for fqdn in self._proxies:
                    if fqdn != self._vcc_123_fqdn and fqdn != self._vcc_45_fqdn:
                        dp = context.DeviceProxy(device_name=fqdn)

                        # NOTE: this crashes when adminMode is memorized because it gets called before the devices are ready
                        self._subscribe_to_change_event(dp, "healthState", fqdn, self.proxies_health_state_change_event)
                        self._subscribe_to_change_event(dp, "longRunningCommandResult", fqdn, self._long_running_command_callback)
                        self._proxies[fqdn] = dp
                print(f"HEALTH_STATE REGISTERED EVENTS: {self.subscription_event_ids}")
                super().start_communicating()
        except tango.DevFailed as ex:
            self.logger.error(f"Failed connecting to FHS Low-level devices; {ex}")
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            return

    def stop_communicating(self: VCCAllBandsComponentManager) -> None:
        """Close communication with the component, then stop monitoring."""
        try:
            for fqdn in self._proxies:
                # unsubscribe from any attribute change events
                self._unsubscribe_from_events(fqdn)
                self._proxies[fqdn] = None

            # Event unsubscription will also be placed here
            super().stop_communicating()
        except tango.DevFailed as ex:
            self.logger.error(f"Failed close device proxies to FHS Low-level devices; {ex}")

    def is_go_to_idle_allowed(self: VCCAllBandsComponentManager) -> bool:
        self.logger.debug("Checking if gotoidle is allowed...")
        errorMsg = f"go_to_idle not allowed in ObsState {self.obs_state}; " "must be in ObsState.READY"

        return self.is_allowed(errorMsg, [ObsState.READY])

    def is_obs_reset_allowed(self: VCCAllBandsComponentManager) -> bool:
        self.logger.debug("Checking if ObsReset is allowed...")
        errorMsg = f"ObsReset not allowed in ObsState {self.obs_state}; \
            must be in ObsState.FAULT or ObsState.ABORTED"

        return self.is_allowed(errorMsg, [ObsState.FAULT, ObsState.ABORTED])

    def configure_scan(
        self: VCCAllBandsComponentManager,
        argin: str,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=self._configure_scan,
            args=[argin],
            task_callback=task_callback,
        )

    def go_to_idle(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="deconfigure",
                command_thread=self._go_to_idle,
            ),
            task_callback=task_callback,
            is_cmd_allowed=self.is_go_to_idle_allowed,
        )

    def obs_reset(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=functools.partial(
                self._obs_reset,
                from_state=self.obs_state,
            ),
            task_callback=task_callback,
            is_cmd_allowed=self.is_obs_reset_allowed,
        )

    def scan(self: VCCAllBandsComponentManager, argin: str, task_callback: Optional[Callable] = None) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="start",
                command_thread=self._scan,
            ),
            args=[argin],
            task_callback=task_callback,
        )

    # def end_scan(
    #     self: VCCAllBandsComponentManager,
    #     task_callback: Optional[Callable] = None,
    # ) -> tuple[TaskStatus, str]:
    #     return self.submit_task(
    #         func=functools.partial(
    #             self._obs_command_with_callback,
    #             hook="stop",
    #             command_thread=self._end_scan,
    #         ),
    #         task_callback=task_callback,
    #     )

    def end_scan(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=self.nullcmd,
            task_callback=task_callback,
        )

    def nullcmd(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """
        End scan operation.

        :return: None
        """
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)
            if self.task_abort_event_is_set("EndScan", task_callback, task_abort_event):
                return
            self._obs_state_action_callback(FhsObsStateMachine.COMPONENT_FAULT)

            # Update obsState callback
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "EndScan completed OK")
            return
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call EndScan command from an incorrect state",
            )

    def abort_commands(
        self: VCCAllBandsComponentManager,
        task_callback: TaskCallbackType | None = None,
    ) -> tuple[TaskStatus, str]:
        """
        Stop all devices.

        :return: None
        """
        self._obs_state_action_callback(FhsObsStateMachine.ABORT_INVOKED)
        result = super().abort_commands(task_callback)

        for fqdn, proxy in self._proxies.items():
            if proxy is not None and fqdn in [self._mac_200_fqdn, self._wib_fqdn, self._packet_validation_fqdn]:
                self.logger.info(f"Stopping proxy {fqdn}")
                result = proxy.Stop()

        self._obs_state_action_callback(FhsObsStateMachine.ABORT_COMPLETED)
        return result

    def _configure_scan(
        self: VCCAllBandsComponentManager,
        argin: str,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        try:
            """
            Read from JSON Config argin and setup VCC All bands with initial configuration from the control
            software
            """
            self._obs_state_action_callback(FhsObsStateMachine.CONFIGURE_INVOKED)
            task_callback(status=TaskStatus.IN_PROGRESS)
            configuration = json.loads(argin)
            jsonschema.validate(configuration, schema)
            if self.task_abort_event_is_set("ConfigureScan", task_callback, task_abort_event):
                return

            self._sample_rate = configuration["dish_sample_rate"]
            self._samples_per_frame = configuration["samples_per_frame"]
            self.frequency_band = freq_band_dict()[configuration["frequency_band"]]
            self.expected_dish_id = configuration["expected_dish_id"]
            self._config_id = configuration["config_id"]

            if "frequency_band_offset_stream_1" in configuration:
                self.frequency_band_offset[0] = configuration["frequency_band_offset_stream_1"]

            if "frequency_band_offset_stream_2" in configuration:
                self.frequency_band_offset[1] = configuration["frequency_band_offset_stream_2"]

            # VCC number of gains is equal to = number of channels * number of polizations
            self._vcc_gains = configuration["vcc_gain"]

            if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                # number of channels * number of polarizations
                self._num_vcc_gains = 10 * 2
            else:
                self._reset_attributes()
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.FAILED,
                    "Bands 5A/B not implemented",
                )
                return

            if len(self._vcc_gains) != self._num_vcc_gains:
                self._reset_attributes()
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.FAILED,
                    f"Incorrect number of gain values supplied: {self._vcc_gains} != {self._num_vcc_gains}",
                )
                return

            if not self.simulation_mode:
                if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                    self._proxies[self._vcc_123_fqdn] = context.DeviceProxy(device_name=self._vcc_123_fqdn)
                    result = self._proxies[self._vcc_123_fqdn].Configure(
                        json.dumps({"sample_rate": self._sample_rate, "gains": self._vcc_gains})
                    )

                    if result[0] == ResultCode.FAILED:
                        self.logger.error(f"Configuration of VCC123 Channelizer failed: {result[1]}")
                        self._reset_attributes()
                        self._set_task_callback(
                            task_callback,
                            TaskStatus.COMPLETED,
                            ResultCode.REJECTED,
                            "Configuration of low-level fhs device failed",
                        )
                        return

                else:
                    # TODO: Implement routing to the 5 Channelizer once outlined
                    self._reset_attributes()
                    self._set_task_callback(
                        task_callback,
                        TaskStatus.COMPLETED,
                        ResultCode.FAILED,
                        f"ConfigureScan failed unsupported band specified: {self.frequency_band}",
                    )
                    return

                # WFS Configuration
                result = self._proxies[self._wfs_fqdn].Configure(json.dumps({"shift_frequency": self.frequency_band_offset[0]}))
                if result[0] == ResultCode.FAILED:
                    self.logger.error(f"Configuration of Wideband Frequency Shifter failed: {result[1]}")
                    self._reset_devices([self._vcc_123_fqdn])
                    self._set_task_callback(
                        task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Configuration of low-level fhs device failed"
                    )
                    return

                # FSS Configuration
                result = self._proxies[self._fss_fqdn].Configure(
                    json.dumps({"band_select": self.frequency_band.value + 1, "band_start_channel": [0, 1]})
                )

                if result[0] == ResultCode.FAILED:
                    self.logger.error(f"Configuration of FS Selection failed: {result[1]}")
                    self._reset_devices([self._vcc_123_fqdn, self._wfs_fqdn])
                    self._set_task_callback(
                        task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Configuration of low-level fhs device failed"
                    )
                    return

                # WIB Configuration
                result = self._proxies[self._wib_fqdn].Configure(
                    json.dumps(
                        {
                            "expected_sample_rate": self._sample_rate,
                            "noise_diode_transition_holdoff_seconds": configuration["noise_diode_transition_holdoff_seconds"],
                            "expected_dish_band": self.frequency_band.value
                            + 1,  # FW Drivers rely on integer indexes, that are 1-based
                        }
                    )
                )

                if result[0] == ResultCode.FAILED:
                    self.logger.error(f"Configuration of WIB failed: {result[1]}")
                    self._reset_devices([self._vcc_123_fqdn, self._wfs_fqdn, self._fss_fqdn])
                    self._set_task_callback(
                        task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Configuration of low-level fhs device failed"
                    )
                    return

                self._proxies[self._wib_fqdn].expectedDishId = self.expected_dish_id

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ConfigureScan completed OK")
            self._obs_state_action_callback(FhsObsStateMachine.CONFIGURE_COMPLETED)
            return
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call ConfigureScan command from an incorrect state",
            )
        except jsonschema.ValidationError as ex:
            self.logger.error(f"Invalid json provided for ConfigureScan: {repr(ex)}")
            self._obs_state_action_callback(FhsObsStateMachine.GO_TO_IDLE)
            self._set_task_callback(
                task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for ConfigureScan"
            )
        except Exception as ex:
            self.logger.error(repr(ex))
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            self._obs_state_action_callback(FhsObsStateMachine.GO_TO_IDLE)
            self._set_task_callback(
                task_callback, TaskStatus.COMPLETED, ResultCode.FAILED, "Failed to establish proxies to HPS VCC devices"
            )

    def _scan(
        self: VCCAllBandsComponentManager,
        argin: int,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """
        Begin scan operation.

        :param argin: scan ID integer

        :return: None
        """
        try:
            # set task status in progress, check for abort event
            self._scan_id = argin
            if not self.simulation_mode:
                try:
                    self._proxies[self._mac_200_fqdn].Start()
                    self._proxies[self._packet_validation_fqdn].Start()
                    self._proxies[self._wib_fqdn].Start()
                except tango.DevFailed as ex:
                    self.logger.error(repr(ex))
                    self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
                    self._set_task_callback(
                        task_callback, TaskStatus.COMPLETED, ResultCode.FAILED, "Failed to establish proxies to FHS VCC devices"
                    )
                    return

            # Update obsState callback
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "Scan completed OK")
            return
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call Scan command from an incorrect state",
            )

    def _end_scan(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """
        End scan operation.

        :return: None
        """
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)
            if self.task_abort_event_is_set("EndScan", task_callback, task_abort_event):
                return

            if not self.simulation_mode:
                try:
                    self._proxies[self._mac_200_fqdn].Stop()
                    self._proxies[self._packet_validation_fqdn].Stop()
                    self._proxies[self._wib_fqdn].Stop()
                except tango.DevFailed as ex:
                    self.logger.error(repr(ex))
                    self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
                    self._set_task_callback(
                        task_callback, TaskStatus.COMPLETED, ResultCode.FAILED, "Failed to establish proxies to FHS VCC devices"
                    )
                    return

            # Update obsState callback
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "EndScan completed OK")
            return
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call EndScan command from an incorrect state",
            )

    # A replacement for unconfigure
    def _go_to_idle(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        try:
            # TODO: Check if ReceiveEnable is still required on the Agilex for the WIB
            task_callback(status=TaskStatus.IN_PROGRESS)
            if self.task_abort_event_is_set("GoToIdle", task_callback, task_abort_event):
                return

            # Reset all device proxies
            self._reset_devices(self._proxies.keys())

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "GoToIdle completed OK")
            return
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call GoToIdle command from an incorrect state",
            )
        except Exception as ex:
            self.logger.error(f"ERROR SETTING GO_TO_IDLE: {repr(ex)}")

    def _obs_reset(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
        from_state=ObsState.ABORTED,
    ) -> None:
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)
            if self.task_abort_event_is_set("ObsReset", task_callback, task_abort_event):
                return

            # If in FAULT state, must run Abort first to make sure all LL devices are actually stopped
            if from_state is ObsState.FAULT:
                self.abort_commands()

                t = 10
                while t > 0:
                    self.logger.warning("@@@@@@@@@@@@@@@@@@@@ POLLING MAC LRC")
                    self.logger.warning(self.lrc_results.get(self._mac_200_fqdn) or "NOTHING")
                    time.sleep(1)
                    t -= 1

                # TODO: poll state instead of sleeping?
                time.sleep(5)

            self._obs_state_action_callback(FhsObsStateMachine.OBSRESET_INVOKED)

            # Reset all device proxies
            self._reset_devices(self._proxies.keys())

            self._obs_state_action_callback(FhsObsStateMachine.OBSRESET_COMPLETED)
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ObsReset completed OK")
            return
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call ObsReset command from an incorrect state",
            )
        except Exception as ex:
            self.logger.error(f"Unexpected error in ObsReset command: {repr(ex)}")

    def _reset_attributes(self: VCCAllBandsComponentManager):
        self._config_id = ""
        self._scan_id = 0
        self.frequency_band = FrequencyBandEnum._1
        self.frequency_band_offset = [0, 0]
        self._sample_rate = 0
        self._samples_per_frame = 0
        self._fsps = []

    def _reset_devices(self: VCCAllBandsComponentManager, devices_name: list[str]):
        try:
            self._reset_attributes()
            for fqdn in devices_name:
                if self._proxies[fqdn] is not None:
                    self._log_go_to_idle_status(fqdn, self._proxies[fqdn].GoToIdle())
        except Exception as ex:
            self.logger.error(f"Error resetting specific devices : {repr(ex)}")

    def task_abort_event_is_set(
        self: VCCAllBandsComponentManager,
        command_name: str,
        task_callback: Callable,
        task_abort_event: Event,
    ) -> bool:
        """
        Helper method for checking task abort event during command thread.

        :param command_name: name of command for result message
        :param task_callback: command tracker update_command_info callback
        :param task_abort_event: task executor abort event

        :return: True if abort event is set, otherwise False
        """
        if task_abort_event.is_set():
            task_callback(
                status=TaskStatus.ABORTED,
                result=(
                    ResultCode.ABORTED,
                    f"{command_name} command aborted by task executor abort event.",
                ),
            )
            return True
        return False

    def _log_go_to_idle_status(self: VCCAllBandsComponentManager, ip_block_name: str, result: tuple[ResultCode, str]):
        if result[0] != ResultCode.OK:
            self.logger.error(f"VCC {self._vcc_id}: Unable to set to IDLE state for ipblock {ip_block_name}")
        else:
            self.logger.info(f"VCC {self._vcc_id}: {ip_block_name} set to IDLE")

    def _subscribe_to_change_event(
        self: VCCAllBandsComponentManager,
        device_proxy,
        attribute: str,
        key: str,
        change_event_callback: Callable[[EventData], None],
    ):
        event_id = device_proxy.subscribe_event(attribute, EventType.CHANGE_EVENT, change_event_callback)
        if key in self.subscription_event_ids:
            self.subscription_event_ids[key].add(event_id)
        else:
            self.subscription_event_ids[key] = {event_id}

    def _unsubscribe_from_events(self: VCCAllBandsComponentManager, fqdn: str):
        if fqdn in self.subscription_event_ids and fqdn in self._proxies and self._proxies[fqdn] is not None:
            for event_id in self.subscription_event_ids[fqdn]:
                try:
                    self._proxies[fqdn].unsubscribe_event(event_id)
                except Exception as ex:
                    self.logger.error(f"Unable to unsubcribe from event {event_id} for device server {fqdn}: {repr(ex)}")

    def proxies_health_state_change_event(self: VCCAllBandsComponentManager, event_data: EventData):
        if event_data.err:
            self.logger.error(
                f"Problem occured when recieving healthState event for {event_data.device.dev_name()}. Unable to determine health state"
            )
            self.fhs_health_monitor.add_health_state(event_data.device.dev_name(), HealthState.UNKNOWN)
        else:
            self.fhs_health_monitor.add_health_state(event_data.device.dev_name(), event_data.attr_value.value)

    def _long_running_command_callback(self: VCCAllBandsComponentManager, event: EventData):
        id, result = event.attr_value.value
        self.lrc_results[event.device.get_fqdn()] = result

        self.logger.info(f"@@@@@@@@@@@@@@@@@@@@ LRC: device.get_fqdn = {event.device.get_fqdn()}")
        self.logger.info(f"@@@@@@@@@@@@@@@@@@@@ LRC: lrc_results now = {self.lrc_results}")

        self.logger.info(
            f"VCC {self._vcc_id}: Long running command '{id}' on '{event.device.name()}' completed with result '{result}'"
        )
        if event.err:
            self.logger.error(f"VCC {self._vcc_id}: Long running command failed {event.errors}")
