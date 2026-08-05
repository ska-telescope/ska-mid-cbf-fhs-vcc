from __future__ import annotations

import json

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = [
    "VCCSourceSelectSimulator",
    "VCCBiteSimulator",
    "VCCBiteToneGenSimulator",
    "GaussianNoiseDriverSimulator",
    "NoiseDiodeSimulator",
    "PolarizationCouplerSimulator",
    "SPFRxPacketizerSimulator",
    "VCCBiteManagerSimulator",
]


class VCCSourceSelectSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "source_select": 0,
                "test_select": false
            }
            """
        )


class VCCBiteSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "band": 1,
                "start_time": 0,
                "sample_rate": 0,
                "speed": 0
            }
            """
        )


class VCCBiteToneGenSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "sample_rate": 0,
                "frequency": 0,
                "magnitude": 0,
                "band": 1
            }
            """
        )


class GaussianNoiseDriverSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "seed": 0,
                "mean": 0,
                "std_dev": 0
            }
            """
        )


class NoiseDiodeSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "switching_period": 0.0,
                "seed": 0,
                "std_dev": 0.0
            }
            """
        )


class PolarizationCouplerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "pol_coupling_rho": 0.0,
                "pol_Y_1_sample_delay": false
            }
            """
        )


class SPFRxPacketizerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "running": false,
                "fifo_overflow_error": 0,
                "local_mac": 0,
                "remote_mac": 0,
                "ethertype": 0,
                "dish_id": 0,
                "hw_src_id": 0,
                "band": 0,
                "sample_rate": 0,
                "sample_rate_b": 0,
                "noise_diode_rising_holdoff": 0.0,
                "noise_diode_rising_holdoff_b": 0.0
            }
            """
        )


class VCCBiteManagerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return json.loads(
            """
            {
                "source_select": [
                    {
                        "source_select": 0,
                        "test_select": false
                    },
                    {
                        "source_select": 0,
                        "test_select": false
                    },
                    {
                        "source_select": 0,
                        "test_select": false
                    }
                ],
                "bite_control": [
                    {
                        "band": 1,
                        "start_time": 0,
                        "sample_rate": 0,
                        "speed": 0
                    },
                    {
                        "band": 1,
                        "start_time": 0,
                        "sample_rate": 0,
                        "speed": 0
                    },
                    {
                        "band": 1,
                        "start_time": 0,
                        "sample_rate": 0,
                        "speed": 0
                    }
                ],
                "bite_tone_gen": [
                    {
                        "sample_rate": 0,
                        "frequency": 0,
                        "magnitude": 0,
                        "band": 1
                    },
                    {
                        "sample_rate": 0,
                        "frequency": 0,
                        "magnitude": 0,
                        "band": 1
                    },
                    {
                        "sample_rate": 0,
                        "frequency": 0,
                        "magnitude": 0,
                        "band": 1
                    }
                ],
                "bite_noise_gen_polX": [
                    {
                        "seed": 0,
                        "mean": 0,
                        "std_dev": 0
                    },
                    {
                        "seed": 0,
                        "mean": 0,
                        "std_dev": 0
                    },
                    {
                        "seed": 0,
                        "mean": 0,
                        "std_dev": 0
                    }
                ],
                "bite_noise_gen_polY": [
                    {
                        "seed": 0,
                        "mean": 0,
                        "std_dev": 0
                    },
                    {
                        "seed": 0,
                        "mean": 0,
                        "std_dev": 0
                    },
                    {
                        "seed": 0,
                        "mean": 0,
                        "std_dev": 0
                    }
                ],
                "bite_noise_diode_polX": [
                    {
                        "switching_period": 0.0,
                        "seed": 0,
                        "std_dev": 0.0
                    },
                    {
                        "switching_period": 0.0,
                        "seed": 0,
                        "std_dev": 0.0
                    },
                    {
                        "switching_period": 0.0,
                        "seed": 0,
                        "std_dev": 0.0
                    }
                ],
                "bite_noise_diode_polY": [
                    {
                        "switching_period": 0.0,
                        "seed": 0,
                        "std_dev": 0.0
                    },
                    {
                        "switching_period": 0.0,
                        "seed": 0,
                        "std_dev": 0.0
                    },
                    {
                        "switching_period": 0.0,
                        "seed": 0,
                        "std_dev": 0.0
                    }
                ],
                "polarization_coupler": [
                    {
                        "pol_coupling_rho": 0.0,
                        "pol_Y_1_sample_delay": false
                    },
                    {
                        "pol_coupling_rho": 0.0,
                        "pol_Y_1_sample_delay": false
                    },
                    {
                        "pol_coupling_rho": 0.0,
                        "pol_Y_1_sample_delay": false
                    }
                ],
                "spfrx_packetizer": [
                    {
                        "running": false,
                        "fifo_overflow_error": 0,
                        "local_mac": 0,
                        "remote_mac": 0,
                        "ethertype": 0,
                        "dish_id": 0,
                        "hw_src_id": 0,
                        "band": 0,
                        "sample_rate": 0,
                        "sample_rate_b": 0,
                        "noise_diode_rising_holdoff": 0.0,
                        "noise_diode_rising_holdoff_b": 0.0
                    },
                    {
                        "running": false,
                        "fifo_overflow_error": 0,
                        "local_mac": 0,
                        "remote_mac": 0,
                        "ethertype": 0,
                        "dish_id": 0,
                        "hw_src_id": 0,
                        "band": 0,
                        "sample_rate": 0,
                        "sample_rate_b": 0,
                        "noise_diode_rising_holdoff": 0.0,
                        "noise_diode_rising_holdoff_b": 0.0
                    },
                    {
                        "running": false,
                        "fifo_overflow_error": 0,
                        "local_mac": 0,
                        "remote_mac": 0,
                        "ethertype": 0,
                        "dish_id": 0,
                        "hw_src_id": 0,
                        "band": 0,
                        "sample_rate": 0,
                        "sample_rate_b": 0,
                        "noise_diode_rising_holdoff": 0.0,
                        "noise_diode_rising_holdoff_b": 0.0
                    }
                ]
            }
            """
        )
