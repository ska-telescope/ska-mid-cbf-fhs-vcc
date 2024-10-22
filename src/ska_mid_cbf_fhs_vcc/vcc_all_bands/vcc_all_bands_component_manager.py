from __future__ import annotations

import functools
import json
import logging
from threading import Event
from typing import Any, Callable, Optional

import tango
from ska_control_model import CommunicationStatus, HealthState, ResultCode, SimulationMode, TaskStatus
from ska_tango_testing import context

from ska_mid_cbf_fhs_vcc.common.fhs_component_manager_base import FhsComponentManagerBase
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_helpers import FrequencyBandEnum, freq_band_dict


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

        self.frequency_band = "1"

        self._mac_200_fqdn = mac_200_FQDN
        self._config_id = ""
        self._scan_id = 0
        self._packet_validation_fqdn = packet_validation_FQDN
        self._vcc_123_channelizer_fqdn = vcc_123_channelizer_FQDN
        self._vcc_45_channelizer_fqdn = vcc_45_channelizer_FQDN
        self._wideband_input_buffer_fqdn = wideband_input_buffer_FQDN
        self._wideband_frequency_shifter_fqdn = wideband_frequency_shifter_FQDN
        # self._circuit_switch_fqdn = circuit_switch_FQDN
        self._fs_selection_fqdn = fs_selection_FQDN

        self.simulation_mode = simulation_mode
        self.emulation_mode = emulation_mode

        self.input_sample_rate = 0

        self._mac_proxy = None
        self._vcc_123_channelizer_proxy = None
        self._packet_validation_proxy = None
        self._mac_200_proxy = None
        self._vcc_45_channelizer_proxy = None
        self._wideband_input_buffer_proxy = None
        self._wideband_frequency_shifter_proxy = None
        # self._circuit_switch_proxy = None
        self._fs_selection_proxy = None

        # vcc channels * number of polarizations
        self._num_vcc_gains = 0

        self._fsps = []
        self._maximum_fsps = 10

        self.frequency_band_offset = [0, 0]

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

                self._fs_selection_proxy = context.DeviceProxy(device_name=self._fs_selection_fqdn)
                self._wideband_frequency_shifter_proxy = context.DeviceProxy(device_name=self._wideband_frequency_shifter_fqdn)
                self._wideband_input_buffer_proxy = context.DeviceProxy(device_name=self._wideband_input_buffer_fqdn)
                self._mac_200_proxy = context.DeviceProxy(device_name=self._mac_200_fqdn)
                self._packet_validation_proxy = context.DeviceProxy(device_name=self._packet_validation_fqdn)

                super().start_communicating()
        except tango.DevFailed as ex:
            self.logger.error(f"Failed connecting to FHS Low-level devices; {ex}")
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            return

    def stop_communicating(self: VCCAllBandsComponentManager) -> None:
        """Close communication with the component, then stop monitoring."""
        try:
            self._fs_selection_proxy = {}
            self._wideband_frequency_shifter_proxy = {}
            self._wideband_input_buffer_proxy = {}
            self._mac_200_proxy = {}
            self._packet_validation_proxy = {}

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
                hook="starting",
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
                hook="stopping",
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
            configuration = json.loads(argin)
            task_callback(status=TaskStatus.IN_PROGRESS)
            if self.task_abort_event_is_set("ConfigureScan", task_callback, task_abort_event):
                return

            self._sample_rate = configuration["dish_sample_rate"]
            self._samples_per_frame = configuration["samples_per_frame"]
            self.frequency_band = freq_band_dict()[configuration["frequency_band"]]
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
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.FAILED,
                    "Bands 5A/B not implemented",
                )
                return

            if len(self._vcc_gains) != self._num_vcc_gains:
                # Implement error handling
                self._set_task_callback(
                    task_callback,
                    TaskStatus.COMPLETED,
                    ResultCode.FAILED,
                    f"Incorrect number of gain values supplied: {self._vcc_gains} != {self._num_vcc_gains}",
                )
                return

            if not self.simulation_mode:
                if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                    self._vcc_123_channelizer_proxy = context.DeviceProxy(device_name=self._vcc_123_channelizer_fqdn)
                    self._vcc_123_channelizer_proxy.Configure(
                        json.dumps({"sample_rate": self._sample_rate, "gains": self._vcc_gains})
                    )
                else:
                    # TODO: Implement routing to the 5 Channelizer once outlined
                    self._set_task_callback(
                        task_callback,
                        TaskStatus.COMPLETED,
                        ResultCode.FAILED,
                        f"ConfigureScan failed unsupported band specified: {self.frequency_band}",
                    )
                    return

            if not self.simulation_mode:
                self._wideband_frequency_shifter_proxy.Configure(json.dumps({"shift_frequency": self.frequency_band_offset[0]}))

                # TODO: understand mechanism for logic behind start channel indexes
                # FSS outputs 26 coarse channels, channelizers have the potential in bands 4/5 to output 30 total, 15 per 4/5 channelizer
                # starting index mitigates the additional coarse channels.
                # band_start_channel[0] -> starting channel for B123 or B45.1
                # band_start_channel[1] -> starting channel for B45.2
                self._fs_selection_proxy.Configure(
                    json.dumps({"band_select": self.frequency_band.value + 1, "band_start_channel": [0, 1]})
                )

                self._wideband_input_buffer_proxy.Configure(
                    json.dumps(
                        {
                            "expected_sample_rate": self._sample_rate,
                            "noise_diode_transition_holdoff_seconds": configuration["noise_diode_transition_holdoff_seconds"],
                            "expected_dish_band": self.frequency_band.value
                            + 1,  # FW Drivers rely on integer indexes, that are 1-based
                        }
                    )
                )

            # TODO: Restore a version of below when Circuit Switch is re-integrated
            # if len(configuration["fsp"]) > 0:
            #     for fsp in configuration["fsp"]:
            #         if fsp["fsp_id"] < 0 or len(self._fsps) > self._maximum_fsps:
            #             # throw exception
            #             return

            #         self._fsps.append(fsp)

            #     # fss_input_size = 4 # TODO: Implement when FSS interface is complete
            #     # TODO Understand the FSS better as it appears to be less like a Circuit Switch than initially thought
            #     #if self.simulation_mode == False:
            #         #input_select = self._circuit_switch_proxy.Status()
            #         #fss_input_size = input_select.get_max_dim_x()

            #     inputs = [None] * fss_input_size
            #     for fsp in self._fsps:
            #         if fsp["frequency_slice_id"] == 0 or fsp["frequency_slice_id"] > fss_input_size:
            #             return
            #         inputs[fsp["fsp_id"]-1] = {"input": fsp["fsp_id"], "output": fsp["frequency_slice_id"]
            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ConfigureScan completed OK")
            self._update_component_state(configuring=False)
            return
        except Exception as ex:
            self.logger.error(repr(ex))
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            self._update_component_state(configuring=False)
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
                self._mac_200_proxy.Start()
                self._packet_validation_proxy.Start()
                self._wideband_input_buffer_proxy.Start()
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
                self._mac_200_proxy.Stop()
                self._packet_validation_proxy.Stop()
                self._wideband_input_buffer_proxy.Stop()
            except tango.DevFailed as ex:
                self.logger.error(repr(ex))
                self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
                self._set_task_callback(
                    task_callback, TaskStatus.COMPLETED, ResultCode.FAILED, "Failed to establish proxies to FHS VCC devices"
                )
                return

        # Update obsState callback
        self._update_component_state(scanning=False)
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

            # Reset attributes to the defaults
            self._config_id = ""
            self._scan_id = 0
            self.frequency_band = FrequencyBandEnum._1
            self.frequency_band_offset = [0, 0]
            self._sample_rate = 0
            self._samples_per_frame = 0
            self._fsps = []

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "GoToIdle completed OK")

            self._log_go_to_idle_status("VCC-B123", self._vcc_123_channelizer_proxy.GoToIdle())
            self._log_go_to_idle_status("WIB", self._wideband_input_buffer_proxy.GoToIdle())
            self._log_go_to_idle_status("WFS", self._wideband_frequency_shifter_proxy.GoToIdle())
            self._log_go_to_idle_status("FSS", self._fs_selection_proxy.GoToIdle())
            self._log_go_to_idle_status("PV", self._packet_validation_proxy.GoToIdle())
            self._log_go_to_idle_status("Mac200", self._mac_200_proxy.GoToIdle())
            return
        except Exception as ex:
            self.logger.error(f"ERROR SETTING GO_TO_IDLE: {repr(ex)}")

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
