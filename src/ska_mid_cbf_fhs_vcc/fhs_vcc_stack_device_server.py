import subprocess

from ska_mid_cbf_fhs_common import FtileEthernet, WidebandPowerMeter
from tango.server import run

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

__all__ = ["main"]


class Ethernet200Gb(FtileEthernet):
    pass


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
            Ethernet200Gb,
            B123WidebandPowerMeter,
            B45AWidebandPowerMeter,
            B5BWidebandPowerMeter,
            FSWidebandPowerMeter,
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
