from dataclasses import dataclass

from dataclasses_json import dataclass_json
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

    @property
    def simulator_api_class(self) -> type[CircuitSwitchSimulator]:
        """:obj:`type[CircuitSwitchSimulator]`: The simulator API class for this IP block."""
        return CircuitSwitchSimulator

    def configure(self, config: CircuitSwitchConfigureArgin):
        """Configure the Circuit Switch."""
        for band in config.band:
            cs_config = CircuitSwitchConfig(output=band.get("output"), input=band.get("input"))
            result = super().configure(cs_config.to_dict())
            if result == 1:
                self.logger.error("Configuring Circuit Switch failed.")
                break
        return result
