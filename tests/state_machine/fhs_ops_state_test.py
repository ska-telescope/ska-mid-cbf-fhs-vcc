from __future__ import annotations

from typing import Iterator
from unittest.mock import Mock
import unittest

import logging

from ska_control_model import AdminMode, ObsState, ResultCode
from ska_tango_testing import context
from ska_tango_testing.mock.tango import MockTangoEventCallbackGroup
from tango import DevState

from ska_mid_cbf_fhs_vcc.common.fhs_obs_state import FhsObsStateMachine, FhsObsStateModel
from ska_mid_cbf_fhs_vcc.common.fhs_base_device import FhsBaseDevice

class FhsObsStateTest(unittest.TestCase):
    
    def __init__(self, methodName: str = "runTest") -> None:
        self.obs_state = None
        super().__init__(methodName)
    
    def test_init(self):
        obs_state_model = FhsObsStateModel(
            logger=None,
            callback=self._update_obs_state,
            state_machine_factory=FhsObsStateMachine,
        )
        
        self.assertIsNotNone(obs_state_model)
        
        obs_state_model.perform_action("configure_invoked")
        
    def _update_obs_state(self: FhsObsStateTest, obs_state: ObsState) -> None:
        self.obs_state = obs_state
        
if __name__ == "__main__":
    unittest.main()