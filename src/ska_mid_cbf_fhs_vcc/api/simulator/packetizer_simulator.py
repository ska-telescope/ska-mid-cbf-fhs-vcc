from __future__ import annotations

import json

from ska_control_model import ResultCode

from ska_mid_cbf_fhs_vcc.api.simulator.base_simulator_api import BaseSimulatorApi

__all__ = ["PacketizerSimulator"]


class PacketizerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> tuple[ResultCode, dict]:
        return (
            ResultCode.OK,
            json.loads(
                """
                {
                    "mac_source_register": 0,
                    "vid_register": 0,
                    "flags_register": 0,
                    "psn_register": 0,
                    "packet_count_register": 0
                }
                """
            ),
        )