from __future__ import annotations  # allow forward references in type hints

import functools
import os
from threading import Event
from typing import Any, Callable, Optional

from ska_control_model import ObsState, ResultCode, SimulationMode, TaskStatus

from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface
from ska_mid_cbf_fhs_vcc.api.firmware.base_firmware_api import BaseFirmwareApi
from ska_mid_cbf_fhs_vcc.api.emulator.base_emulator_api import BaseEmulatorApi
from ska_mid_cbf_fhs_vcc.common.fhs_component_manager_base import FhsComponentManagerBase
from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_device_base import FhsLowLevelDeviceBase


class FhsLowLevelComponentManager(FhsComponentManagerBase):
    def __init__(
        self: FhsLowLevelComponentManager,
        *args: Any,
        device: FhsLowLevelDeviceBase,
        simulator_api: FhsBaseApiInterface,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )

        self._device = device
        self._device_id = device.device_id
        self._simulation_mode = device.simulation_mode
        self._emulation_mode = device.emulation_mode

        self.logger.info(
            f"Device Api starting for simulation_mode: {device.simulation_mode}, emulation_mode: {device.emulation_mode}"
        )
        bitstream_path = os.path.join(device.bitstream_path, device.bitstream_id, device.bitstream_version)

        self._api: FhsBaseApiInterface
        if self._simulation_mode == SimulationMode.TRUE and simulator_api is not None:
            self._api = simulator_api(self._device_id, self.logger)
        elif self._simulation_mode == SimulationMode.FALSE and self._emulation_mode and device.emulator_ip_block_id is not None:
            self._api = BaseEmulatorApi(
                bitstream_path, device.emulator_ip_block_id, device.emulator_id, device.emulator_base_url, self.logger
            )
        else:
            self._api = BaseFirmwareApi(bitstream_path, device.firmware_ip_block_id, self.logger)

    ####
    # Allowance Functions
    ####

    def is_recover_allowed(self: FhsLowLevelComponentManager) -> bool:
        self.logger.debug("Checking if Recover is allowed...")
        errorMsg = f"Device {self._device_id}  recover not allowed in ObsState {self.obs_state}; \
            must be in ObsState.IDLE or READY or ABORTED or RESETTING"
        return self.is_allowed(errorMsg, [ObsState.IDLE, ObsState.FAULT, ObsState.READY, ObsState.ABORTED])

    def is_configure_allowed(self: FhsLowLevelComponentManager) -> bool:
        self.logger.debug("Checking if Configure is allowed...")
        errorMsg = f"Device {self._device_id} Configure not allowed in ObsState {self.obs_state}; \
            must be in ObsState.IDLE or READY"

        return self.is_allowed(errorMsg, [ObsState.IDLE, ObsState.READY])

    def is_start_allowed(self: FhsLowLevelComponentManager) -> bool:
        self.logger.debug("Checking if Start is allowed...")
        errorMsg = f"Device {self._device_id} Start not allowed in ObsState {self.obs_state}; \
            must be in ObsState.IDLE or READY"

        return self.is_allowed(errorMsg, [ObsState.IDLE, ObsState.READY])

    def is_stop_allowed(self: FhsLowLevelComponentManager) -> bool:
        self.logger.debug("Checking if Stop is allowed...")
        errorMsg = f"Device {self._device_id} stop not allowed in ObsState {self.obs_state}; \
            must be in ObsState.IDLE, READY or ABORTED"

        return self.is_allowed(errorMsg, [ObsState.IDLE, ObsState.READY, ObsState.SCANNING, ObsState.ABORTED, ObsState.FAULT])

    def is_deconfigure_allowed(self: FhsLowLevelComponentManager) -> bool:
        self.logger.debug("Checking if Stop is allowed...")
        errorMsg = f"Device {self._device_id} deconfigure not allowed in ObsState {self.obs_state}; \
            must be in ObsState.READY"

        return self.is_allowed(errorMsg, [ObsState.IDLE, ObsState.READY, ObsState.ABORTED, ObsState.FAULT])

    def is_go_to_idle_allowed(self: FhsComponentManagerBase) -> bool:
        self.logger.debug("Checking if gotoidle is allowed...")
        errorMsg = f"go_to_idle not allowed in ObsState {self.obs_state}; " "must be in ObsState.READY"

        return self.is_allowed(errorMsg, [ObsState.READY, ObsState.ABORTED, ObsState.FAULT])

    #####
    # Command Functions
    #####

    def test_cmd(self: FhsLowLevelComponentManager, task_callback: Optional[Callable] = None) -> tuple[TaskStatus, str]:
        return [TaskStatus.COMPLETED, "Test Complete"]

    def recover(self: FhsLowLevelComponentManager) -> tuple[ResultCode, str]:
        try:
            if self.is_recover_allowed():
                self._obs_state_action_callback(FhsObsStateMachine.RECOVER_INVOKED)
                self._api.recover()
                self._obs_state_action_callback(FhsObsStateMachine.RECOVER_COMPLETED)
                return ResultCode.OK, "Recover command completed OK"
            else:
                return (
                    ResultCode.REJECTED,
                    f"Recover command is not allowed in obs state {self.obs_state}",
                )
        except Exception as ex:
            return ResultCode.FAILED, f"Recover command failed. ex={ex!r}"

    def configure(self: FhsLowLevelComponentManager, argin: dict) -> tuple[ResultCode, str]:
        self.logger.debug(f"Component state: {self.component_state}")
        if self.is_configure_allowed():
            self._obs_command_running_callback(hook="configure", running=True)
            result = self._configure(argin)
            self._obs_command_running_callback(hook="configure", running=False)
            return result
        else:
            return (
                ResultCode.REJECTED,
                f"Configure not allowed in component state {self.component_state}",
            )

    def deconfigure(self: FhsLowLevelComponentManager, argin: dict = None) -> tuple[ResultCode, str]:
        self.logger.debug(f"Component state: {self.component_state}")
        if self.is_deconfigure_allowed():
            self._obs_command_running_callback(hook="deconfigure", running=True)
            result = self._configure(argin, True)
            self._obs_command_running_callback(hook="deconfigure", running=False)
            return result
        else:
            return (
                ResultCode.REJECTED,
                f"Deconfigure not allowed in component state {self.component_state}",
            )

    def start(self: FhsLowLevelComponentManager, task_callback: Optional[Callable] = None) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.communication_state}")
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="start",
                command_thread=self._start,
            ),
            is_cmd_allowed=self.is_start_allowed,
            task_callback=task_callback,
        )

    def stop(
        self: FhsLowLevelComponentManager,
        task_callback: Optional[Callable] = tuple[TaskStatus, str],
    ) -> tuple[TaskStatus, str]:
        self.logger.debug(f"Component state: {self.communication_state}")
        return self.submit_task(
            func=functools.partial(
                self._obs_command_with_callback,
                hook="stop",
                command_thread=self._stop,
            ),
            is_cmd_allowed=self.is_stop_allowed,
            task_callback=task_callback,
        )

    def status(
        self: FhsLowLevelComponentManager,
        clear: bool = False,
    ) -> tuple[ResultCode, dict]:
        try:
            return self._api.status(clear)
        except Exception as ex:
            return ResultCode.FAILED, f"Status command FAILED. ex={ex!r}"

    # ------------------------
    #  Private Fast Commands
    # ------------------------

    def _configure(
        self: FhsLowLevelComponentManager,
        argin: dict = None,
        deconfigure: bool = False,
    ) -> tuple[ResultCode, str]:
        try:
            mode = "Configure" if not deconfigure else "Deconfigure"
            self.logger.info(f"Running {mode} command")

            if not deconfigure:
                if argin is not None:
                    return self._api.configure(argin)
                else:
                    return ResultCode.REJECTED, f"No Configuration given for {self._device_id}"
            else:
                return self._api.deconfigure(argin)

        except Exception as ex:
            return ResultCode.FAILED, f"{mode} command FAILED. ex={ex!r}"

    # -------------------------
    # Private LRC
    # -------------------------
    def _testCmd(self: FhsLowLevelComponentManager, task_callback: Optional[Callable] = None) -> None:
        # Assume configure fails at the start
        resultCode = ResultCode.FAILED
        taskStatus = TaskStatus.FAILED

        try:
            resultCode = (ResultCode.OK, f"Configure {self._device_id} completed OK")
            taskStatus = TaskStatus.COMPLETED
        except Exception as ex:
            resultCode = (ResultCode.FAILED, f"Unable to recover mac: {str(ex)}")
            self.set_fault_and_failed()

        task_callback(
            result=resultCode,
            status=taskStatus,
        )

    def _start(
        self: FhsLowLevelComponentManager,
        task_callback: Callable,
        task_abort_event: Event,
    ) -> None:
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)

            if not task_abort_event.isSet():
                # TODO Add polling
                result = self._api.start()

                if result[0] is ResultCode.OK:
                    self._set_task_callback_ok_completed(task_callback, result[1])
                else:
                    self._set_task_callback_failed(task_callback, result[1])
            else:
                self._set_task_callback_aborted(task_callback, "Start command was ABORTED")

        except Exception as ex:
            self._set_task_callback_failed(task_callback, f"Start command FAILED. ex={ex!r}")
            self.set_fault_and_failed()

    def _stop(
        self: FhsLowLevelComponentManager,
        task_callback: Optional[Callable] = None,
        task_abort_event: Optional[Event] = None,
    ) -> None:
        try:
            task_callback(status=TaskStatus.IN_PROGRESS)

            if not task_abort_event.is_set():
                # TODO add polling
                result = self._api.stop()
                if result[0] is ResultCode.OK:
                    self._set_task_callback_ok_completed(task_callback, result[1])
                else:
                    self._set_task_callback_failed(task_callback, result[1])
            else:
                self._set_task_callback_aborted(task_callback, "Stop command was ABORTED")

        except Exception as ex:
            self._set_task_callback_failed(task_callback, f"Stop command FAILED. ex={ex!r}")
            self.set_fault_and_failed()
