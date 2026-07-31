from __future__ import annotations

import json

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = ["VCCBiteSimulator"]


class VCCBiteSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        # TODO: Fill in these status fields
        return json.loads(
            """
            {

            }
            """
        )
