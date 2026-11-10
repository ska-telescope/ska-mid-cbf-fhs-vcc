from collections.abc import Callable

from pydantic import Field
from ska_mid_cbf_fhs_common import BaseIPBlockManager, FhsDataclass, UInt8, UInt64

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_simulator import B123VccOsppfbChannelizerSimulator


class B123VccOsppfbChannelizerConfig(FhsDataclass):
    sample_rate: UInt64
    pol: UInt8
    channel: int
    gain: float


##
# status class that will be populated by the APIs and returned to provide the status of the Frequency Slice Selection
##
class B123VccOsppfbChannelizerStatus(FhsDataclass):
    sample_rate: UInt64
    num_channels: int
    num_polarisations: int
    gains: list[float]


class B123VccOsppfbChannelizerConfigureArgin(FhsDataclass):
    sample_rate: UInt64 = 3960000000  # default values
    gains: list[float] = Field(default_factory=lambda: [1.0] * 20)  # default gain values
    transaction_id: str | None = None


class B123VccOsppfbChannelizerManager(BaseIPBlockManager[B123VccOsppfbChannelizerConfig, B123VccOsppfbChannelizerStatus]):
    """B123 VCC IP block manager."""

    @property
    def config_dataclass(self) -> type[B123VccOsppfbChannelizerConfig]:
        """:obj:`type[B123VccOsppfbChannelizerConfig]`: The configuration dataclass for the B123 VCC."""
        return B123VccOsppfbChannelizerConfig

    @property
    def status_dataclass(self) -> type[B123VccOsppfbChannelizerStatus]:
        """:obj:`type[B123VccOsppfbChannelizerStatus]`: The status dataclass for the B123 VCC."""
        return B123VccOsppfbChannelizerStatus

    @property
    def simulator_api_class(self) -> type[B123VccOsppfbChannelizerSimulator]:
        """:obj:`type[B123VccOsppfbChannelizerSimulator]`: The simulator API class for the B123 VCC."""
        return B123VccOsppfbChannelizerSimulator

    def configure(self, config: B123VccOsppfbChannelizerConfigureArgin) -> int:
        """Configure the B123 VCC."""
        return self._generate_and_configure(config, super().configure)

    def deconfigure(self, config: B123VccOsppfbChannelizerConfigureArgin | None = None) -> int:
        """Deconfigure the B123 VCC."""
        if config is None:
            config = B123VccOsppfbChannelizerConfigureArgin()
        return self._generate_and_configure(config, super().deconfigure)

    def _generate_and_configure(
        self,
        vcc_config_argin: B123VccOsppfbChannelizerConfigureArgin,
        configure_fn: Callable[[B123VccOsppfbChannelizerConfig], int],
    ) -> int:
        # Channels are dual-polarized i.e. 2 gain values per channel[x, y]
        num_channels = len(vcc_config_argin.gains) // 2
        transaction_id = vcc_config_argin.transaction_id
        for polarization in (0, 1):
            for i in range(num_channels):
                vcc_config = B123VccOsppfbChannelizerConfig(
                    sample_rate=vcc_config_argin.sample_rate,
                    gain=vcc_config_argin.gains[i + polarization * num_channels],
                    channel=i,
                    pol=polarization,
                )

                self.log_info(f"VCC JSON CONFIG channel={i} pol={polarization}: {vcc_config}", transaction_id)

                result = configure_fn(vcc_config)
                if result == 1:
                    self.log_error("Configuring VCC failed.", transaction_id)
                    return result
        return result
