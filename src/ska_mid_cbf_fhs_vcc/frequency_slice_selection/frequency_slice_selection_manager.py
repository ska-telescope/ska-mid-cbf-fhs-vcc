from dataclasses import dataclass, field

from dataclasses_json import dataclass_json
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_simulator import FrequencySliceSelectionSimulator


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
    """Frequency Slice Selection IP block manager."""

    @property
    def simulator_api_class(self) -> type[FrequencySliceSelectionSimulator]:
        """:obj:`type[FrequencySliceSelectionSimulator]`: The simulator API class for this IP block."""
        return FrequencySliceSelectionSimulator

    def configure(self, config: FrequencySliceSelectionConfig) -> int:
        """Configure the Frequency Slice Selection."""
        return super().configure(config.to_dict())

    def deconfigure(self, config: FrequencySliceSelectionConfig | None = None) -> int:
        """Deconfigure the Frequency Slice Selection."""
        if config is None:
            return super().recover()
        return super().deconfigure(config.to_dict())
