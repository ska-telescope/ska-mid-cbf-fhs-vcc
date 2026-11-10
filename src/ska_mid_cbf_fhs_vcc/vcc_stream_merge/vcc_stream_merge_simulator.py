from __future__ import annotations

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["VCCStreamMergeSimulator"]


class VCCStreamMergeSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "mac_destination": 0,
            "vid": 0,
            "vcc_id": 0,
            "fs_id": 0,
            "timestamp": 0,
            "psn": [0],
            "packet_count": 0,
            "diag_stop_monitor": 0,
        }
