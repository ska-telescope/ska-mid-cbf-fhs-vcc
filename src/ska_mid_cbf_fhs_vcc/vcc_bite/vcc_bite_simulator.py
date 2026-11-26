from __future__ import annotations

from ska_mid_cbf_fhs_common import BaseSimulatorApi

__all__ = [
    "GaussianNoiseDriverSimulator",
    "NoiseDiodeSimulator",
    "PolarizationCouplerSimulator",
    "SPFRxPacketizerSimulator",
    "VCCBiteManagerSimulator",
    "VCCBiteSimulator",
    "VCCBiteToneGenSimulator",
    "VCCSourceSelectSimulator",
]


class VCCSourceSelectSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "source_select": 0,
            "test_select": False,
        }


class VCCBiteSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "band": 1,
            "start_time": 0,
            "sample_rate": 0,
            "speed": 0,
        }


class VCCBiteToneGenSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "sample_rate": 0,
            "frequency": 0,
            "magnitude": 0,
            "band": 1,
        }


class GaussianNoiseDriverSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "seed": 0,
            "mean": 0,
            "std_dev": 0,
        }


class NoiseDiodeSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "sample_rate": 0,
            "switching_period": 0.0,
            "seed": 0,
            "std_dev": 0.0,
        }


class PolarizationCouplerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "correlation_coefficient": 0.0,
            "delay_enable": False,
        }


class SPFRxPacketizerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "running": False,
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
            "noise_diode_rising_holdoff_b": 0.0,
        }


class VCCBiteManagerSimulator(BaseSimulatorApi):
    def status(self, clear: bool = False) -> dict:
        return {
            "source_select": [
                {
                    "source_select": 0,
                    "test_select": False,
                },
                {
                    "source_select": 0,
                    "test_select": False,
                },
                {
                    "source_select": 0,
                    "test_select": False,
                },
            ],
            "bite_control": [
                {
                    "band": 1,
                    "start_time": 0,
                    "sample_rate": 0,
                    "speed": 0,
                },
                {
                    "band": 1,
                    "start_time": 0,
                    "sample_rate": 0,
                    "speed": 0,
                },
                {
                    "band": 1,
                    "start_time": 0,
                    "sample_rate": 0,
                    "speed": 0,
                },
            ],
            "bite_tone_gen": [
                {
                    "sample_rate": 0,
                    "frequency": 0,
                    "magnitude": 0,
                    "band": 1,
                },
                {
                    "sample_rate": 0,
                    "frequency": 0,
                    "magnitude": 0,
                    "band": 1,
                },
                {
                    "sample_rate": 0,
                    "frequency": 0,
                    "magnitude": 0,
                    "band": 1,
                },
            ],
            "bite_noise_gen_polX": [
                {
                    "seed": 0,
                    "mean": 0,
                    "std_dev": 0,
                },
                {
                    "seed": 0,
                    "mean": 0,
                    "std_dev": 0,
                },
                {
                    "seed": 0,
                    "mean": 0,
                    "std_dev": 0,
                },
            ],
            "bite_noise_gen_polY": [
                {
                    "seed": 0,
                    "mean": 0,
                    "std_dev": 0,
                },
                {
                    "seed": 0,
                    "mean": 0,
                    "std_dev": 0,
                },
                {
                    "seed": 0,
                    "mean": 0,
                    "std_dev": 0,
                },
            ],
            "bite_noise_diode_polX": [
                {
                    "sample_rate": 0,
                    "switching_period": 0.0,
                    "seed": 0,
                    "std_dev": 0.0,
                },
                {
                    "sample_rate": 0,
                    "switching_period": 0.0,
                    "seed": 0,
                    "std_dev": 0.0,
                },
                {
                    "sample_rate": 0,
                    "switching_period": 0.0,
                    "seed": 0,
                    "std_dev": 0.0,
                },
            ],
            "bite_noise_diode_polY": [
                {
                    "sample_rate": 0,
                    "switching_period": 0.0,
                    "seed": 0,
                    "std_dev": 0.0,
                },
                {
                    "sample_rate": 0,
                    "switching_period": 0.0,
                    "seed": 0,
                    "std_dev": 0.0,
                },
                {
                    "sample_rate": 0,
                    "switching_period": 0.0,
                    "seed": 0,
                    "std_dev": 0.0,
                },
            ],
            "polarization_coupler": [
                {
                    "correlation_coefficient": 0.0,
                    "delay_enable": False,
                },
                {
                    "correlation_coefficient": 0.0,
                    "delay_enable": False,
                },
                {
                    "correlation_coefficient": 0.0,
                    "delay_enable": False,
                },
            ],
            "spfrx_packetizer": [
                {
                    "running": False,
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
                    "noise_diode_rising_holdoff_b": 0.0,
                },
                {
                    "running": False,
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
                    "noise_diode_rising_holdoff_b": 0.0,
                },
                {
                    "running": False,
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
                    "noise_diode_rising_holdoff_b": 0.0,
                },
            ],
        }
