# -*- coding: utf-8 -*-
#
# This file is part of the SKA Mid.CBF MCS project
#
# Ported from ska-mid-cbf-mcs project which in turn was ported from the SKA Low MCCS project:
# https://gitlab.com/ska-telescope/ska-low-mccs/-/blob/main/src/ska_low_mccs/testing/mock/mock_callable.py
#
# Distributed under the terms of the GPL license.
# See LICENSE for more info.

"""This module implements infrastructure for mocking callbacks and other callables."""
from __future__ import annotations  # allow forward references in type hints

import queue
import unittest.mock
from typing import Any, Optional, Sequence, Tuple

import tango

__all__ = ["MockCallable", "MockChangeEventCallback"]


class MockCallable:
    """
    This class implements a mock callable.

    It is useful for when you want to assert that a callable is called,
    but the callback is called asynchronously, so that you might have to
    wait a short time for the call to occur.

    If you use a regular mock for the callback, your tests will end up
    littered with sleeps:

    .. code-block:: python

        antenna_apiu_proxy.start_communicating()
        communication_status_changed_callback.assert_called_once_with(
            CommunicationStatus.NOT_ESTABLISHED
        )
        time.sleep(0.1)
        communication_status_changed_callback.assert_called_once_with(
            CommunicationStatus.ESTABLISHED
        )

    These sleeps waste time, slow down the tests, and they are difficult
    to tune: maybe you only need to sleep 0.1 seconds on your
    development machine, but what if the CI pipeline deploys the tests
    to an environment that needs 0.2 seconds for this?

    This class solves that by putting each call to the callback onto a
    queue. Then, each time we assert that a callback was called, we get
    a call from the queue, waiting if necessary for the call to arrive,
    but with a timeout:

    .. code-block:: python

        antenna_apiu_proxy.start_communicating()
        communication_status_changed_callback.assert_next_call(
            CommunicationStatus.NOT_ESTABLISHED
        )
        communication_status_changed_callback.assert_next_call(
            CommunicationStatus.ESTABLISHED
        )
    """

    def __init__(
        self: MockCallable,
        return_value: Any = None,
        called_timeout: float = 5.0,
        not_called_timeout: float = 1.0,
    ):
        """
        Initialise a new instance.

        :param return_value: what to return when called
        :param called_timeout: how long to wait for a call to occur when
            we are expecting one. It makes sense to wait a long time for
            the expected call, as it will generally arrive much much
            sooner anyhow, and failure for the call to arrive in time
            will cause the assertion to fail. The default is 5 seconds.
        :param not_called_timeout: how long to wait for a callback when
            we are *not* expecting one. Since we need to wait the full
            timeout period in order to determine that a callback has not
            arrived, asserting that a call has not been made can
            severely slow down your tests. By keeping this timeout quite
            short, we can speed up our tests, at the risk of prematurely
            passing an assertion. The default is 0.5
        """
        self._return_value: Any = return_value
        self._called_timeout = called_timeout
        self._not_called_timeout = not_called_timeout
        self._queue: queue.Queue = queue.Queue()

    def __call__(self: MockCallable, *args: Any, **kwargs: Any) -> Any:
        """
        Handle a callback call.

        Create a standard mock, call it, and put it on the queue. (This
        approach lets us take advantange of the mock's assertion
        functionality later.)

        :param args: positional args in the call
        :param kwargs: keyword args in the call

        :return: the object's return calue
        """
        called_mock = unittest.mock.Mock()
        called_mock(*args, **kwargs)
        self._queue.put(called_mock)
        return self._return_value

    def assert_not_called(
        self: MockCallable, timeout: Optional[float] = None
    ) -> None:
        """
        Assert that the callback still has not been called after the timeout period.

        This is a slow method because it has to wait the full timeout
        period in order to determine that the call is not coming. An
        optional timeout parameter is provided for the situation where
        you are happy for the assertion to pass after a shorter wait
        time.

        :param timeout: optional timeout for the check. If not provided, the
            default is the class setting
        """
        timeout = self._not_called_timeout if timeout is None else timeout
        try:
            called_mock = self._queue.get(timeout=timeout)
        except queue.Empty:
            return
        called_mock.assert_not_called()  # we know this will fail and raise an exception

    def assert_next_call(
        self: MockCallable, *args: Any, **kwargs: Any
    ) -> None:
        """
        Assert the arguments of the next call to this mock callback.

        If the call has not been made, this method will wait up to the
        specified timeout for a call to arrive.

        :param args: positional args that the call is asserted to have
        :param kwargs: keyword args that the call is asserted to have

        :raises AssertionError: if the callback has not been called.
        """
        try:
            called_mock = self._queue.get(timeout=self._called_timeout)
        except queue.Empty:
            raise AssertionError("Callback has not been called.")
        called_mock.assert_called_once_with(*args, **kwargs)

    def get_next_call(
        self: MockCallable,
    ) -> Tuple[Sequence[Any], Sequence[Any]]:
        """
        Return the arguments of the next call to this mock callback.

        This is useful for situations where you do not know exactly what
        the arguments of the next call will be, so you cannot use the
        :py:meth:`.assert_next_call` method. Instead you want to assert
        some specific properties on the arguments:

        .. code-block:: python

            (args, kwargs) = mock_callback.get_next_call()
            event_data = args[0].attr_value
            assert event_data.name == "healthState"
            assert event_data.value == HealthState.UNKNOWN
            assert event_data.quality == tango.AttrQuality.ATTR_VALID

        If the call has not been made, this method will wait up to the
        specified timeout for a call to arrive.

        :raises AssertionError: if the callback has not been called
        :return: an (args, kwargs) tuple
        """
        try:
            called_mock = self._queue.get(timeout=self._called_timeout)
        except queue.Empty:
            raise AssertionError("Callback has not been called.")
        return called_mock.call_args

    def assert_last_call(
        self: MockCallable, *args: Any, **kwargs: Any
    ) -> None:
        """
        Assert the arguments of the last call to this mock callback.

        The "last" call is the last call before an attempt to get the
        next event times out.

        This is useful for situations where we know a device may call a
        callback several time, and we don't care too much about the
        exact order of calls, but we do know what the final call should
        be.

        :param args: positional args that the call is asserted to have
        :param kwargs: keyword args that the call is asserted to have

        :raises AssertionError: if the callback has not been called.
        """
        called_mock = None
        while True:
            try:
                called_mock = self._queue.get(timeout=self._not_called_timeout)
            except queue.Empty:
                break
        if called_mock is None:
            raise AssertionError("Callback has not been called.")

        called_mock.assert_called_once_with(*args, **kwargs)


