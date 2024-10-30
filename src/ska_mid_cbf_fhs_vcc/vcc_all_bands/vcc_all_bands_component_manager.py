from __future__ import annotations

import functools
import json
import logging
from threading import Event
from typing import Any, Callable, Optional, Dict, List

import jsonschema
import tango
from ska_control_model import CommunicationStatus, HealthState, ResultCode, SimulationMode, TaskStatus
from ska_tango_testing import context

from ska_mid_cbf_fhs_vcc.common.fhs_component_manager_base import FhsComponentManagerBase
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
        
        self._proxies: Dict[str, context.DeviceProxy] = {}

        self._proxies[mac_200_FQDN] = None
        self._proxies[packet_validation_FQDN] = None
        self._proxies[wideband_input_buffer_FQDN] = None
        self._proxies[vcc_123_channelizer_FQDN] = None
        self._proxies[vcc_45_channelizer_FQDN] = None
        self._proxies[fs_selection_FQDN] = None
        # self._circuit_switch_proxy = None
        self._fs_selection_proxy = None

        # vcc channels * number of polarizations
        self._num_vcc_gains = 0

        self._fsps = []
        self._maximum_fsps = 10

        self.frequency_band_offset = [0, 0]

        self.expected_dish_id = None

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
                    if fqdn != self._vcc_123_fqdn or fqdn != self._vcc_45_fqdn:
                        self._proxies[fqdn] = context.DeviceProxy(device_name=fqdn)
                # self._fs_selection_proxy = context.DeviceProxy(device_name=self._fs_selection_fqdn)
                # self._wideband_frequency_shifter_proxy = context.DeviceProxy(device_name=self._wideband_frequency_shifter_fqdn)
                # self._wideband_input_buffer_proxy = context.DeviceProxy(device_name=self._wideband_input_buffer_fqdn)
                # self._mac_200_proxy = context.DeviceProxy(device_name=self._mac_200_fqdn)
                # self._packet_validation_proxy = context.DeviceProxy(device_name=self._packet_validation_fqdn)

                super().start_communicating()
        except tango.DevFailed as ex:
            self.logger.error(f"Failed connecting to FHS Low-level devices; {ex}")
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            return

    def stop_communicating(self: VCCAllBandsComponentManager) -> None:
        """Close communication with the component, then stop monitoring."""
        try:
            for fqdn in self._proxies:
                self._proxies[fqdn] = None

            # Event unsubscription will also be placed here
            super().stop_communicating()
        except tango.DevFailed as ex:
            self.logger.error(f"Failed close device proxies to FHS Low-level devices; {ex}")

    def configure_scan(
        self: VCCAllBandsComponentManager,
        argin: str,
        task_callback: Optional[Callable] = None,
    ) -> tuple[TaskStatus, str]:
        return self.submit_task(
            func=functools.partial(self._configure_scan),
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
            self._update_component_state(configuring=True)
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
                        self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Configuration of low-level fhs device failed")
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
                    self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Configuration of low-level fhs device failed")
                    return
                
                # FSS Configuration
                result = self._proxies[self._fss_fqdn].Configure(
                    json.dumps({"band_select": self.frequency_band.value + 1, "band_start_channel": [0, 1]})
                )
                
                if result[0] == ResultCode.FAILED:
                    self.logger.error(f"Configuration of FS Selection failed: {result[1]}")
                    self._reset_devices([self._vcc_123_fqdn, self._wfs_fqdn])
                    self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Configuration of low-level fhs device failed")
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
                    self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Configuration of low-level fhs device failed")
                    return
                    
                self._proxies[self._wib_fqdn].expected_dish_id = self.expected_dish_id

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ConfigureScan completed OK")
            self._update_component_state(configuring=False)
            return
        except jsonschema.ValidationError as ex:
            self.logger.error(f"Invalid json provided for ConfigureScan: {repr(ex)}")
            self._update_component_state(idle=True)
            self._set_task_callback(
                task_callback, TaskStatus.COMPLETED, ResultCode.REJECTED, "Arg provided does not match schema for ConfigureScan"
            )
            return
        except Exception as ex:
            self.logger.error(repr(ex))
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            self._update_component_state(idle=True)
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

    def _end_scan(
        self: VCCAllBandsComponentManager,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        """
        End scan operation.

        :return: None
        """
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
        except Exception as ex:
            self.logger.error(f"ERROR SETTING GO_TO_IDLE: {repr(ex)}")
    
    def _reset_attributes(self: VCCAllBandsComponentManager):
        self._config_id = ""
        self._scan_id = 0
        self.frequency_band = FrequencyBandEnum._1
        self.frequency_band_offset = [0, 0]
        self._sample_rate = 0
        self._samples_per_frame = 0
        self._fsps = []
         
    def _reset_devices(self: VCCAllBandsComponentManager, devices_name: List[str]):
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
