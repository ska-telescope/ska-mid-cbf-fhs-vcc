# -*- coding: utf-8 -*-
#
# This file is part of the SKA Mid.CBF FHS-VCC project
#
# Repurposed from the ska-mid-cbf-mcs project
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.

"""This module contains pytest-specific test harness for FHS-VCC unit tests."""

from __future__ import annotations

from typing import Generator

import pytest
from tango import GreenMode, asyncio_executor
from ska_tango_testing.harness import TangoTestHarnessContext
from ska_tango_testing.integration import TangoEventTracer

EVENT_TIMEOUT = 30


@pytest.fixture()
def event_loop():
    yield asyncio_executor.get_global_executor().loop


@pytest.fixture(name="device_under_test")
def device_under_test_fixture(
    test_context: TangoTestHarnessContext,
):
    """
    Fixture that returns the device under test.

    :param test_context: the context in which the tests run
    :return: the DeviceProxy to device under test
    """
    # print("DUT Event loop is " + str(asyncio.get_running_loop()._thread_id))
    # asyncio_executor.get_global_executor().loop = asyncio.get_running_loop()
    # dev = await get_device_proxy("test/vcc123/1", green_mode=GreenMode.Asyncio, wait=False)
    dev = test_context.get_device("test/vcc123/1")
    dev.set_green_mode(GreenMode.Asyncio)  # for some reason it does not get set by the device class
    return dev


@pytest.fixture(name="event_tracer", autouse=True)
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
        "obsState",
        "adminMode",
        "state",
    ]
    for attr in change_event_attr_list:
        tracer.subscribe_event(device_under_test, attr)

    return tracer
