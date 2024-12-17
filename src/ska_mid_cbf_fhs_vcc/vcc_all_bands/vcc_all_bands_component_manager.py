from __future__ import annotations

import asyncio
import functools
import json
import logging
from threading import Event
from typing import Any, Callable, Optional

import jsonschema
import tango
from ska_control_model import CommunicationStatus, HealthState, ObsState, ResultCode, SimulationMode, TaskStatus
from ska_control_model.faults import StateModelError
from ska_tango_base.base.base_component_manager import TaskCallbackType
from ska_tango_testing import context
from tango import EventData, EventType, GreenMode
from tango.asyncio import DeviceProxy
from tango.device_proxy import get_device_proxy

from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice
from ska_mid_cbf_fhs_vcc.common.fhs_component_manager_base import FhsComponentManagerBase
from ska_mid_cbf_fhs_vcc.common.fhs_health_monitor import FhsHealthMonitor
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine
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

        self._proxies: dict[str, DeviceProxy] = {}

        self._proxies[device.mac_200_fqdn] = None
        self._proxies[device.packet_validation_fqdn] = None
        self._proxies[device.wideband_input_buffer_fqdn] = None
        self._proxies[device.wideband_frequency_shifter_fqdn] = None
        self._proxies[device.vcc123_channelizer_fqdn] = None
        # self._proxies[device.vcc45_channelizer_fqdn] = None
        self._proxies[device.fs_selection_fqdn] = None
        self._proxies[device.b123_wideband_power_meter_fqdn] = None
        self._proxies[device.b45a_wideband_power_meter_fqdn] = None
        self._proxies[device.b5b_wideband_power_meter_fqdn] = None
        self._proxies[device.packetizer_fqdn] = None

        self._power_meter_fqdns = {
            i: device.fs_wideband_power_meter_fqdn.replace("<multiplicity>", str(i)) for i in range(1, 26 + 1)
        }
        for fqdn in self._power_meter_fqdns.values():
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

    async def start_communicating(self: VCCAllBandsComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        try:
            if not self.simulation_mode:
                if self._communication_state == CommunicationStatus.ESTABLISHED:
                    self.logger.info("Already communicating.")
                    return

                self.logger.info("Establishing Communication with low-level proxies")

                async def _connect_device(fqdn: str):
                    self.logger.info(f"Establishing Communication with {fqdn}")
                    dp = await DeviceProxy(fqdn, wait=False)
                    # NOTE: this crashes when adminMode is memorized because it gets called before the devices are ready
                    await self._subscribe_to_change_event(dp, "healthState", fqdn, self._proxies_health_state_change_event)
                    await self._subscribe_to_change_event(
                        dp, "longRunningCommandResult", fqdn, self._long_running_command_callback
                    )
                    self.logger.info(f"Connected to {fqdn}")
                    self._proxies[fqdn] = dp

                await asyncio.gather(*[_connect_device(fqdn) for fqdn, dp in self._proxies.items() if dp is None])
                print(f"HEALTH_STATE REGISTERED EVENTS: {self.subscription_event_ids}")
                super().start_communicating()
        except tango.DevFailed as ex:
            self.logger.error(f"Failed connecting to FHS Low-level devices; {ex}")
            self._update_communication_state(communication_state=CommunicationStatus.NOT_ESTABLISHED)
            return

    async def stop_communicating(self: VCCAllBandsComponentManager) -> None:
        """Close communication with the component, then stop monitoring."""
        try:
            for fqdn in self._proxies:
                # unsubscribe from any attribute change events
                await self._unsubscribe_from_events(fqdn)
                self._proxies[fqdn] = None

            # Event unsubscription will also be placed here
            super().stop_communicating()
        except tango.DevFailed as ex:
            self.logger.error(f"Failed close device proxies to FHS Low-level devices; {ex}")

    def configure_scan(self: VCCAllBandsComponentManager, argin: str, task_callback: TaskCallbackType) -> tuple[TaskStatus, str]:
        self._asyncio_tasks.append(asyncio.create_task(self._configure_scan(argin, task_callback=task_callback)))
        return (TaskStatus.QUEUED, "ConfigureScan queued")

    def go_to_idle(self: VCCAllBandsComponentManager, task_callback: TaskCallbackType) -> tuple[TaskStatus, str]:
        if self.obs_state in [ObsState.READY]:
            self._asyncio_tasks.append(
                asyncio.create_task(
                    self._obs_command_with_callback(
                        hook="deconfigure", command_thread=self._go_to_idle, task_callback=task_callback
                    )
                )
            )
            return (TaskStatus.QUEUED, "GoToIdle queued")
        else:
            errorMsg = f"GoToIdle not allowed in ObsState {self.obs_state}; must be in ObsState.READY"
            self.logger.warning(errorMsg)
            return (TaskStatus.REJECTED, errorMsg)

    def obs_reset(self: VCCAllBandsComponentManager, task_callback: TaskCallbackType) -> tuple[TaskStatus, str]:
        if self.obs_state in [ObsState.FAULT, ObsState.ABORTED]:
            self._asyncio_tasks.append(
                asyncio.create_task(
                    self._obs_command_with_callback(
                        hook="obsreset",
                        command_thread=functools.partial(self._obs_reset, from_state=self.obs_state),
                        task_callback=task_callback,
                    )
                )
            )
            return (TaskStatus.QUEUED, "ObsReset queued")
        else:
            errorMsg = f"ObsReset not allowed in ObsState {self.obs_state}; must be in ObsState.FAULT or ObsState.ABORTED"
            self.logger.warning(errorMsg)
            return (TaskStatus.REJECTED, errorMsg)

    def scan(self: VCCAllBandsComponentManager, argin: str, task_callback: TaskCallbackType) -> tuple[TaskStatus, str]:
        self._asyncio_tasks.append(
            asyncio.create_task(
                self._obs_command_with_callback(hook="start", command_thread=self._scan, task_callback=task_callback)
            )
        )
        return (TaskStatus.QUEUED, "Scan queued")

    def end_scan(
        self: VCCAllBandsComponentManager,
        task_callback: TaskCallbackType,
    ) -> tuple[TaskStatus, str]:
        self._asyncio_tasks.append(
            asyncio.create_task(
                self._obs_command_with_callback(hook="stop", command_thread=self._end_scan, task_callback=task_callback)
            )
        )
        return (TaskStatus.QUEUED, "EndScan queued")

    async def _configure_device(self, fqdn: str, config: dict) -> None:
        """
        Configure the device with the given config

        :param fqdn: The FQDN of the device to configure
        :param config: The config to apply to the device
        :return: None
        """
        self.logger.info(f"{fqdn} configuring with {config}..")
        proxy = self._proxies[fqdn]
        result = await proxy.Configure(json.dumps(config), wait=False)

        if result[0] == ResultCode.FAILED:
            raise Exception(f"Configuration of {fqdn} failed: {result[1]}")

    async def _configure_scan(
        self: VCCAllBandsComponentManager,
        argin: str,
        task_callback: TaskCallbackType,
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

            self._sample_rate = configuration["dish_sample_rate"]
            self._samples_per_frame = configuration["samples_per_frame"]
            self.frequency_band = freq_band_dict()[configuration["frequency_band"]]
            self._expected_dish_id = configuration["expected_dish_id"]
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

            tasks = []

            # VCC123 Channelizer Configuration
            if self.frequency_band in {FrequencyBandEnum._1, FrequencyBandEnum._2}:
                config = {"sample_rate": self._sample_rate, "gains": self._vcc_gains}
                tasks.append(self._configure_device(self.device.vcc123_channelizer_fqdn, config))
            else:
                # TODO: Implement routing to the 5 Channelizer once outlined
                raise Exception(f"ConfigureScan failed unsupported band specified: {self.frequency_band}")

            # WFS Configuration
            config = {"shift_frequency": self.frequency_band_offset[0]}
            tasks.append(self._configure_device(self.device.wideband_frequency_shifter_fqdn, config))

            # FSS Configuration
            config = {"band_select": self.frequency_band.value + 1, "band_start_channel": [0, 1]}
            tasks.append(self._configure_device(self.device.fs_selection_fqdn, config))

            # WIB Configuration
            async def _configure_wib():
                config = {
                    "expected_sample_rate": self._sample_rate,
                    "noise_diode_transition_holdoff_seconds": configuration["noise_diode_transition_holdoff_seconds"],
                    "expected_dish_band": self.frequency_band.value + 1,  # FW Drivers rely on integer indexes, that are 1-based
                }
                await self._configure_device(self.device.wideband_input_buffer_fqdn, config)
                self._proxies[self.device.wideband_input_buffer_fqdn].expectedDishId = self._expected_dish_id

            tasks.append(_configure_wib())

            # Pre-channelizer WPM Configuration
            self._b123_pwrm = configuration["b123_pwrm"]
            self._b45a_pwrm = configuration["b45a_pwrm"]
            self._b5b_pwrm = configuration["b5b_pwrm"]

            for (
                fqdn,
                lane,
            ) in [
                (self.device.b123_wideband_power_meter_fqdn, self._b123_pwrm),
                (self.device.b45a_wideband_power_meter_fqdn, self._b45a_pwrm),
                (self.device.b5b_wideband_power_meter_fqdn, self._b5b_pwrm),
            ]:
                config = {
                    "averaging_time": lane["averaging_time"],
                    "sample_rate": self._sample_rate,
                    "flagging": lane["flagging"],
                }
                tasks.append(self._configure_device(fqdn, config))

            # Post-channelizer WPM Configuration
            self._fs_lanes = configuration["fs_lanes"]

            # Verify vlan_id is within range
            # ((config.vid >= 2 && config.vid <= 1001) || (config.vid >= 1006 && config.vid <= 4094))
            for lane in self._fs_lanes:
                if not (2 <= lane["vlan_id"] <= 1001 or 1006 <= lane["vlan_id"] <= 4094):
                    self.logger.error(f"VLAN ID {lane['vlan_id']} is not within range")
                    raise Exception("VLAN ID is not within range")

            for lane in self._fs_lanes:
                fqdn = self._power_meter_fqdns[int(lane["fs_id"])]
                config = {
                    "averaging_time": config["averaging_time"],
                    "sample_rate": self._sample_rate,
                    "flagging": config["flagging"],
                }
                tasks.append(self._configure_device(fqdn, config))

            # Packetizer Configuration
            config = {
                "fs_lanes": [
                    {"vlan_id": lane["vlan_id"], "vcc_id": self._vcc_id, "fs_id": lane["fs_id"]} for lane in self._fs_lanes
                ]
            }
            tasks.append(self._configure_device(self.device.packetizer_fqdn, config))

            await asyncio.gather(*tasks)

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ConfigureScan completed OK")
            self._obs_state_action_callback(FhsObsStateMachine.CONFIGURE_COMPLETED)
            return
        except asyncio.CancelledError:
            self._set_task_callback_aborted(task_callback, "ConfigureScan was cancelled")
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

    async def _scan(
        self: VCCAllBandsComponentManager,
        argin: int,
        task_callback: TaskCallbackType,
    ) -> None:
        """
        Begin scan operation.

        :param argin: scan ID integer

        :return: None
        """
        try:
            # set task status in progress, check for abort event
            self._scan_id = argin
            try:
                await asyncio.gather(
                    self._proxies[self.device.mac_200_fqdn].Start(wait=False),
                    self._proxies[self.device.packet_validation_fqdn].Start(wait=False),
                    self._proxies[self.device.wideband_input_buffer_fqdn].Start(wait=False),
                )
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
        except asyncio.CancelledError:
            self._set_task_callback_aborted(task_callback, "Scan was cancelled")
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call Scan command from an incorrect state",
            )

    async def _end_scan(
        self: VCCAllBandsComponentManager,
        task_callback: TaskCallbackType,
    ) -> None:
        """
        End scan operation.

        :return: None
        """
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)
            try:
                await self._stop_devices()
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
        except asyncio.CancelledError:
            self._set_task_callback_aborted(task_callback, "EndScan was cancelled")
        except StateModelError as ex:
            self.logger.error(f"Attempted to call command from an incorrect state: {repr(ex)}")
            self._set_task_callback(
                task_callback,
                TaskStatus.COMPLETED,
                ResultCode.REJECTED,
                "Attempted to call EndScan command from an incorrect state",
            )

    # A replacement for unconfigure
    async def _go_to_idle(self: VCCAllBandsComponentManager, task_callback: TaskCallbackType) -> None:
        try:
            # TODO: Check if ReceiveEnable is still required on the Agilex for the WIB
            task_callback(status=TaskStatus.IN_PROGRESS)

            # Reset all device proxies
            await self._reset_devices(self._proxies.keys())

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "GoToIdle completed OK")
            return
        except asyncio.CancelledError:
            self._set_task_callback_aborted(task_callback, "GoToIdle was cancelled")
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

    async def _obs_reset(
        self: VCCAllBandsComponentManager,
        task_callback: TaskCallbackType,
        from_state=ObsState.ABORTED,
    ) -> None:
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)

            # If in FAULT state, devices may still be running, so make sure they are stopped
            if from_state is ObsState.FAULT:
                await self._stop_devices()

            # Reset all device proxies
            await self._reset_devices(self._proxies.keys())

            self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, "ObsReset completed OK")
            return
        except asyncio.CancelledError:
            self._set_task_callback_aborted(task_callback, "ObsReset was cancelled")
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

    async def _stop_devices(self: VCCAllBandsComponentManager):
        self.logger.info("Stopping mac, packet_validation and wideband_input_buffer")
        await asyncio.gather(
            self._proxies[self.device.mac_200_fqdn].Stop(wait=False),
            self._proxies[self.device.packet_validation_fqdn].Stop(wait=False),
            self._proxies[self.device.wideband_input_buffer_fqdn].Stop(wait=False),
        )

    async def _abort_commands(self: VCCAllBandsComponentManager):
        super()._abort_commands()
        await self._stop_devices()

    def _reset_attributes(self: VCCAllBandsComponentManager):
        self._config_id = ""
        self._scan_id = 0
        self.frequency_band = FrequencyBandEnum._1
        self.frequency_band_offset = [0, 0]
        self._sample_rate = 0
        self._samples_per_frame = 0
        self._fsps = []

    async def _reset_device(self: VCCAllBandsComponentManager, fqdn: str):
        result = await self._proxies[fqdn].GoToIdle(wait=False)
        if result[0] != ResultCode.OK:
            self.logger.error(f"VCC {self._vcc_id}: Unable to set to IDLE state for ipblock {fqdn}")
        else:
            self.logger.info(f"VCC {self._vcc_id}: {fqdn} set to IDLE")

    async def _reset_devices(self: VCCAllBandsComponentManager, devices_name: list[str]):
        try:
            self._reset_attributes()
            await asyncio.gather(*[self._reset_device(fqdn) for fqdn in devices_name if self._proxies[fqdn] is not None])
        except Exception as ex:
            self.logger.error(f"Error resetting specific devices : {repr(ex)}")

    async def _subscribe_to_change_event(
        self: VCCAllBandsComponentManager,
        device_proxy,
        attribute: str,
        key: str,
        change_event_callback: Callable[[EventData], None],
    ):
        event_id = await device_proxy.subscribe_event(attribute, EventType.CHANGE_EVENT, change_event_callback, wait=False)
        if key in self.subscription_event_ids:
            self.subscription_event_ids[key].add(event_id)
        else:
            self.subscription_event_ids[key] = {event_id}

    async def _unsubscribe_from_events(self: VCCAllBandsComponentManager, fqdn: str):
        if fqdn in self.subscription_event_ids and fqdn in self._proxies and self._proxies[fqdn] is not None:
            for event_id in self.subscription_event_ids[fqdn]:
                try:
                    await self._proxies[fqdn].unsubscribe_event(event_id, wait=False)
                except Exception as ex:
                    self.logger.error(f"Unable to unsubcribe from event {event_id} for device server {fqdn}: {repr(ex)}")

    def _proxies_health_state_change_event(self: VCCAllBandsComponentManager, event_data: EventData):
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
