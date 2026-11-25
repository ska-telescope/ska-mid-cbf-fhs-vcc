from __future__ import annotations

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["PacketValidationSimulator"]


class PacketValidationSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "drop_dst_mac": True,
            "drop_src_mac": True,
            "drop_ethertype": True,
            "drop_antenna_id": True,
            "egress_cnt": 0,
            "ingress_error_cnt": 0,
            "size_error_cnt": 0,
            "exp_dst_mac": 0,
            "last_wrong_dst_mac": 0,
            "wrong_dst_mac_cnt": 0,
            "exp_src_mac": 0,
            "last_wrong_src_mac": 0,
            "wrong_src_mac_cnt": 0,
            "exp_ethertype": 0,
            "last_wrong_ethertype": 0,
            "wrong_ethertype_cnt": 0,
            "exp_antenna_id": 0,
            "last_wrong_antenna_id": 0,
            "wrong_antenna_id_cnt": 0,
        }
