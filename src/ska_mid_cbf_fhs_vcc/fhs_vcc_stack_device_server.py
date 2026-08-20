import os
import re
import subprocess

from tango.server import run

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

__all__ = ["main"]

JOB_NAME_PREFIX = "fhs-vcc-bitstream-download-job"
HOST_NAME_PATTERN = re.compile(r"fhs-vcc-unit-(\d+)-\d+-vcc-\d+-\d+")


def main(args=None, **kwargs):  # noqa: E302
    unit_num = get_unit_num_from_hostname()
    job_name = f"{JOB_NAME_PREFIX}-{unit_num}"
    # Call the kubectl command and wait until the bitstreams have been successfully downloaded
    wait_for_job_completion(job_name)

    return run(
        classes=(VCCAllBandsController,),
        args=args,
        **kwargs,
    )


def get_unit_num_from_hostname() -> str:
    hostname = os.environ.get("HOSTNAME", "")
    match = HOST_NAME_PATTERN.match(hostname)
    if not match:
        raise RuntimeError(
            f"Could not determine unitNum from pod's env var HOSTNAME: '{hostname}'. "
            f"The expected format is 'fhs-vcc-unit-<unitNum>-<instance>-vcc-<num>-<ordinal>'"
        )
    return match.group(1)


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
