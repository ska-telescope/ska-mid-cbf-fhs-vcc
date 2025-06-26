from dataclasses import dataclass, field
from logging import Logger

from dataclasses_json import dataclass_json
from ska_control_model import SimulationMode

from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_simulator import FrequencySliceSelectionSimulator
from ska_mid_cbf_fhs_vcc.ip_block_manager.base_ip_block_manager import BaseIPBlockManager


@dataclass_json
@dataclass
class FrequencySliceSelectionConfig:
    band_select: int = 1
    band_start_channel: list[int] = field(default_factory=lambda: [0, 1, 2])


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class FrequencySliceSelectionStatus:
    band_select: int
    band_start_channel: list[int]


class FrequencySliceSelectionManager(BaseIPBlockManager):
    """Mock Frequency Slice Selection IP block manager."""

    def __init__(
        self,
        ip_block_id: str,
        bitstream_path: str,
        bitstream_id: str,
        bitstream_version: str,
        firmware_ip_block_id: str,
        simulation_mode: SimulationMode = SimulationMode.TRUE,
        emulation_mode: bool = False,
        emulator_ip_block_id: str | None = None,
        emulator_id: str | None = None,
        emulator_base_url: str | None = None,
        logger: Logger | None = None,
    ):
        super().__init__(
            ip_block_id,
            bitstream_path,
            bitstream_id,
            bitstream_version,
            firmware_ip_block_id,
            FrequencySliceSelectionSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logger,
        )

    def configure(self, config: FrequencySliceSelectionConfig):
        """Configure the Frequency Slice Selection."""
        return super().configure(config.to_dict())

    def deconfigure(self, config: FrequencySliceSelectionConfig | None):
        """Deconfigure the Frequency Slice Selection."""
        if config is None:
            return super().recover()
        return super().deconfigure(config.to_dict())
