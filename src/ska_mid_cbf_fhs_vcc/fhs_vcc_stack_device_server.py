import subprocess

from ska_mid_cbf_fhs_common import WidebandPowerMeter, FtileEthernet
from tango.server import run

from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channeliser.b123_vcc_osppfb_channeliser_device import B123VccOsppfbChanneliser
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_device import FrequencySliceSelection
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_device import PacketValidation
from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_device import VCCStreamMerge
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_device import WidebandFrequencyShifter
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_device import WidebandInputBuffer

__all__ = ["main"]


class B123WidebandPowerMeter(WidebandPowerMeter):
    pass


class B45AWidebandPowerMeter(WidebandPowerMeter):
    pass


class B5BWidebandPowerMeter(WidebandPowerMeter):
    pass


class FSWidebandPowerMeter(WidebandPowerMeter):
    pass


def main(args=None, **kwargs):  # noqa: E302
    # Call the kubectl command and wait until the bitstreams have been successfully downloaded
    wait_for_job_completion("bitstream-download-job")

    return run(
        classes=(
            B123VccOsppfbChanneliser,
            FrequencySliceSelection,
            FtileEthernet,
            PacketValidation,
            WidebandInputBuffer,
            WidebandFrequencyShifter,
            B123WidebandPowerMeter,
            B45AWidebandPowerMeter,
            B5BWidebandPowerMeter,
            FSWidebandPowerMeter,
            VCCStreamMerge,
            VCCAllBandsController,
        ),
        args=args,
        **kwargs,
    )


def wait_for_job_completion(job_name) -> bool:
    cmd = ["kubectl", "wait", "--for=condition=complete", "--timeout=60s", f"job/{job_name}"]

    try:
        subprocess.run(cmd, check=True)
        print(f"Job {job_name} completed successfully...")
        return True
    except subprocess.CalledProcessError as ex:
        print(f"Job {job_name} did not complete successfully.. {repr(ex)}")
        return False


if __name__ == "__main__":  # noqa: #E305
    main()
