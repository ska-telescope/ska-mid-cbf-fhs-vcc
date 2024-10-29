import errno
import logging
import os

import polling2
from tango.server import run

from ska_mid_cbf_fhs_vcc.api.common.api_config_reader import APIConfigReader
from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channeliser.b123_vcc_osppfb_channeliser_device import B123VccOsppfbChanneliser
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_device import FrequencySliceSelection
from ska_mid_cbf_fhs_vcc.mac.mac_200_device import Mac200
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_device import PacketValidation
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_device import WidebandFrequencyShifter
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_device import WidebandInputBuffer

10
__all__ = ["main"]


def main(args=None, **kwargs):  # noqa: E302
    check_if_bitstream_exists()

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
        **kwargs,
    )


def check_if_bitstream_exists():
    logger = logging.Logger(name="FhsVccStackDs", level=logging.INFO)

    try:
        _config_location = os.environ["CONFIG_MAP_LOCATION"]
        _api_config_reader: APIConfigReader = APIConfigReader(_config_location, logger)

        bitstream_path: str = _api_config_reader.getConfigMapValue("bitstreamPath")
        bitstream_id: str = _api_config_reader.getConfigMapValue("bitstreamId")
        bitstream_version: str = _api_config_reader.getConfigMapValue("bitstreamVersion")

        driver_path = os.path.join(bitstream_path, bitstream_id, bitstream_version, "drivers")

        if os.path.exists(bitstream_path):
            print("INFO: Starting to poll bitstream.......")

            polling2.poll(
                check_bitstream_available,
                args=(driver_path,),
                timeout=60,
                step=0.5,
            )
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), bitstream_path)

    except polling2.TimeoutException as te:
        print(f"ERROR: Polling for bitstream timeout, {driver_path} not found!")
        raise te
    except KeyError as ke:
        print("ERROR: CONFIG_MAP_LOCATION env variable not found")
        raise ke


def check_bitstream_available(driver_path):
    if os.path.exists(driver_path):
        print(f"INFO: Bitstream {driver_path} found!")
        return True
    else:
        print(f"INFO: Waiting for bitstream {driver_path}")
        return False


if __name__ == "__main__":  # noqa: #E305
    main()
