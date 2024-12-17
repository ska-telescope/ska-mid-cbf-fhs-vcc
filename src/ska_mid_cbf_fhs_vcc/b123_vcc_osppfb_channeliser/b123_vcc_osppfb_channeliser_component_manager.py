from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, PowerState, ResultCode

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
    sample_rate: np.uint64 = 3960000000  # default values
    gains: list[float] = field(
        default_factory=lambda: [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ]
    )  # default gain values


class B123VccOsppfbChanneliserComponentManager(FhsLowLevelComponentManager):
    def __init__(
        self: B123VccOsppfbChanneliserComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=B123VccOsppfbChanneliserSimulator,
            **kwargs,
        )

    ##
    # Public Commands
    ##

    # TODO Determine what needs to be communicated with here
    async def start_communicating(self: B123VccOsppfbChanneliserComponentManager) -> None:
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
    def go_to_idle(self: B123VccOsppfbChanneliserComponentManager) -> tuple[ResultCode, str]:
        result = self.deconfigure()

        if result[0] is not ResultCode.FAILED:
            result = super().go_to_idle()

        return result

    def configure(self: B123VccOsppfbChanneliserComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("VCC Configuring..")

            vccConfigArgin: VccConfigArgin = VccConfigArgin.schema().loads(argin)

            self.logger.info(f"CONFIGURE JSON CONFIG: {vccConfigArgin.to_json()}")

            return self._generate_and_configure(vccConfigArgin, super().configure)
        except ValidationError as vex:
            errorMsg = "Validation error: Unable to configure, argin doesn't match the required schema"
            self.logger.error(f"{errorMsg}: {vex}")
            return ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{errorMsg}: {ex!r}")
            return ResultCode.FAILED, errorMsg
            # TODO helthstate check

    def deconfigure(self: B123VccOsppfbChanneliserComponentManager, argin: str = None) -> tuple[ResultCode, str]:
        try:
            self.logger.info("VCC Deconfiguring..")

            # Get the default values
            vccConfigArgin = VccConfigArgin()

            # If the argin is not none then we're 'reconfiguring' using the values set otherwise we use the default values
            if argin is not None:
                vccConfigArgin: VccConfigArgin = VccConfigArgin.schema().loads(argin)

            self.logger.info(f"DECONFIGURE JSON CONFIG: {vccConfigArgin.to_json()}")

            return self._generate_and_configure(vccConfigArgin, super().deconfigure)
        except ValidationError as vex:
            errorMsg = "Validation error: Unable to deconfigure, argin doesn't match the required schema"
            self.logger.error(f"{errorMsg}: {vex}")
            return ResultCode.FAILED, errorMsg
        except Exception as ex:
            errorMsg = f"Unable to deconfigure {self._device_id}"
            self.logger.error(f"{errorMsg}: {ex!r}")
            return ResultCode.FAILED, errorMsg
            # TODO helthstate check

    def _generate_and_configure(
        self: B123VccOsppfbChanneliserComponentManager, vccConfigArgin: VccConfigArgin, configure
    ) -> dict:
        result: tuple[ResultCode, str] = (
            ResultCode.OK,
            f"{self._device_id} configured successfully",
        )

        # Channels are dual-polarized i.e. 2 gain values per channel[x, y]
        chan = 0
        for i, gain in enumerate(vccConfigArgin.gains):
            vccConfig = B123VccOsppfbChanneliserConfig(
                sample_rate=vccConfigArgin.sample_rate,
                gain=gain,
                channel=chan,
                pol=i % 2,
            )
            if i % 2:
                chan += 1

            self.logger.info(f"VCC JSON CONFIG {i}: {vccConfig.to_json()}")

            result = configure(vccConfig.to_dict())
            if result[0] != ResultCode.OK:
                self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")
                break

        return result
