from __future__ import annotations  # allow forward references in type hints

import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import (
    CommunicationStatus,
    HealthState,
    ResultCode,
    SimulationMode,
)

from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import (
    FhsLowLevelComponentManager,
)
from ska_mid_cbf_fhs_vcc.api.emulator.wib_emulator_api import WibEmulatorApi
from ska_mid_cbf_fhs_vcc.api.simulator.wideband_input_buffer_simulator import (
    WidebandInputBufferSimulator,
)


@dataclass_json
@dataclass
class WideBandInputBufferConfig:
    expected_sample_rate: np.uint64
    noide_diode_transition_holdoff_seconds: float


##
# status class that will be populated by the APIs and returned to provide the status of Mac
##
@dataclass_json
@dataclass
class WideBandInputBufferStatus:
    buffer_underflowed: bool
    buffer_overflowed: bool
    loss_of_signal: np.uint32
    band_id: np.uint8


@dataclass_json
@dataclass
class WibArginConfig:
    expected_sample_rate: np.uint64
    noise_diode_transition_holdoff_seconds: float


class WidebandInputBufferComponentManager(
    FhsLowLevelComponentManager[WideBandInputBufferConfig, WideBandInputBufferStatus]
):
    def __init__(
        self: WidebandInputBufferComponentManager,
        *args: Any,
        logger: logging.Logger,
        device_id=None,
        config_location,
        attr_change_callback: Callable[[str, Any], None] | None = None,
        attr_archive_callback: Callable[[str, Any], None] | None = None,
        health_state_callback: Callable[[HealthState], None] | None = None,
        obs_command_running_callback: Callable[[str, bool], None],
        max_queue_size: int = 32,
        simulation_mode: SimulationMode = SimulationMode.FALSE,
        emulation_mode: bool = True,
        **kwargs: Any,
    ) -> None:
        if simulation_mode == SimulationMode.TRUE:
            self._api = WidebandInputBufferSimulator(device_id, logger)
        elif simulation_mode == SimulationMode.FALSE and emulation_mode is True:
            self._api = WibEmulatorApi(device_id, config_location, logger)
        else:
            raise NotImplementedError("FW Api not implemented")

        self.status_class = WideBandInputBufferStatus(False, False, 0, 0)
        self.config_class = WideBandInputBufferConfig(0, 0.0)

        super().__init__(
            *args,
            logger=logger,
            device_id=device_id,
            api=self._api,
            status_class=self.status_class,
            config_class=self.config_class,
            attr_change_callback=attr_change_callback,
            attr_archive_callback=attr_archive_callback,
            health_state_callback=health_state_callback,
            obs_command_running_callback=obs_command_running_callback,
            max_queue_size=max_queue_size,
            simulation_mode=simulation_mode,
            emulation_mode=emulation_mode,
            **kwargs,
        )

    ##
    # Public Commands
    ##
    def configure(self: FhsLowLevelComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("WIB Configuring..")

            configJson: WibArginConfig = WibArginConfig.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {configJson.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            wibJsonConfig = WideBandInputBufferConfig(
                expected_sample_rate=configJson.expected_sample_rate,
                noide_diode_transition_holdoff_seconds=configJson.noise_diode_transition_holdoff_seconds,
            )

            self.logger.info(f"WIB JSON CONFIG: {wibJsonConfig.to_json()}")

            result = super().configure(wibJsonConfig.to_dict())

            if result[0] != ResultCode.OK:
                self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")

        except ValidationError as vex:
            errorMsg = "Validation error: argin doesn't match the required schema."
            self.logger.error(f"{errorMsg}: {vex}")
            result = ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{errorMsg}: {ex!r}")
            result = ResultCode.FAILED, errorMsg

        return result

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: WidebandInputBufferComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
