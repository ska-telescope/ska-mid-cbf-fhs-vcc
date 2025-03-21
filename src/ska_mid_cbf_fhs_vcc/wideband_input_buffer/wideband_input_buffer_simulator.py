from __future__ import annotations

import json
from logging import Logger

from ska_control_model import ResultCode
from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["WidebandInputBufferSimulator"]


# buffer_underflowed: bool
# buffer_overflowed: bool
# loss_of_signal: np.uint32
# error: bool
# loss_of_signal_seconds: np.uint32
# meta_band_id: np.uint8
# meta_dish_id: np.uint16
# rx_sample_rate: np.uint32
# meta_transport_sample_rate: np.uint32


class WidebandInputBufferSimulator(BaseSimulatorApi):
    def __init__(self: BaseSimulatorApi, device_id: str, logger: Logger) -> None:
        self.status_str = """{
                "buffer_underflowed": false,
                "buffer_overflowed": false,
                "loss_of_signal": 0,
                "error": false,
                "loss_of_signal_seconds": 0,
                "meta_band_id": 1,
                "meta_dish_id": 1,
                "rx_sample_rate": 3960000000,
                "meta_transport_sample_rate": 3960000000
            }"""

        super().__init__(device_id, logger)

    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        try:
            return ResultCode.OK, json.loads(self.status_str)

        except Exception as ex:
            print(f"status error {repr(ex)}")

    def update_status(self, new_status: str):
        self.status_str = new_status
