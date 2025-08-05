from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass, field
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
class VCCStreamMergeConfigureArgin:
    fs_lane_configs: list[VCCStreamMergeConfig] = field(default_factory=lambda: [])


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
            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            self.logger.info("VCC Stream Merge Configuring..")

            argin_parsed: VCCStreamMergeConfigureArgin = VCCStreamMergeConfigureArgin.schema().loads(argin)
            self.logger.info(f"VCC Stream Merge JSON CONFIG: {argin_parsed.to_json()}")

            for vcc_sm_config in argin_parsed.fs_lane_configs:
                self.logger.info(f"VCC Stream Merge FS Lane JSON CONFIG: {vcc_sm_config.to_json()}")

                result = super().configure(vcc_sm_config.to_dict())

                if result[0] != ResultCode.OK:
                    self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")
                    break

        except ValidationError as vex:
            error_msg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            result = ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            result = ResultCode.FAILED, error_msg

        return result

    def deconfigure(self: VCCStreamMergeComponentManager, argin: str = None) -> tuple[ResultCode, str]:
        try:
            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} deconfigured successfully",
            )

            if argin is None:
                result = super().recover()
            else:
                argin_parsed: VCCStreamMergeConfigureArgin = VCCStreamMergeConfigureArgin.schema().loads(argin)

                self.logger.info(f"DECONFIG JSON CONFIG: {argin_parsed.to_json()}")

                for vcc_sm_config in argin_parsed.fs_lane_configs:
                    self.logger.info(f"VCC Stream Merge FS Lane JSON CONFIG: {vcc_sm_config.to_json()}")

                    result = super().deconfigure(vcc_sm_config.to_dict())

                    if result[0] != ResultCode.OK:
                        self.logger.error(f"Deconfiguring {self._device_id} failed. {result[1]}")
                        break

        except ValidationError as vex:
            error_msg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            result = ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            result = ResultCode.FAILED, error_msg

        return result

    def start_communicating(self: VCCStreamMergeComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
