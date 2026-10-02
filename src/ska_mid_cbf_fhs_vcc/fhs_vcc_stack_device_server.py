import subprocess
import os
import sys
import time
from pathlib import Path

from tango.server import run

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

__all__ = ["main"]


def main(args=None, **kwargs):  # noqa: E302
    # Wait for the download path size to stop increasing
    #bitstream_mount_path = os.getenv("BITSTREAM_MOUNT_PATH")
    bitstream_mount_path = "/app/mnt/bitstream"
    print(bitstream_mount_path)
    wait_for_download_completion(bitstream_mount_path)

    return run(
        classes=(VCCAllBandsController,),
        args=args,
        **kwargs,
    )

def dir_size(root: Path) -> int:
    """Return total size (in bytes) of all regular files under *root*."""
    total = 0
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            try:
                fp = Path(dirpath) / name
                total += fp.stat().st_size
            except (FileNotFoundError, PermissionError):
                # File vanished or we can't read it – ignore it for this pass
                continue
    return total

def wait_for_download_completion(folder: Path, interval: float = 5.0) -> bool:
    print(str(folder))
    if not folder.is_dir():
        sys.exit(f"Error: {folder} is not a directory")

    prev = dir_size(folder)
    print(f"Starting size of '{folder}': {prev}")

    while True:
        time.sleep(interval)
        cur = dir_size(folder)

        if cur == prev:
            print(f"Size unchanged after {interval}s → stopping.")
            break

        prev = cur


if __name__ == "__main__":  # noqa: #E305
    main()
