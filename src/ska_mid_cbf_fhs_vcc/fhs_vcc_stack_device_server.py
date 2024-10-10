from tango.server import run

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channeliser.b123_vcc_osppfb_channeliser_device import B123VccOsppfbChanneliser
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_device import FrequencySliceSelection
from ska_mid_cbf_fhs_vcc.mac.mac_200_device import Mac200
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_device import PacketValidation
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_device import WidebandFrequencyShifter
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_device import WidebandInputBuffer

__all__ = ["main"]


def main(args=None, **kwargs):  # noqa: E302
    return run(
        classes=(
            B123VccOsppfbChanneliser,
            FrequencySliceSelection,
            Mac200,
            PacketValidation,
            WidebandInputBuffer,
            WidebandFrequencyShifter,
            VCCAllBandsController,
        ),
        args=args,
        **kwargs
    )


if __name__ == "__main__":  # noqa: #E305
    main()
