from __future__ import annotations

import functools
import json
import logging
from threading import Event
from typing import Any, Callable, Optional

import jsonschema
import tango
from ska_control_model import CommunicationStatus, HealthState, ObsState, ResultCode, SimulationMode, TaskStatus
from ska_control_model.faults import StateModelError
from ska_mid_cbf_fhs_common import FhsBaseDevice, FhsComponentManagerBase, FhsHealthMonitor, FhsObsStateMachine
from ska_tango_base.base.base_component_manager import TaskCallbackType
from ska_tango_testing import context
from tango import EventData, EventType

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_helpers import FrequencyBandEnum, freq_band_dict

from .vcc_all_bands_config import schema


class VCCAllBandsComponentManager(FhsComponentManagerBase):
    def __init__(
        self: VCCAllBandsComponentManager,
        *args: Any,
        device: FhsBaseDevice,
        logger: logging.Logger,
        simulation_mode: SimulationMode = SimulationMode.FALSE,
        attr_change_callback: Callable[[str, Any], None] | None = None,
        attr_archive_callback: Callable[[str, Any], None] | None = None,
        health_state_callback: Callable[[HealthState], None] | None = None,
        obs_command_running_callback: Callable[[str, bool], None],
        emulation_mode: bool = False,
        **kwargs: Any,
    ) -> None:
        self.device = device
        self._vcc_id = device.device_id

        self.frequency_band = FrequencyBandEnum._1
        self._config_id = ""
        self._scan_id = 0

        self.simulation_mode = simulation_mode
        self.emulation_mode = emulation_mode

        self.input_sample_rate = 0

        self._proxies: dict[str, context.DeviceProxy] = {}

        self._proxies[device.ethernet_200g_fqdn] = None
        self._proxies[device.packet_validation_fqdn] = None
        self._proxies[device.wideband_input_buffer_fqdn] = None
        self._proxies[device.wideband_frequency_shifter_fqdn] = None
        self._proxies[device.vcc123_channelizer_fqdn] = None
        # self._proxies[device.vcc45_channelizer_fqdn] = None
        self._proxies[device.fs_selection_fqdn] = None
        self._proxies[device.b123_wideband_power_meter_fqdn] = None
        self._proxies[device.b45a_wideband_power_meter_fqdn] = None
        self._proxies[device.b5b_wideband_power_meter_fqdn] = None

        self._power_meter_fqdns = {
            i: device.fs_wideband_power_meter_fqdn.replace("<multiplicity>", str(i)) for i in range(1, 26 + 1)
        }
        for fqdn in self._power_meter_fqdns.values():
            self._proxies[fqdn] = None

        self._vcc_stream_merge_fqdns = {
            i: device.vcc_stream_merge_fqdn.replace("<multiplicity>", str(i)) for i in range(1, 3)
        }
        for fqdn in self._vcc_stream_merge_fqdns.values():
            self._proxies[fqdn] = None

        # self._circuit_switch_proxy = None

        # vcc channels * number of polarizations
        self._num_vcc_gains = 0

        self._fsps = []
        self._maximum_fsps = 10

        self.frequency_band_offset = [0, 0]

        self._expected_dish_id = None

        # store the subscription event_ids here with a key (fqdn for deviceproxies)
        self.subscription_event_ids: dict[str, set[int]] = {}

        self.fhs_health_monitor = FhsHealthMonitor(
            logger=logger,
            get_device_health_state=self.get_device_health_state,
            update_health_state_callback=health_state_callback,
        )

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

                for fqdn, dp in self._proxies.items():
                    if dp is None:
                        self.logger.info(f"Establishing Communication with {fqdn}")
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
                self._obs_command_with_callback,
                hook="obsreset",
                command_thread=functools.partial(
                    self._obs_reset,
                    from_state=self.obs_state,
                ),
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

    def end_scan(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="stop",
                command_thread=self._end_scan,
            ),
            task_callback=task_callback,
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

        result = self._stop_proxies()

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
            self._expected_dish_id = configuration["expected_dish_id"]
            self._config_id = configuration["config_id"]
            self.logger.info(
                f"Configuring VCC {self._vcc_id} - Config ID: {self._config_id}, Freq Band: {self.frequency_band.value}"
            )

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
                raise ValueError("Bands 5A/B not implemented")

            if len(self._vcc_gains) != self._num_vcc_gains:
                self._reset_attributes()
                raise ValueError(f"Incorrect number of gain values supplied: {self._vcc_gains} != {self._num_vcc_gains}")

            if not self.simulation_mode:
                # VCC123 Channelizer Configuration
                self.logger.debug("VCC123 Channelizer Configuring..")
                if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                    result = self._proxies[self.device.vcc123_channelizer_fqdn].Configure(
                        json.dumps({"sample_rate": self._sample_rate, "gains": self._vcc_gains})
                    )

                    if result[0] == ResultCode.FAILED:
                        self.logger.error(f"Configuration of VCC123 Channelizer failed: {result[1]}")
                        self._reset_attributes()
                        raise ChildProcessError("Configuration of low-level fhs device failed: VCC123")

                else:
                    # TODO: Implement routing to the 5 Channelizer once outlined
                    self._reset_attributes()
                    raise ValueError(f"ConfigureScan failed unsupported band specified: {self.frequency_band}")

                # WFS Configuration
                self.logger.debug("Wideband Frequency Shifter Configuring..")
                result = self._proxies[self.device.wideband_frequency_shifter_fqdn].Configure(
                    json.dumps({"shift_frequency": self.frequency_band_offset[0]})
                )
                if result[0] == ResultCode.FAILED:
                    self.logger.error(f"Configuration of Wideband Frequency Shifter failed: {result[1]}")
                    self._reset_devices([self.device.vcc123_channelizer_fqdn])
                    raise ChildProcessError("Configuration of low-level fhs device failed: Wideband Frequency Shifter")

                # FSS Configuration
                result = self._proxies[self.device.fs_selection_fqdn].Configure(
                    json.dumps({"band_select": self.frequency_band.value + 1, "band_start_channel": [0, 1]})
                )

                if result[0] == ResultCode.FAILED:
                    self.logger.error(f"Configuration of FS Selection failed: {result[1]}")
                    self._reset_devices([self.device.vcc123_channelizer_fqdn, self.device.wideband_frequency_shifter_fqdn])
                    raise ChildProcessError("Configuration of low-level fhs device failed: FS Selection")

                # WIB Configuration
                self.logger.debug("Wideband Input Buffer Configuring..")
                result = self._proxies[self.device.wideband_input_buffer_fqdn].Configure(
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
                    self._reset_devices(
                        [
                            self.device.vcc123_channelizer_fqdn,
                            self.device.wideband_frequency_shifter_fqdn,
                            self.device.fs_selection_fqdn,
                        ]
                    )
                    raise ChildProcessError("Configuration of low-level fhs device failed: WIB")

                self._proxies[self.device.wideband_input_buffer_fqdn].expectedDishId = self._expected_dish_id

                # Pre-channelizer WPM Configuration
                self.logger.debug("Pre-channelizer Wideband Power Meters Configuring..")
                self._b123_pwrm = configuration["b123_pwrm"]
                self._b45a_pwrm = configuration["b45a_pwrm"]
                self._b5b_pwrm = configuration["b5b_pwrm"]

                for (
                    fqdn,
                    config,
                ) in [
                    (self.device.b123_wideband_power_meter_fqdn, self._b123_pwrm),
                    (self.device.b45a_wideband_power_meter_fqdn, self._b45a_pwrm),
                    (self.device.b5b_wideband_power_meter_fqdn, self._b5b_pwrm),
                ]:
                    self.logger.debug(f"Configuring {fqdn} with {config}")
                    result = self._proxies[fqdn].Configure(
                        json.dumps(
                            {
                                "averaging_time": config["averaging_time"],
                                "sample_rate": self._sample_rate,
                                "flagging": config["flagging"],
                            }
                        )
                    )
                    if result[0] == ResultCode.FAILED:
                        self.logger.error(f"Configuration of Wideband Power Meter failed: {result[1]}")
                        self._reset_devices(
                            [
                                self.device.vcc123_channelizer_fqdn,
                                self.device.wideband_frequency_shifter_fqdn,
                                self.device.fs_selection_fqdn,
                                self.device.wideband_input_buffer_fqdn,
                            ]
                        )
                        raise ChildProcessError("Configuration of low-level fhs device failed: Wideband Power Meter")

                # Post-channelizer WPM Configuration
                self.logger.debug("Post-channelizer Wideband Power Meters Configuring..")
                self._fs_lanes = configuration["fs_lanes"]

                # Verify vlan_id is within range
                # ((config.vid >= 2 && config.vid <= 1001) || (config.vid >= 1006 && config.vid <= 4094))
                for config in self._fs_lanes:
                    if not (2 <= config["vlan_id"] <= 1001 or 1006 <= config["vlan_id"] <= 4094):
                        raise ValueError(f"VLAN ID {config['vlan_id']} is not within range")

                for config in self._fs_lanes:
                    fqdn = self._power_meter_fqdns[int(config["fs_id"])]
                    self.logger.debug(f"Configuring {fqdn} with {config}")
                    result = self._proxies[fqdn].Configure(
                        json.dumps(
                            {
                                "averaging_time": config["averaging_time"],
                                "sample_rate": self._sample_rate,
                                "flagging": config["flagging"],
                            }
                        )
                    )
                    if result[0] == ResultCode.FAILED:
                        self.logger.error(f"Configuration of Wideband Power Meter failed: {result[1]}")
                        self._reset_devices(
                            [
                                self.device.vcc123_channelizer_fqdn,
                                self.device.wideband_frequency_shifter_fqdn,
                                self.device.fs_selection_fqdn,
                                self.device.wideband_input_buffer_fqdn,
                                self.device.b123_wideband_power_meter_fqdn,
                                self.device.b45a_wideband_power_meter_fqdn,
                                self.device.b5b_wideband_power_meter_fqdn,
                            ]
                        )
                        raise ChildProcessError("Configuration of low-level fhs device failed: FS Power Meter")

                # VCC Stream Merge Configuration
                self.logger.debug("VCC Stream Merge Configuring..")
                for i, lane in enumerate(self._fs_lanes):
                    result = self._proxies[self._vcc_stream_merge_fqdns[i // 13 + 1]].Configure(json.dumps({
                        "vid": lane["vlan_id"],
                        "vcc_id": self._vcc_id,
                        "fs_id": lane["fs_id"]
                    }))
                    if result[0] == ResultCode.FAILED:
                        self.logger.error(f"Configuration of VCC Stream Merge failed: {result[1]}")
                        self._reset_devices([*self._vcc_stream_merge_fqdns.values()])
                        raise ChildProcessError("Configuration of low-level fhs device failed: VCC Stream Merge")

            self.logger.info(f"Sucessfully completed ConfigureScan for Config ID: {self._config_id}")
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
        except ValueError as ex:
            self.logger.error(f"Error due to config not meeting scan requirements: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                f"Arg provided does not meet ConfigureScan criteria: {ex}",
            )
        except ChildProcessError as ex:
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, ex)
        except jsonschema.ValidationError as ex:
            self.logger.error(f"Invalid json provided for ConfigureScan: {repr(ex)}")
            self._obs_state_action_callback(FhsObsStateMachine.GO_TO_IDLE)
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                f"Arg provided does not meet ConfigureScan criteria: {ex}",
            )
        except Exception as ex:
            self.logger.error(repr(ex))
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            self._obs_state_action_callback(FhsObsStateMachine.GO_TO_IDLE)
            self._set_task_callback(
                task_callback, TaskStatus.COMPLETED, ResultCode.FAILED, "Failed to an unexpected exception during ConfigureScan"
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
                    self._proxies[self.device.ethernet_200g_fqdn].Start()
                    self._proxies[self.device.packet_validation_fqdn].Start()
                    self._proxies[self.device.wideband_input_buffer_fqdn].Start()
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
                    self._proxies[self.device.ethernet_200g_fqdn].Stop()
                    self._proxies[self.device.packet_validation_fqdn].Stop()
                    self._proxies[self.device.wideband_input_buffer_fqdn].Stop()
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

            # If in FAULT state, devices may still be running, so make sure they are stopped
            if from_state is ObsState.FAULT:
                self._stop_proxies()

            # Reset all device proxies
            self._reset_devices(self._proxies.keys())

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

    def _stop_proxies(self: VCCAllBandsComponentManager):
        result = None
        for fqdn, proxy in self._proxies.items():
            if proxy is not None and fqdn in [
                self.device.ethernet_200g_fqdn,
                self.device.wideband_input_buffer_fqdn,
                self.device.packet_validation_fqdn,
            ]:
                self.logger.info(f"Stopping proxy {fqdn}")
                result = proxy.Stop()
        return result

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

        self.logger.info(
            f"VCC {self._vcc_id}: Long running command '{id}' on '{event.device.name()}' completed with result '{result}'"
        )
        if event.err:
            self.logger.error(f"VCC {self._vcc_id}: Long running command failed {event.errors}")
