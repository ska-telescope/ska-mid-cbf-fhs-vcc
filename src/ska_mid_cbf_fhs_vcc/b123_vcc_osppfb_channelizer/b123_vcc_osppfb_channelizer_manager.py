from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from dataclasses_json import dataclass_json
from ska_control_model import SimulationMode

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_simulator import (
    B123VccOsppfbChannelizerSimulator,
)
from ska_mid_cbf_fhs_vcc.ip_block_manager.base_ip_block_manager import BaseIPBlockManager


@dataclass_json
@dataclass
class B123VccOsppfbChannelizerConfig:
    sample_rate: np.uint64
    pol: dict
    channel: np.uint16
    gain: np.float32


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
@dataclass_json
@dataclass
class B123VccOsppfbChannelizerStatus:
    sample_rate: np.uint32
    num_channels: int
    num_polarisations: int
    gains: list[np.float32]


@dataclass_json
@dataclass
class B123VccOsppfbChannelizerConfigureArgin:
    sample_rate: np.uint64 = 3960000000  # default values
    gains: list[float] = field(
        default_factory=lambda: [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ]
    )  # default gain values


class B123VccOsppfbChannelizerManager(BaseIPBlockManager):
    """Mock B123 VCC IP block manager."""

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
            B123VccOsppfbChannelizerSimulator,
            simulation_mode,
            emulation_mode,
            emulator_ip_block_id,
            emulator_id,
            emulator_base_url,
            logging_level,
        )

    def configure(self, config: B123VccOsppfbChannelizerConfigureArgin):
        """Configure the B123 VCC."""
        return self._generate_and_configure(config, super().configure)

    def deconfigure(self, config: B123VccOsppfbChannelizerConfigureArgin | None):
        """Deconfigure the B123 VCC."""
        if config is None:
            config = B123VccOsppfbChannelizerConfigureArgin()
        return self._generate_and_configure(config, super().deconfigure)

    def _generate_and_configure(
        self,
        vcc_config_argin: B123VccOsppfbChannelizerConfigureArgin,
        configure_fn: Callable[[B123VccOsppfbChannelizerConfigureArgin], int],
    ) -> int:
        # Channels are dual-polarized i.e. 2 gain values per channel[x, y]
        num_channels = len(vcc_config_argin.gains) // 2
        for polarization in (0, 1):
            for i in range(num_channels):
                vcc_config = B123VccOsppfbChannelizerConfig(
                    sample_rate=vcc_config_argin.sample_rate,
                    gain=vcc_config_argin.gains[i + polarization * num_channels],
                    channel=i,
                    pol=polarization,
                )

                self.logger.info(f"VCC JSON CONFIG channel={i} pol={polarization}: {vcc_config}")

                result = configure_fn(vcc_config.to_dict())
                if result == 1:
                    self.logger.error("Configuring VCC failed.")
                    return result
        return result
