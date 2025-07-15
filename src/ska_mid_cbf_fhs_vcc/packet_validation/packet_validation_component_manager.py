from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

import numpy as np
from dataclasses_json import dataclass_json
from marshmallow import ValidationError
from ska_control_model import CommunicationStatus, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_simulator import PacketValidationControllerSimulator


@dataclass_json
@dataclass
class PacketValidationConfig:
    drop_dst_mac: bool = True
    drop_src_mac: bool = True
    drop_ethertype: bool = True
    drop_antenna_id: bool = True
    clr_cnt: bool = True
    exp_dst_mac: np.uint64_t = 0
    exp_src_mac: np.uint64_t = 0
    exp_ethertype: np.uint64_t = 0
    exp_antenna_id: np.uint64_t = 0


##
# status class that will be populated by the APIs and returned to provide the status of Packet Validation
##
@dataclass_json
@dataclass
class PacketValidationStatus:
    drop_dst_mac: bool = True
    drop_src_mac: bool = True
    drop_ethertype: bool = True
    drop_antenna_id: bool = True
    egress_cnt: np.uint32_t = 0
    ingress_error_cnt: np.uint32_t = 0
    size_error_cnt: np.uint32_t = 0
    exp_dst_mac: np.uint64_t = 0
    last_wrong_dst_mac: np.uint64_t = 0
    wrong_dst_mac_cnt: np.uint32_t = 0
    exp_src_mac: np.uint64_t = 0
    last_wrong_src_mac: np.uint64_t = 0
    wrong_src_mac_cnt: np.uint32_t = 0
    exp_ethertype: np.uint64_t = 0
    last_wrong_ethertype: np.uint64_t = 0
    wrong_ethertype_cnt: np.uint32_t = 0
    exp_antenna_id: np.uint64_t = 0
    last_wrong_antenna_id: np.uint64_t = 0
    wrong_antenna_id_cnt: np.uint32_t = 0


class PacketValidationComponentManager(FhsLowLevelComponentManagerBase):
    def __init__(
        self: PacketValidationComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=PacketValidationControllerSimulator,
            **kwargs,
        )

    ##
    # Public Commands
    ##
    def configure(self: PacketValidationComponentManager, argin: str) -> tuple[ResultCode, str]:
        try:
            self.logger.info("Packet Validation Configuring..")

            pv_config: PacketValidationConfig = PacketValidationConfig.schema().loads(argin)

            self.logger.info(f"CONFIG JSON CONFIG: {pv_config.to_json()}")

            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} configured successfully",
            )

            result = super().configure(pv_config.to_dict())

            if result[0] != ResultCode.OK:
                self.logger.error(f"Configuring {self._device_id} failed. {result[1]}")

        except ValidationError as vex:
            error_msg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            result = ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            result = ResultCode.FAILED, error_msg

        return result

    def deconfigure(self: PacketValidationComponentManager, argin: str = None) -> tuple[ResultCode, str]:
        self.logger.error(f"############################# Deconfigure called")
        try:
            result: tuple[ResultCode, str] = (
                ResultCode.OK,
                f"{self._device_id} deconfigured successfully",
            )

            if argin is None:
                result = super().recover()
            else:
                pv_config: PacketValidationConfig = PacketValidationConfig.schema().loads(argin)

                self.logger.info(f"DECONFIG JSON CONFIG: {pv_config.to_json()}")

                result = super().deconfigure(argin)

                if result[0] != ResultCode.OK:
                    self.logger.error(f"DeConfiguring {self._device_id} failed. {result[1]}")

        except ValidationError as vex:
            error_msg = "Validation error: argin doesn't match the required schema"
            self.logger.error(f"{error_msg}: {vex}")
            result = ResultCode.FAILED, error_msg
        except Exception as ex:
            error_msg = f"Unable to configure {self._device_id}"
            self.logger.error(f"{error_msg}: {ex!r}")
            result = ResultCode.FAILED, error_msg

        return result

    # TODO Determine what needs to be communicated with here
    def start_communicating(self: PacketValidationComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
