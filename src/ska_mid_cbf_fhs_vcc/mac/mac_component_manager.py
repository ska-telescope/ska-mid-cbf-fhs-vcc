from __future__ import annotations  # allow forward references in type hints

from dataclasses import dataclass
from typing import Any

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import CommunicationStatus, ResultCode
from ska_mid_cbf_fhs_common import FhsLowLevelComponentManagerBase

from ska_mid_cbf_fhs_vcc.mac.mac_controller_simulator import MacBaseControllerSimulator


@dataclass_json
@dataclass
class MacConfig:
    rx_loopback_enable: bool = False


##
# status class that will be populated by the APIs and returned to provide the status of Mac
##
@dataclass_json
@dataclass
class MacStatus:
    class phy:
        rx_loopback: bool = False
        rx_freq_lock = []
        rx_word_lock = []

    class fec:
        rx_corrected_code_words: np.uint32 = 0
        rx_uncorrected_code_words: np.uint32 = 0

    class mac:
        rx_fragments: np.uint32 = 0
        rx_runt: np.uint32 = 0
        rx_64_bytes: np.uint32 = 0
        rx_65_to_127_bytes: np.uint32 = 0
        rx_128_to_255_bytes: np.uint32 = 0
        rx_256_to_511_bytes: np.uint32 = 0
        rx_512_to_1023_bytes: np.uint32 = 0
        rx_1024_to_1518_bytes: np.uint32 = 0
        rx_1519_to_max_bytes: np.uint32 = 0
        rx_oversize: np.uint32 = 0
        rx_frame_octets_ok: np.uint32 = 0
        rx_crcerr: np.uint32 = 0
        tx_fragments: np.uint32 = 0
        tx_runt: np.uint32 = 0
        tx_64_bytes: np.uint32 = 0
        tx_65_to_127_bytes: np.uint32 = 0
        tx_128_to_255_bytes: np.uint32 = 0
        tx_256_to_511_bytes: np.uint32 = 0
        tx_512_to_1023_bytes: np.uint32 = 0
        tx_1024_to_1518_bytes: np.uint32 = 0
        tx_1519_to_max_bytes: np.uint32 = 0
        tx_oversize: np.uint32 = 0
        tx_frame_octets_ok: np.uint32 = 0
        tx_crcerr: np.uint32 = 0


class MacComponentManager(FhsLowLevelComponentManagerBase):
    def __init__(
        self: MacComponentManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            simulator_api=MacBaseControllerSimulator,
            **kwargs,
        )

    def go_to_idle(self: MacComponentManager) -> tuple[ResultCode, str]:
        result = self.deconfigure(MacConfig().to_dict())

        if result[0] is not ResultCode.FAILED:
            result = super().go_to_idle()
        else:
            self.logger.error("Unable to go to idle, result from deconfiguring was FAILED")

        return result

    # --------------------
    # Public Commands
    # --------------------
    # TODO Determine what needs to be communicated with here
    def start_communicating(self: MacComponentManager) -> None:
        """Establish communication with the component, then start monitoring."""
        if self._communication_state == CommunicationStatus.ESTABLISHED:
            self.logger.info("Already communicating.")
            return

        super().start_communicating()
