from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_simulator import FrequencySliceSelectionSimulator


@dataclass
class FrequencySliceSelectionConfig(DataClassJsonMixin):
    band_select: int = 1
    band_start_channel: list[int] = field(default_factory=lambda: [0, 1, 2])


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass
class FrequencySliceSelectionStatus(DataClassJsonMixin):
    band_select: int
    band_start_channel: list[int]


class FrequencySliceSelectionManager(BaseIPBlockManager[FrequencySliceSelectionConfig, FrequencySliceSelectionStatus]):
    """Frequency Slice Selection IP block manager."""

    @property
    def config_dataclass(self) -> type[FrequencySliceSelectionConfig]:
        """:obj:`type[FrequencySliceSelectionConfig]`: The configuration dataclass for the Frequency Slice Selection block."""
        return FrequencySliceSelectionConfig

    @property
    def status_dataclass(self) -> type[FrequencySliceSelectionStatus]:
        """:obj:`type[FrequencySliceSelectionStatus]`: The status dataclass for the Frequency Slice Selection block."""
        return FrequencySliceSelectionStatus

    @property
    def simulator_api_class(self) -> type[FrequencySliceSelectionSimulator]:
        """:obj:`type[FrequencySliceSelectionSimulator]`: The simulator API class for the Frequency Slice Selection block."""
        return FrequencySliceSelectionSimulator

    def deconfigure(self, config: FrequencySliceSelectionConfig | None = None) -> int:
        """Deconfigure the Frequency Slice Selection."""
        if config is None:
            return super().recover()
        return super().deconfigure(config)
