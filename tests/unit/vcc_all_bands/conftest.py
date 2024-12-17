from __future__ import annotations

from typing import Generator

import pytest
from ska_tango_testing.harness import TangoTestHarnessContext
from ska_tango_testing.integration import TangoEventTracer


@pytest.fixture(name="vcc_all_bands_device")
def vcc_all_bands_device_fixture(
    test_context: TangoTestHarnessContext,
):
    """
    Fixture that returns the device under test.

    :param test_context: the context in which the tests run
    :return: the DeviceProxy to device under test
    """
    return test_context.get_device("test/vccallbands/1")


@pytest.fixture(name="wib_device")
def wib_device_fixture(
    test_context: TangoTestHarnessContext,
):
    """
    Fixture that returns the device under test.

    :param test_context: the context in which the tests run
    :return: the DeviceProxy to device under test
    """
    return test_context.get_device("test/wib/1")


@pytest.fixture(name="wib_event_tracer", autouse=True)
def wib_tango_event_tracer(
    wib_device,
) -> Generator[TangoEventTracer, None, None]:
    """
    Fixture that returns a TangoEventTracer for pertinent devices.
    Takes as parameter all required device proxy fixtures for this test module.

    :param device_under_test: the DeviceProxy to device under test
    :return: TangoEventTracer
    """
    tracer = TangoEventTracer()

    change_event_attr_list = ["longRunningCommandResult", "obsState", "adminMode", "state", "healthState"]
    for attr in change_event_attr_list:
        tracer.subscribe_event(wib_device, attr)

    return tracer
