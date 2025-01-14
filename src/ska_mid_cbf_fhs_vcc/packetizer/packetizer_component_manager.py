from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.packetizer_simulator import PacketizerSimulator
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase


@dataclass_json
@dataclass
class PacketizerConfig:
    vid: np.uint16  # VLAN identifier, for unique VLAN identification.
    vcc_id: np.uint16  # Influences the Source MAC address.
    fs_id: np.uint16  # Frequency slice identifier.


##
# status class that will be populated by the APIs and returned to provide the status of Packetizer
##
@dataclass
class PacketizerStatus:
    mac_source_register: np.uint64  # Source MAC Address.
    vid_register: np.uint16  # VLAN identifier.
    flags_register: np.uint16  # Various flags, currently used for noise diode state.
    psn_register: np.uint16  # Packet sequence number.
    packet_count_register: np.uint32  # Packet count.


@dataclass_json
@dataclass
class PacketizerConfigArgin:
    fs_lanes: list[dict]


class PacketizerComponentManager(FhsLowLevelComponentManagerBase):
    def __init__(
        self: PacketizerComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=PacketizerSimulator,
            **kwargs,
        )

    # ------------------
    # Public Commands
    # ------------------

    def configure(self: PacketizerComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("Packetizer Configuring..")

            configJson: PacketizerConfigArgin = PacketizerConfigArgin.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {configJson.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            for fs_lane in configJson.fs_lanes:
                packetizerJsonConfig = PacketizerConfig(
                    vid=fs_lane.get("vlan_id"),
                    vcc_id=fs_lane.get("vcc_id"),
                    fs_id=fs_lane.get("fs_id"),
                )

                self.logger.info(f"Packetizer JSON CONFIG: {packetizerJsonConfig.to_json()}")

                result = super().configure(packetizerJsonConfig.to_dict())

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

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: PacketizerComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
