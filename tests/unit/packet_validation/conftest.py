"""This module contains pytest-specific test harness for FHS-VCC Packet Validation unit tests."""

from __future__ import annotations

from typing import Generator

import pytest
from ska_tango_testing.harness import TangoTestHarnessContext
from ska_tango_testing.integration import TangoEventTracer

EVENT_TIMEOUT = 30


@pytest.fixture(name="device_under_test", scope="module")
def device_under_test_fixture(
    test_context: TangoTestHarnessContext,
):
    """
    Fixture that returns the device under test.

    :param test_context: the context in which the tests run
    :return: the DeviceProxy to device under test
    """
    return test_context.get_device("test/packet_validation/1")


@pytest.fixture(name="event_tracer", scope="module", autouse=True)
def tango_event_tracer(
    device_under_test,
) -> Generator[TangoEventTracer, None, None]:
    """
    Fixture that returns a TangoEventTracer for pertinent devices.
    Takes as parameter all required device proxy fixtures for this test module.

    :param device_under_test: the DeviceProxy to device under test
    :return: TangoEventTracer
    """
    tracer = TangoEventTracer()

    change_event_attr_list = [
        "longRunningCommandResult",
        "adminMode",
        "state",
    ]
    for attr in change_event_attr_list:
        tracer.subscribe_event(device_under_test, attr)

    return tracer
