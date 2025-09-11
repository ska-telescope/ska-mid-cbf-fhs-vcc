"""This module contains pytest-specific test harness for FHS-VCC VCC All Bands Controller unit tests."""

from __future__ import annotations

from typing import Generator

import pytest
from ska_control_model import AdminMode, HealthState, ObsState
from ska_tango_testing.harness import TangoTestHarnessContext
from ska_tango_testing.integration import TangoEventTracer

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

@pytest.fixture(scope="session")  # Use "session" scope for true constants
def event_timeout() -> int:
    """Event tracer timeout."""
    return 10

@pytest.fixture(name="vcc_all_bands_device")
def vcc_all_bands_device_fixture(
    test_context: TangoTestHarnessContext,
) -> VCCAllBandsController:
    """Fixture that returns the device under test.

    Args:
        test_context (:obj:`TangoTestHarnessContext`): The context in which the tests run.

    Returns:
        :obj:`DeviceProxy`: A proxy to the device under test.
    """
    return test_context.get_device("test/vccallbands/1")

@pytest.fixture(name="vcc_all_bands_event_tracer", autouse=True)
def vcc_all_bands_tango_event_tracer(
    vcc_all_bands_device,
) -> Generator[TangoEventTracer, None, None]:
    """Fixture that returns a TangoEventTracer for pertinent devices.
    Takes as parameter all required device proxy fixtures for this test module.

    Args:
        device_under_test (:obj:`DeviceProxy`): Proxy to the device under test.

    Returns:
        :obj:`TangoEventTracer`: An event tracer for the device under test.
    """
    tracer = TangoEventTracer(
        event_enum_mapping={
            "adminMode": AdminMode,
            "obsState": ObsState,
            "healthState": HealthState,
        }
    )

    change_event_attr_list = [
        "longRunningCommandResult",
        "adminMode",
        "state",
        "obsState",
        "healthState"
    ]
    for attr in change_event_attr_list:
        tracer.subscribe_event(vcc_all_bands_device, attr)

    yield tracer

    tracer.unsubscribe_all()
    tracer.clear_events()
