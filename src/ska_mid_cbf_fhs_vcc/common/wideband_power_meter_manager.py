from dataclasses import dataclass

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import SimulationMode

from ska_mid_cbf_fhs_vcc.common.wideband_power_meter_simulator import WidebandPowerMeterSimulator
from ska_mid_cbf_fhs_vcc.ip_block_manager.base_ip_block_manager import BaseIPBlockManager


@dataclass_json
@dataclass
class WidebandPowerMeterConfig:
    averaging_time: float  # Averaging interval in seconds
    flagging: np.uint8  # Handling for flagged data, 0 - ignore, 1 - use, 2 - saturate and use


##
# status class that will be populated by the APIs and returned to provide the status of Wideband Power Meter
##
@dataclass
class WidebandPowerMeterStatus:
    timestamp: float  # Timestamp in seconds of the last sample in the averaging interval
    avg_power_pol_x: float  # Average signal power
    avg_power_pol_y: float  # Average signal power
    avg_power_nd_on_pol_x: float  # Average signal power, noise diode ON
    avg_power_nd_on_pol_y: float  # Average signal power, noise diode ON
    avg_power_nd_off_pol_x: float  # Average signal power, noise diode OFF
    avg_power_nd_off_pol_y: float  # Average signal power, noise diode OFF
    avg_power_nd_trn_pol_x: float  # Average signal power, noise diode transition
    avg_power_nd_trn_pol_y: float  # Average signal power, noise diode transition
    flag: bool  # Flagged data detected during averaging interval
    # Overflow detected during averaging interval: bit 0 nd on pol X, bit 1 nd on pol Y, bit 2 nd off pol X, bit 3 nd off pol Y
    overflow: np.uint8


class WidebandPowerMeterManager(BaseIPBlockManager):
    """Mock Wideband Power Meter IP block manager."""

    def __init__(
        self,
        ip_block_id: str,
        controlling_device_name: str,
        bitstream_path: str,
        bitstream_id: str,
        bitstream_version: str,
        firmware_ip_block_id: str,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        emulator_ip_block_id: str | None = None,
        emulator_id: str | None = None,
        emulator_base_url: str | None = None,
        logging_level: str = "INFO",
    ):
        super().__init__(
            ip_block_id,
            controlling_device_name,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            WidebandPowerMeterSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logging_level,
        )
        self.logger.debug("##################### WIDEBAND POWER METER DEBUG MESSAGE #########################")

    def configure(self, config: WidebandPowerMeterConfig):
        """Configure the Wideband Power Meter."""
        return super().configure(config.to_dict())

    def test(self):
        self.logger.critical("!!!!!!!!!!!!!!!!!!!!!!!!! WIDEBAND POWER METER CRITICAL MESSAGE !!!!!!!!!!!!!!!!!!!!!!!!!")
        self.logger.error("&&&&&&&&&&&&&&&&&&&&&&&&& WIDEBAND POWER METER ERROR MESSAGE &&&&&&&&&&&&&&&&&&&&&&&&&")
        self.logger.warning("@@@@@@@@@@@@@@@@@@@@@@@@@ WIDEBAND POWER METER WARNING MESSAGE @@@@@@@@@@@@@@@@@@@@@@@@@")
        self.logger.info("######################### WIDEBAND POWER METER INFO MESSAGE #########################")
        self.logger.debug("????????????????????????? WIDEBAND POWER METER DEBUG MESSAGE ?????????????????????????")
