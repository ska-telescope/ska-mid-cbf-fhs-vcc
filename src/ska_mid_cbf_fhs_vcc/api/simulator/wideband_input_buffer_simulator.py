from __future__ import annotations

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

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
    def status(self, clear: bool = False) -> tuple[ResultCode, str]:
        return (
            ResultCode.OK,
            """{
                buffer_underflowed: false,
                buffer_overflowed: false,
                error: false,
                loss_of_signal_seconds: 0,
                meta_band_id: 123,
                meta_dish_id: 456,
                rx_sample_rate: 10,
                meta_transport_sample_rate: 10
            }""",
        )