class MockChangeEventCallback(MockCallable):
    """
    This class implements a mock change event callback.

    It is a special case of a :py:class:`MockCallable` where the
    callable expects to be called with event_name, event_value and
    event_quality arguments (which is how
    :py:class:`ska_mid_cbf_mcs.device_proxy.CbfDeviceProxy` calls its change event
    callbacks).
    """

    def __init__(
        self: MockChangeEventCallback,
        event_name: str,
        called_timeout: float = 5.0,
        not_called_timeout: float = 0.5,
    ):
        """
        Initialise a new instance.

        :param event_name: the name of the event for which this callable
            is a callback
        :param called_timeout: how long to wait for a call to occur when
            we are expecting one. It makes sense to wait a long time for
            the expected call, as it will generally arrive much much
            sooner anyhow, and failure for the call to arrive in time
            will cause the assertion to fail. The default is 5 seconds.
        :param not_called_timeout: how long to wait for a callback when
            we are *not* expecting one. Since we need to wait the full
            timeout period in order to determine that a callback has not
            arrived, asserting that a call has not been made can
            severely slow down your tests. By keeping this timeout quite
            short, we can speed up our tests, at the risk of prematurely
            passing an assertion. The default is 0.5
        """
        self._event_name = event_name.lower()
        super().__init__(None, called_timeout, not_called_timeout)

    def assert_next_change_event(
        self: MockChangeEventCallback,
        value: Any,
        quality: tango.AttrQuality = tango.AttrQuality.ATTR_VALID,
    ) -> None:
        """
        Assert the arguments of the next call to this mock callback.

        If the call has not been made, this method will wait up to the
        specified timeout for a call to arrive.

        :param value: the asserted value of the change event
        :param quality: the asserted quality of the change event. This
            is optional, with a default of ATTR_VALID.

        :raises AssertionError: if the callback has not been called.
        """
        (args, kwargs) = self.get_next_call()
        (call_name, call_value, call_quality) = args
        assert (
            call_name.lower() == self._event_name
        ), f"Event name '{call_name.lower()}'' does not match expected name '{self._event_name}'"
        assert (
            call_value == value
        ), f"Call value {call_value} does not match expected value {value}"
        assert (
            call_quality == quality
        ), f"Call quality {call_quality} does not match expected quality {quality}"

    def assert_last_change_event(
        self: MockChangeEventCallback,
        value: Any,
        quality: tango.AttrQuality = tango.AttrQuality.ATTR_VALID,
    ) -> None:
        """
        Assert the arguments of the last call to this mock callback.

        The "last" call is the last call before an attempt to get the
        next event times out.

        This is useful for situations where we know a device may fire
        several events, and we don't know or care about the exact order
        of events, but we do know what the final event should be. For
        example, when we tell CbfController to turn on, it has to turn
        many devices on, which have to turn many devices on, etc. With
        so m

        :param value: the asserted value of the change event
        :param quality: the asserted quality of the change event. This
            is optional, with a default of ATTR_VALID.

        :raises AssertionError: if the callback has not been called.
        """
        called_mock = None
        failure_message = "Callback has not been called"

        while True:
            timeout = (
                self._called_timeout
                if called_mock is None
                else self._not_called_timeout
            )
            try:
                called_mock = self._queue.get(timeout=timeout)
            except queue.Empty:
                break

            (args, kwargs) = called_mock.call_args
            (call_name, call_value, call_quality) = args

            if call_name.lower() != self._event_name:
                failure_message = (
                    f"Event name '{call_name.lower()}' does not match expected name "
                    f"'{self._event_name}'"
                )
                called_mock = None
                continue

            if call_value != value:
                failure_message = f"Call value {call_value} does not match expected value {value}"
                called_mock = None
                continue

            if call_quality != quality:
                failure_message = (
                    f"Call quality {call_quality} does not match expected quality "
                    f"{quality}"
                )
                called_mock = None
                continue

        if called_mock is None:
            raise AssertionError(failure_message)