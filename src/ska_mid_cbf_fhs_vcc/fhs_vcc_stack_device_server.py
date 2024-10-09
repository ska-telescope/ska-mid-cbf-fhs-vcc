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
        ),
        args=args,
        **kwargs,
    )


def check_if_bitstream_exists():
    logger = logging.Logger(name="FhsVccStackDs")

    try:
        _config_location = os.environ["CONFIG_MAP_LOCATION"]

        _api_config_reader: APIConfigReader = APIConfigReader(_config_location, logger)
        bitstream_path: str = _api_config_reader.getConfigMapValue("bitstreamPath")
        firmware_version: str = _api_config_reader.getConfigMapValue("firmwareVersion")
        firmware_version = f"_{firmware_version.replace(".", "_")}"

        if os.path.exists(bitstream_path):
            print(".......Starting to poll bitstream.......")

            polling2.poll(
                check_bitstream_available,
                args=(bitstream_path, firmware_version, logger),
                timeout=60,
                step=0.5,
            )
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), bitstream_path)

    except polling2.TimeoutException as te:
        print(f"Polling for bitstream timeout, {firmware_version} not found!")
        raise te
    except KeyError as ke:
        print("CONFIG_MAP_LOCATION env variable not found")
        raise ke


def check_bitstream_available(bitstream_path, firmware_version, logger):
    if os.path.exists(f"{bitstream_path}/{firmware_version}"):
        print(f"Bitstream {firmware_version} found!")
        return True
    else:
        print(f"...Waiting for bitstream {firmware_version}...")
        return False


if __name__ == "__main__":  # noqa: #E305
    main()
