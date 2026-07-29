# -*- coding: utf-8 -*-
#
# This file is part of the ska-mid-cbf-mcs project
#
# Distributed under the terms of the BSD 3-Clause license.
# See LICENSE for more info.

"""Release information for SKA Mid.CBF fhs-vcc Python Package."""

def get_release() -> str:
    with open("../.release", "r") as release_file:
        for line in release_file:
            if line.startswith("release="):
                return line.strip().split("=")[1]

    return "unknown"

NAME = "ska_mid_cbf_fhs_vcc"
VERSION = get_release()
VERSION_INFO = VERSION.split(".")
DESCRIPTION = "Mid.CBF VCC Software."
URL = "https://gitlab.com/ska-telescope/ska-mid-cbf/monitor-control/ska-mid-cbf-terabox-mgmt"
LICENSE = "BSD-3-Clause"  # noqa: A001
COPYRIGHT = ""  # noqa: A001

