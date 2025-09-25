from __future__ import annotations

import json
from logging import Logger

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["WidebandInputBufferSimulator"]


# link_failure: bool
# buffer_overflow: bool
# loss_of_signal: np.uint32
# error: bool
# loss_of_signal_seconds: np.uint32
# meta_band_id: np.uint8
# meta_dish_id: np.uint16
# rx_sample_rate: np.uint32
# meta_transport_sample_rate: np.uint32


class WidebandInputBufferSimulator(BaseSimulatorApi):
    def __init__(self, ip_block_name: str, logger: Logger) -> None:
        self.status_str = """{
                "link_failure": false,
                "buffer_overflow": false,
                "loss_of_signal": 0,
                "error": false,
                "loss_of_signal_seconds": 0,
                "meta_band_id": 1,
                "meta_dish_id": 1,
                "rx_sample_rate": 3960000000,
                "meta_transport_sample_rate": 3960000000,
                "packet_error": false,
                "packet_error_count": 0,
                "packet_drop": false,
                "packet_drop_count": 0,
                "rx_packet_rate": 1500000,
                "expected_sample_rate": 3960000000
            }"""

        super().__init__(ip_block_name, logger)

    def status(self, clear: bool = False) -> dict:
        return json.loads(self.status_str)

    def update_status(self, new_status: str):
        self.status_str = new_status
