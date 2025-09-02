from dataclasses import dataclass

from dataclasses_json import dataclass_json
from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.circuit_switch.circuit_switch_simulator import CircuitSwitchSimulator


@dataclass_json
@dataclass
class CircuitSwitchConfig:
    output: int
    input: int


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class CircuitSwitchStatus:
    num_inputs: int
    num_outputs: int
    connected: list[int]


@dataclass_json
@dataclass
class CircuitSwitchConfigureArgin:
    band: list[dict]


class CircuitSwitchManager(BaseIPBlockManager):
    """Circuit Switch IP block manager."""

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
        create_log_file: bool = True,
    ):
        super().__init__(
            ip_block_id,
            controlling_device_name,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            CircuitSwitchSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logging_level,
            create_log_file,
        )

    def configure(self, config: CircuitSwitchConfigureArgin):
        """Configure the Circuit Switch."""
        for band in config.band:
            cs_config = CircuitSwitchConfig(output=band.get("output"), input=band.get("input"))
            result = super().configure(cs_config.to_dict())
            if result == 1:
                self.logger.error("Configuring Circuit Switch failed.")
                break
        return result
