from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_simulator import VCCStreamMergeSimulator


@dataclass_json
@dataclass
class VCCStreamMergeConfig:
    vid: np.uint16  # VLAN identifier, for unique VLAN identification.
    vcc_id: np.uint16  # Influences the Source MAC address.
    fs_id: np.uint16  # Frequency slice identifier.


##
# status class that will be populated by the APIs and returned to provide the status of VCC Stream Merge
##
@dataclass
class VCCStreamMergeStatus:
    mac_source_register: np.uint64  # Source MAC Address.
    vid_register: np.uint16  # VLAN identifier.
    flags_register: np.uint16  # Various flags, currently used for noise diode state.
    psn_register: np.uint16  # Packet sequence number.
    packet_count_register: np.uint32  # Packet count.


@dataclass_json
@dataclass
class VCCStreamMergeConfigArgin:
    fs_lanes: list[dict]


class VCCStreamMergeComponentManager(FhsLowLevelComponentManagerBase):
    def __init__(
        self: VCCStreamMergeComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=VCCStreamMergeSimulator,
            **kwargs,
        )

    # ------------------
    # Public Commands
    # ------------------

    def configure(self: VCCStreamMergeComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("VCC Stream Merge Configuring..")

            config_json: VCCStreamMergeConfigArgin = VCCStreamMergeConfigArgin.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {config_json.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            for fs_lane in config_json.fs_lanes:
                vcc_sm_config = VCCStreamMergeConfig(
                    vid=fs_lane.get("vlan_id"),
                    vcc_id=fs_lane.get("vcc_id"),
                    fs_id=fs_lane.get("fs_id"),
                )

                self.logger.info(f"VCC Stream Merge JSON CONFIG: {vcc_sm_config.to_json()}")

                result = super().configure(vcc_sm_config.to_dict())

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
    def start_communicating(self: VCCStreamMergeComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
