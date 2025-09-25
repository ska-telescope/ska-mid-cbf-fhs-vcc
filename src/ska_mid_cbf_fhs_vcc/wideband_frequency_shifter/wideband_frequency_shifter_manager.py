from dataclasses import dataclass

from dataclasses_json import dataclass_json
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

    @property
    def simulator_api_class(self) -> type[WidebandFrequencyShifterSimulator]:
        """:obj:`type[WidebandFrequencyShifterSimulator]`: The simulator API class for this IP block."""
        return WidebandFrequencyShifterSimulator

    def configure(self, config: WidebandFrequencyShifterConfig) -> int:
        """Configure the Wideband Frequency Shifter."""
        return super().configure(config.to_dict())

    def deconfigure(self, config: WidebandFrequencyShifterConfig | None = None) -> int:
        """Deconfigure the Wideband Frequency Shifter."""
        if config is None:
            return super().recover()
        return super().deconfigure(config.to_dict())
