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
                "receive_enable": true,
                "packet_error": false,
                "packet_drop": false,
                "link_failure": false,
                "buffer_overflow": false,
                "error": false,
                "firmware_band": 1,
                "stream_rate": 1500000,
                "packet_rate": 1500000,
                "noise_diode_transition_holdoff_count": 1,
                "packet_error_count": 0,
                "packet_drop_count": 0,
                "loss_of_signal_seconds": 0,
                "meta_ethertype": 1,
                "meta_dish_id": 1,
                "meta_band_id": 1,
                "meta_utc_time_code": 0,
                "meta_transport_sample_rate": 3960000000,
                "meta_hardware_source_id": 0,
                "rx_packet_rate": 1500000,
                "rx_sample_rate": 3960000000
            }"""

        super().__init__(ip_block_name, logger)

    def status(self, clear: bool = False) -> dict:
        try:
            return json.loads(self.status_str)
        except Exception as ex:
            self._logger.error(f"Unable to convert status to dict: {ex.with_traceback()}")

    def update_status(self, new_status: str):
        self.status_str = new_status
