from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from ska_control_model import HealthState

from ska_mid_cbf_fhs_vcc.api.common.fhs_base_api_interface import FhsBaseApiInterface


class FhsHealthMonitor:
    def __init__(
        self,
        logger: logging.Logger,
        get_device_health_state: Callable,
        update_health_state_callback: Callable,
        check_registers_callback: Callable | None = None,
        api: FhsBaseApiInterface | None = None,
        status_func: str = "status",
        poll_interval=1.0,
    ) -> None:
        self._last_health_state = HealthState.UNKNOWN
        self.lock = threading.Lock()
        self.component_statuses: dict[str, HealthState] = {}

        self.logger = logger
        self.api = api
        self.check_registers_callback = check_registers_callback

        self.get_device_health_state = get_device_health_state
        self.update_health_state_callback = update_health_state_callback

        self._health_states = [HealthState.FAILED, HealthState.DEGRADED, HealthState.UNKNOWN, HealthState.OK]

        # only set up polling if we're provided an api and a check_registers_callback function
        if self.api and self.check_registers_callback:
            self._polling_thread = RegisterPollingThread(
                api=self.api,
                status_func=status_func,
                check_registers_callback=self.check_registers_callback,
                poll_interval=poll_interval,
                add_health_state=self.add_health_state,
                merge_health_states=self.merge_health_states,
            )
        else:
            self._polling_thread = None

    def start_polling(self: FhsHealthMonitor):
        if self.api and self.check_registers_callback and self._polling_thread:
            self._polling_thread.start()
        else:
            self.logger.warning(
                "Unable to start polling, health monitor not configured with an api or callback function for checking registers"
            )

    def stop_polling(self: FhsHealthMonitor):
        if self._polling_thread:
            self._polling_thread.stop()

    def add_health_state(self: FhsHealthMonitor, key: str, health_state: HealthState):
        with self.lock:
            if key and health_state:
                self.component_statuses[key] = health_state
            else:
                raise ValueError(
                    "Key must be provided when single health state added, No key to be supplied when using dict of healthstates"
                )

            self.determine_health_state()

    def merge_health_states(self: FhsHealthMonitor, dict_to_merge: dict[str, HealthState]):
        with self.lock:
            self.component_statuses.update(dict_to_merge)
            self.determine_health_state()

    def remove_failure(self: FhsHealthMonitor, key: str):
        with self.lock:
            if key in self.component_statuses:
                self.component_statuses.pop(key)
                self.determine_health_state()

    def reset_failures(self: FhsHealthMonitor):
        self.component_statuses = {}

    def determine_health_state(self: FhsHealthMonitor):
        for health_state in self._health_states:
            if health_state in self.component_statuses.values():
                if health_state is not self.get_device_health_state():
                    self._last_health_state = health_state
                    self.update_health_state_callback(health_state)
                break


class RegisterPollingThread(threading.Thread):
    def __init__(
        self: RegisterPollingThread,
        api: FhsBaseApiInterface,
        status_func: str,
        check_registers_callback: Callable,
        add_health_state: Callable,
        merge_health_states: Callable,
        poll_interval=1.0,
    ):
        super().__init__()
        self.api = api
        self.status_func = status_func
        self.check_registers_callback = check_registers_callback
        self.poll_interval = poll_interval
        self.daemon = True
        self._stop_event = threading.Event()
        self._running = False
        self.add_health_state = add_health_state
        self.merge_health_states = merge_health_states

    def run(self: RegisterPollingThread):
        if not self._running:
            while not self._stop_event.is_set():
                try:
                    time.sleep(self.poll_interval)
                    status_func = getattr(self.api, self.status_func)

                    print("::::: got Status func ::::::")

                    _, status = status_func()

                    print(f":::::::::: STATUS RECEIVED {status} ::::::::::")

                    health_states: dict[str, HealthState] = self.check_registers_callback(status)
                    self.merge_health_states(health_states)

                except Exception as ex:
                    self.add_health_state("REGISTER_POLLING_EXCEPTION", HealthState.UNKNOWN)
                    self.stop()
                    print(f"Error - Unable to monitor health. {repr(ex)}")
        else:
            print("LowLevelHealthMonitor is already running")

    def stop(self):
        self._stop_event.set()
