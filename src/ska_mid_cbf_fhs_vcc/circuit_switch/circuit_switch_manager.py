from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin
from ska_mid_cbf_fhs_common import BaseIPBlockManager

from ska_mid_cbf_fhs_vcc.circuit_switch.circuit_switch_simulator import CircuitSwitchSimulator


@dataclass
class CircuitSwitchConfig(DataClassJsonMixin):
    output: int
    input: int


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass
class CircuitSwitchStatus(DataClassJsonMixin):
    num_inputs: int
    num_outputs: int
    connected: list[int]


@dataclass
class CircuitSwitchConfigureArgin(DataClassJsonMixin):
    band: list[dict]


class CircuitSwitchManager(BaseIPBlockManager[CircuitSwitchConfig, CircuitSwitchStatus]):
    """Circuit Switch IP block manager."""

    @property
    def config_dataclass(self) -> type[CircuitSwitchConfig]:
        """:obj:`type[CircuitSwitchConfig]`: The configuration dataclass for the Circuit Switch."""
        return CircuitSwitchConfig

    @property
    def status_dataclass(self) -> type[CircuitSwitchStatus]:
        """:obj:`type[CircuitSwitchStatus]`: The status dataclass for the Circuit Switch."""
        return CircuitSwitchStatus

    @property
    def simulator_api_class(self) -> type[CircuitSwitchSimulator]:
        """:obj:`type[CircuitSwitchSimulator]`: The simulator API class for the Circuit Switch."""
        return CircuitSwitchSimulator

    def configure(self, config: CircuitSwitchConfigureArgin):
        """Configure the Circuit Switch."""
        for band in config.band:
            cs_config = CircuitSwitchConfig(output=band.get("output"), input=band.get("input"))
            result = super().configure(cs_config)
            if result == 1:
                self.logger.error("Configuring Circuit Switch failed.")
                break
        return result
