from dataclasses import dataclass

from dataclasses_json import dataclass_json
from ska_control_model import SimulationMode
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_simulator import WidebandFrequencyShifterSimulator


@dataclass_json
@dataclass
class WidebandFrequencyShifterConfig:
    shift_frequency: float = 0.0


##
# status class that will be populated by the APIs and returned to provide the status of Wideband frequency shifter
##
@dataclass_json
@dataclass
class WidebandFrequencyShifterStatus:
    shift_frequency: float


class WidebandFrequencyShifterManager(BaseIPBlockManager):
    """Wideband Frequency Shifter IP block manager."""

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
            WidebandFrequencyShifterSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logging_level,
            create_log_file,
        )

    def configure(self, config: WidebandFrequencyShifterConfig) -> int:
        """Configure the Wideband Frequency Shifter."""
        return super().configure(config.to_dict())

    def deconfigure(self, config: WidebandFrequencyShifterConfig | None = None) -> int:
        """Deconfigure the Wideband Frequency Shifter."""
        if config is None:
            return super().recover()
        return super().deconfigure(config.to_dict())
