from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_simulator import WidebandFrequencyShifterSimulator


@dataclass
class WidebandFrequencyShifterConfig(DataClassJsonMixin):
    transaction_id: Optional[str] = None
    shift_frequency: float = 0.0


##
# status class that will be populated by the APIs and returned to provide the status of Wideband frequency shifter
##
@dataclass
class WidebandFrequencyShifterStatus(DataClassJsonMixin):
    shift_frequency: float


class WidebandFrequencyShifterManager(BaseIPBlockManager[WidebandFrequencyShifterConfig, WidebandFrequencyShifterStatus]):
    """Wideband Frequency Shifter IP block manager."""

    @property
    def config_dataclass(self) -> type[WidebandFrequencyShifterConfig]:
        """:obj:`type[WidebandFrequencyShifterConfig]`: The configuration dataclass for the Wideband Frequency Shifter."""
        return WidebandFrequencyShifterConfig

    @property
    def status_dataclass(self) -> type[WidebandFrequencyShifterStatus]:
        """:obj:`type[WidebandFrequencyShifterStatus]`: The status dataclass for the Wideband Frequency Shifter."""
        return WidebandFrequencyShifterStatus

    @property
    def simulator_api_class(self) -> type[WidebandFrequencyShifterSimulator]:
        """:obj:`type[WidebandFrequencyShifterSimulator]`: The simulator API class for the Wideband Frequency Shifter."""
        return WidebandFrequencyShifterSimulator

    def deconfigure(self, config: WidebandFrequencyShifterConfig | None = None) -> int:
        """Deconfigure the Wideband Frequency Shifter."""
        if config is None:
            return super().recover()
        return super().deconfigure(config)
