# -*- coding: utf-8 -*-
#
# This file is part of the SKA Mid CBF FHS VCC project With inspiration gathered from the Mid.CBF MCS project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE.txt for more info.

from __future__ import annotations  # allow forward references in type hints

import logging
from threading import Lock
from typing import Any, Callable, Optional, cast

from ska_control_model import CommunicationStatus, HealthState, PowerState, ResultCode, TaskStatus
from ska_tango_base.base.base_component_manager import BaseComponentManager
from ska_tango_base.executor.executor_component_manager import TaskExecutorComponentManager

from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine, ObsState


class FhsComponentManagerBase(TaskExecutorComponentManager):
    @property
    def faulty(self: FhsComponentManagerBase) -> Optional[bool]:
        """
        Return whether this component manager is currently experiencing a fault.

        :return: whether this component manager is currently
            experiencing a fault.
        """
        return cast(bool, self._component_state["fault"])

    def __init__(
        self: TaskExecutorComponentManager,
        *args: Any,
        attr_change_callback: Callable[[str, Any], None] | None = None,
        attr_archive_callback: Callable[[str, Any], None] | None = None,
        health_state_callback: Callable[[HealthState], None] | None = None,
        obs_command_running_callback: Callable[[str, bool], None],
        obs_state_action_callback: Callable[[str], None] | None = None,
        logger: logging.Logger,
        **kwargs: Any,
    ) -> None:
        self.obs_state = ObsState.IDLE

        self._attr_change_callback = attr_change_callback
        self._attr_archive_callback = attr_archive_callback
        self._device_health_state_callback = health_state_callback
        self._obs_command_running_callback = obs_command_running_callback
        self._obs_state_action_callback = obs_state_action_callback

        self._health_state_lock = Lock()
        self._health_state = HealthState.UNKNOWN

        super().__init__(
            power=None,
            fault=None,
            logger=logger,
            **kwargs,
        )

    def get_device_health_state(self: FhsComponentManagerBase):
        return self._health_state

    def update_device_health_state(
        self: FhsComponentManagerBase,
        health_state: HealthState,
    ) -> None:
        """
        Handle a health state change.
        This is a helper method for use by subclasses.
        :param state: the new health state of the
            component manager.
        """
        with self._health_state_lock:
            if self._health_state != health_state:
                if self._device_health_state_callback is not None:
                    self._device_health_state_callback(health_state)
                else:
                    self.logger.error("No callback set for updating health state")

    def set_fault_and_failed(self: FhsComponentManagerBase) -> None:
        """_summary_
        Set the component state to faulty and update its health to failed

        This is to be called when an exception occurs in the component manager
        """
        self._component_state_callback(fault=True)
        self.update_device_health_state(
            health_state=HealthState.DEGRADED
        )  # TODO Determine if the health state here needs to be degraded or not

    def is_go_to_idle_allowed(self: FhsComponentManagerBase) -> bool:
        self.logger.debug("Checking if gotoidle is allowed...")
        errorMsg = f"go_to_idle not allowed in Obstate {self.obs_state}; " "must be in Obstate.READY, ABORTED or FAULT"

        return self.is_allowed(errorMsg, [ObsState.READY, ObsState.ABORTED, ObsState.FAULT])

    def is_allowed(self: FhsComponentManagerBase, error_msg: str, obsStates: list[ObsState]) -> bool:
        result = True

        if self.obs_state not in obsStates:
            self.logger.warning(error_msg)
            result = False

        return result

    ########
    # Commands
    ########
    def go_to_idle(self: FhsComponentManagerBase) -> tuple[ResultCode, str]:
        self.logger.debug(f"Component state: {self._component_state}")

        msg = "GoToIdle called sucessfully"

        if self.obs_state != ObsState.IDLE:
            if self.is_go_to_idle_allowed():
                self._obs_state_action_callback(FhsObsStateMachine.GO_TO_IDLE)
        else:
            msg = "Already in the IDLE State"

        return ResultCode.OK, msg

    ########
    # Private Commands
    ########
    # Called when adminMode is set to ONLINE from the SKA base_device.py
    def start_communicating(self: BaseComponentManager) -> None:
        self._component_state_callback(power=PowerState.ON)
        self._update_communication_state(communication_state=CommunicationStatus.ESTABLISHED)

    # Called when adminMode is set to OFFLINE
    def stop_communicating(self: BaseComponentManager) -> None:
        self._component_state_callback(power=PowerState.UNKNOWN)
        self._update_communication_state(communication_state=CommunicationStatus.DISABLED)

    ###
    # Utility functions
    ###

    def _obs_command_with_callback(
        self: FhsComponentManagerBase,
        *args,
        command_thread: Callable[[Any], None],
        hook: str,
        **kwargs,
    ):
        """
        Wrap command thread with ObsStateModel-driving callbacks.

        :param command_thread: actual command thread to be executed
        :param hook: hook for state machine action
        """
        self._obs_command_running_callback(hook=hook, running=True)
        command_thread(*args, **kwargs)
        self._obs_command_running_callback(hook=hook, running=False)

    def _set_task_callback_aborted(self: FhsComponentManagerBase, task_callback: Callable, message: str) -> None:
        self._set_task_callback(task_callback, TaskStatus.ABORTED, ResultCode.ABORTED, message)

    def _set_task_callback_ok_completed(self: FhsComponentManagerBase, task_callback: Callable, message: str) -> None:
        self._set_task_callback(task_callback, TaskStatus.COMPLETED, ResultCode.OK, message)

    def _set_task_callback_failed(self: FhsComponentManagerBase, task_callback: Callable, message: str) -> None:
        self._set_task_callback(task_callback, TaskStatus.FAILED, ResultCode.FAILED, message)

    def _set_task_callback_rejected(self: FhsComponentManagerBase, task_callback: Callable, message: str) -> None:
        self._set_task_callback(task_callback, TaskStatus.REJECTED, ResultCode.REJECTED, message)

    def _set_task_callback(
        self: FhsComponentManagerBase,
        task_callback: Callable,
        task_status: TaskStatus,
        task_result: ResultCode,
        message: str,
    ) -> None:
        task_callback(result=(task_result, message), status=task_status)
