from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, PowerState, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_simulator import (
    B123VccOsppfbChannelizerSimulator,
)


@dataclass_json
@dataclass
class B123VccOsppfbChannelizerConfig:
    sample_rate: np.uint64
    pol: dict
    channel: np.uint16
    gain: np.float32


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class B123VccOsppfbChannelizerStatus:
    sample_rate: np.uint32
    num_channels: int
    num_polarisations: int
    gains: list[np.float32]


@dataclass_json
@dataclass
class B123VccOsppfbChannelizerConfigureArgin:
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


class B123VccOsppfbChannelizerComponentManager(
    FhsLowLevelComponentManagerBase
):
    def __init__(
        self: B123VccOsppfbChannelizerComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=B123VccOsppfbChannelizerSimulator,
            **kwargs,
        )

    ##
    # Public Commands
    ##

    # TODO Determine what needs to be communicated with here
    def start_communicating(
        self: B123VccOsppfbChannelizerComponentManager,
    ) -> None:
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

    def configure(
        self: B123VccOsppfbChannelizerComponentManager, argin: str
    ) -> tuple[ResultCode, str]:
        try:
            self.logger.info("VCC Configuring..")

            argin_parsed: B123VccOsppfbChannelizerConfigureArgin = (
                B123VccOsppfbChannelizerConfigureArgin.schema().loads(argin)
            )

            self.logger.info(
                f"CONFIGURE JSON CONFIG: {argin_parsed.to_json()}"
            )

            return self._generate_and_configure(
                argin_parsed, super().configure
            )
        except ValidationError as vex:
            error_msg = "Validation error: Unable to configure, argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            return ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            return ResultCode.FAILED, error_msg
            # TODO helthstate check

    def deconfigure(
        self: B123VccOsppfbChannelizerComponentManager, argin: str = None
    ) -> tuple[ResultCode, str]:
        try:
            self.logger.info("VCC Deconfiguring..")

            # Get the default values
            argin_parsed = B123VccOsppfbChannelizerConfigureArgin()

            # If the argin is not none then we're 'reconfiguring' using the values set otherwise we use the default values
            if argin is not None:
                argin_parsed: B123VccOsppfbChannelizerConfigureArgin = (
                    B123VccOsppfbChannelizerConfigureArgin.schema().loads(
                        argin
                    )
                )

            self.logger.info(
                f"DECONFIGURE JSON CONFIG: {argin_parsed.to_json()}"
            )

            return self._generate_and_configure(
                argin_parsed, super().deconfigure
            )
        except ValidationError as vex:
            error_msg = "Validation error: Unable to deconfigure, argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            return ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to deconfigure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            return ResultCode.FAILED, error_msg
            # TODO helthstate check

    def _generate_and_configure(
        self: B123VccOsppfbChannelizerComponentManager,
        vcc_config_argin: B123VccOsppfbChannelizerConfigureArgin,
        configure,
    ) -> dict:
        result: tuple[ResultCode, str] = (
            ResultCode.OK,
            f"{self._device_id} configured successfully",
        )

        # Channels are dual-polarized i.e. 2 gain values per channel[x, y]
        num_channels = len(vcc_config_argin.gains) // 2
        for polarization in (0, 1):
            for i in range(num_channels):
                vcc_config = B123VccOsppfbChannelizerConfig(
                    sample_rate=vcc_config_argin.sample_rate,
                    gain=vcc_config_argin.gains[
                        i + polarization * num_channels
                    ],
                    channel=i,
                    pol=polarization,
                )

                self.logger.info(
                    f"VCC JSON CONFIG channel={i} pol={polarization}: {vcc_config}"
                )

                result = configure(vcc_config.to_dict())
                if result[0] != ResultCode.OK:
                    self.logger.error(
                        f"Configuring {self._device_id} failed. {result[1]}"
                    )
                    break

        return result
