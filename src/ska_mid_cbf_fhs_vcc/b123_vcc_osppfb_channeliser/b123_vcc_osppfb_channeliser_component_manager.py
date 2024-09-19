from __future__ import annotations  # allow forward references in type hints

import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, HealthState, PowerState, ResultCode, SimulationMode

from ska_mid_cbf_fhs_vcc.api.emulator.b123_vcc_osppfb_channeliser_emulator_api import B123VccOsppfbChanneliserEmulatorApi
from ska_mid_cbf_fhs_vcc.api.firmware.b123_vcc_osppfb_channeliser_firmware_api import B123VccOsppfbChanneliserFirmwareApi
from ska_mid_cbf_fhs_vcc.api.simulator.b123_vcc_osppfb_channeliser_simulator import B123VccOsppfbChanneliserSimulator
from ska_mid_cbf_fhs_vcc.common.low_level.fhs_low_level_component_manager import FhsLowLevelComponentManager


@dataclass_json
@dataclass
class B123VccOsppfbChanneliserConfig:
    sample_rate: np.uint64
    pol: dict
    channel: np.uint16
    gain: np.float32


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class B123VccOsppfbChanneliserStatus:
    sample_rate: np.uint32
    num_channels: int
    num_polarisations: int
    gains: list[np.float32]


@dataclass_json
@dataclass
class VccConfigArgin:
    sample_rate: np.uint64
    gains: list[float]


class B123VccOsppfbChanneliserComponentManager(FhsLowLevelComponentManager[B123VccOsppfbChanneliserConfig]):
    def __init__(
        self: B123VccOsppfbChanneliserComponentManager,
        *args: Any,
        logger: logging.Logger,
        device_id,
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
            self._api = B123VccOsppfbChanneliserSimulator(device_id, logger)
        elif simulation_mode == SimulationMode.FALSE and emulation_mode is True:
            self._api = B123VccOsppfbChanneliserEmulatorApi(device_id, config_location, logger)
        else:
            self._api = B123VccOsppfbChanneliserFirmwareApi(config_location, logger)

        self.config_class = B123VccOsppfbChanneliserConfig(sample_rate=0, pol=None, channel=0, gain=0.0)

        super().__init__(
            *args,
            logger=logger,
            device_id=device_id,
            api=self._api,
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

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: B123VccOsppfbChanneliserComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""

        self.logger.info("Starting Communication for VCC...")

        self._update_communication_state(CommunicationStatus.ESTABLISHED)

        self._update_component_state(power=PowerState.ON)

        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()

    #####
    # Commands
    #####

    def configure(self: FhsLowLevelComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("VCC Configuring..")

            vccConfigArgin: VccConfigArgin = VccConfigArgin.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {vccConfigArgin.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            for i, gain in enumerate(vccConfigArgin.gains):
                vccJsonConfig = B123VccOsppfbChanneliserConfig(
                    sample_rate=vccConfigArgin.sample_rate,
                    gain=gain,
                    channel=i,
                    pol=i % 2,
                )

                self.logger.info(f"VCC JSON CONFIG {i}: {vccJsonConfig.to_json()}")

                result = super().configure(vccJsonConfig.to_dict())
                if result[0] != ResultCode.OK:
                    self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")
                    break

        except ValidationError as vex:
            errorMsg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{errorMsg}: {vex}")
            result = ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{errorMsg}: {ex!r}")
            result = ResultCode.FAILED, errorMsg

        return result
