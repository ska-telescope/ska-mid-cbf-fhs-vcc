# -*- coding: utf-8 -*-
#
# This file is part of the ska-mid-cbf-fhs-sim project
#
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.
#
# Copyright (c) 2025 National Research Council of Canada
"""Contain the tests for the Vcc."""

from __future__ import annotations

import gc
import json
import os
from typing import Any

import pytest
from assertpy import assert_that
from ska_control_model import AdminMode, ObsState, ResultCode
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

from ska_mid_cbf_fhs_common.testing.configurable_test_context import ConfigurableThreadedTestTangoContextManager

# Path
test_data_path = os.path.dirname(os.path.abspath(__file__)) + "/../../data/"

# Disable garbage collection to prevent tests hanging
gc.disable()

FREQ_BAND_DICT = {"1": 0, "2": 1, "3": 2, "4": 3, "5a": 4, "5b": 5}

@pytest.mark.forked
class TestVCCAllBandsSim:
    """Test class for VCCAllBandsSim."""

    @pytest.fixture(name="test_context", scope="module")
    def init_test_context(self):
        """
        Fixture to set up the VCC All Bands device for testing with a mock Tango database.
        """
        harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)

        harness.add_device(
            device_name="test/vccallbands/1",
            device_class=VCCAllBandsController,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1", # set to 1 to test simulated behaviour
            emulation_mode="1",
            ethernet_200g_fqdn="test/ethernet200g/1",
            packet_validation_fqdn="test/packet_validation/1",
            vcc123_channelizer_fqdn="test/vcc123/1",
            vcc45_channelizer_fqdn="vcc45",
            wideband_input_buffer_fqdn="test/wib/1",
            wideband_frequency_shifter_fqdn="test/wfs/1",
            circuit_switch_fqdn="cs",
            fs_selection_fqdn="test/fss/1",
            b123_wideband_power_meter_fqdn="test/b123wpm/1",
            b45a_wideband_power_meter_fqdn="test/b45awpm/1",
            b5b_wideband_power_meter_fqdn="test/b5bwpm/1",
            fs_wideband_power_meter_fqdn="test/fs<multiplicity>wpm/1",
            vcc_stream_merge_fqdn="test/vcc-stream-merge<multiplicity>/1",
        )

        with harness as test_context:
            yield test_context

    def device_online_and_on(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        vcc_all_bands_event_tracer: TangoEventTracer,
        event_timeout: int,
    ) -> bool:
        """
        Helper function that starts up and turns on the DUT.

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        """
        # Set a given device to AdminMode.ONLINE and DevState.ON
        vcc_all_bands_device.adminMode = AdminMode.ONLINE

        assert_that(vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
        )

        assert_that(vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=vcc_all_bands_device,
            attribute_name="state",
            attribute_value=DevState.ON,
        )

        return vcc_all_bands_device.adminMode == AdminMode.ONLINE

    def test_State(self: TestVCCAllBandsSim, vcc_all_bands_device: Any) -> None:
        """
        Test the State attribute just after device initialization.

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        """
        assert vcc_all_bands_device.state() == DevState.ON

    def test_Status(self: TestVCCAllBandsSim, vcc_all_bands_device: Any) -> None:
        """
        Test the Status attribute just after device initialization.

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        """
        assert vcc_all_bands_device.Status() == "ON"

    def test_adminMode(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
    ) -> None:
        """
        Test the adminMode attribute just after device initialization.

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        """
        assert vcc_all_bands_device.adminMode == AdminMode.OFFLINE

    @pytest.mark.parametrize(
        "attribute_name, \
        attribute_value_type",  # |command_param_type [1: str], [2: int], [3: empty arr]|
        [
            ("expectedDishId", 1),
            ("requestedRFIHeadroom", 3),
            ("vccGains", 3),
            ("frequencyBand", 2),
            ("inputSampleRate", 2),
            ("frequencyBandOffset", 3),
            ("subarrayID", 2),
        ],
    )
    def test_read_attributes(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        attribute_name: str,
        attribute_value_type: int,
    ) -> None:
        """
        Test uploading delay model

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        """
        # Set values
        attribute_value = ""
        match attribute_value_type:
            case 1:
                attribute_value = ""
            case 2:
                attribute_value = 0
            case 3:
                attribute_value = [0]

        # Test read values
        assert getattr(vcc_all_bands_device, attribute_name) == attribute_value

    @pytest.mark.parametrize(
        "attribute_name, \
        attribute_value_type",  # |command_param_type [1: str], [2: int], [3: empty arr]|
        [
            ("expectedDishId", 1),
            ("requestedRFIHeadroom", 3),
            ("vccGains", 3),
            # ("frequencyBand", 4), # TODO fix, refactor whole test
            ("inputSampleRate", 2),
            ("frequencyBandOffset", 3),
            ("subarrayID", 2),
        ],
    )
    def test_attribute_overrides(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        attribute_name: str,
        attribute_value_type: int,
    ) -> None:
        """Test overriding attributes"""
        # Set values
        attribute_new_value = "test"
        match attribute_value_type:
            case 1:
                attribute_new_value = "test"
            case 2:
                attribute_new_value = 1
            case 3:
                attribute_new_value = [1]
            case 4:
                attribute_new_value = "_2"

        vcc_all_bands_device.simOverrides = json.dumps(
            {
                "attributes": {
                    attribute_name: attribute_new_value,
                }
            }
        )

        # Check value change
        assert (
            getattr(vcc_all_bands_device, attribute_name) == attribute_new_value
        )

    def test_ConfigureScan_override_fail(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        vcc_all_bands_event_tracer: TangoEventTracer,
        event_timeout: int,
    ) -> None:
        """
        Test overriding ConfigureScan command to fail, then resetting to default
        behaviour.

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        :param vcc_all_bands_event_tracer: A TangoEventTracer used to recieve subscribed change
                             events from the device under test.
        """
        # Store original override values to reset later
        original_overrides = vcc_all_bands_device.simOverrides

        # Set vcc_all_bands_device ONLINE
        vcc_all_bands_device.adminMode = AdminMode.ONLINE

        # Check event
        assert_that(vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        # vcc_all_bands_device pushes attribute events if value changes
        old_sub_id = vcc_all_bands_device.subarrayID
        new_sub_id = old_sub_id + 1
        vcc_all_bands_device.simOverrides = json.dumps(
            {
                "attributes": {
                    "subarrayID": new_sub_id,
                }
            }
        )

        # Defaults to successful commands
        [[result_code], [configure_scan_command_id]] = (
            vcc_all_bands_device.ConfigureScan("test")
        )
        assert result_code == ResultCode.QUEUED
        [[result_code], [go_to_idle_command_id]] = vcc_all_bands_device.GoToIdle()
        assert result_code == ResultCode.QUEUED
        expected_events = [
            ("obsState", ObsState.CONFIGURING, ObsState.IDLE, 1),
            ("obsState", ObsState.READY, ObsState.CONFIGURING, 1),
            (
                "longRunningCommandResult",
                (
                    f"{configure_scan_command_id}",
                    f'[{ResultCode.OK.value}, "ConfigureScan completed OK"]',
                ),
                None,
                1,
            ),
            ("obsState", ObsState.CONFIGURING, ObsState.READY, 1),
            ("obsState", ObsState.IDLE, ObsState.CONFIGURING, 1),
            (
                "longRunningCommandResult",
                (
                    f"{go_to_idle_command_id}",
                    f'[{ResultCode.OK.value}, "GoToIdle completed OK"]',
                ),
                None,
                1,
            ),
        ]

        # Check events
        for name, value, previous, n in expected_events:
            assert_that(vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

        # Override ConfigureScan command to fail
        vcc_all_bands_device.simOverrides = json.dumps(
            {
                "commands": {
                    "ConfigureScan": {
                        "result_code": "FAILED",
                        "message": "ConfigureScan failed",
                        "invoked_action": "CONFIGURE_INVOKED",
                        "completed_action": "GO_TO_IDLE",
                    },
                }
            }
        )
        [[result_code], [configure_scan_command_id]] = (
            vcc_all_bands_device.ConfigureScan("test")
        )
        assert result_code == ResultCode.QUEUED
        expected_events = [
            ("obsState", ObsState.CONFIGURING, ObsState.IDLE, 2),
            ("obsState", ObsState.IDLE, ObsState.CONFIGURING, 1),
            (
                "longRunningCommandResult",
                (
                    f"{configure_scan_command_id}",
                    f'[{ResultCode.FAILED.value}, "ConfigureScan failed"]',
                ),
                None,
                1,
            ),
        ]

        # Check events
        for name, value, previous, n in expected_events:
            assert_that(vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

        # Reset overrides
        vcc_all_bands_device.simOverrides = original_overrides
        [[result_code], [configure_scan_command_id]] = (
            vcc_all_bands_device.ConfigureScan("test")
        )
        assert result_code == ResultCode.QUEUED
        [[result_code], [go_to_idle_command_id]] = vcc_all_bands_device.GoToIdle()
        assert result_code == ResultCode.QUEUED
        expected_events = [
            ("obsState", ObsState.CONFIGURING, ObsState.IDLE, 3),
            ("obsState", ObsState.READY, ObsState.CONFIGURING, 2),
            (
                "longRunningCommandResult",
                (
                    f"{configure_scan_command_id}",
                    f'[{ResultCode.OK.value}, "ConfigureScan completed OK"]',
                ),
                None,
                1,
            ),
            ("obsState", ObsState.CONFIGURING, ObsState.READY, 2),
            ("obsState", ObsState.IDLE, ObsState.CONFIGURING, 2),
            (
                "longRunningCommandResult",
                (
                    f"{go_to_idle_command_id}",
                    f'[{ResultCode.OK.value}, "GoToIdle completed OK"]',
                ),
                None,
                1,
            ),
        ]

        # Check events
        for name, value, previous, n in expected_events:
            assert_that(vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

        # Set vcc_all_bands_device OFFLINE
        vcc_all_bands_device.adminMode = AdminMode.OFFLINE

        expected_events = [
            ("adminMode", AdminMode.OFFLINE, AdminMode.ONLINE, 1),
        ]

        # Check events
        for name, value, previous, n in expected_events:
            assert_that(vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

    def test_scan(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        vcc_all_bands_event_tracer: TangoEventTracer,
        event_timeout: int,
    ) -> None:
        """
        Test Scan command

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        :param vcc_all_bands_event_tracer: A TangoEventTracer used to recieve subscribed change
                             events from the device under test.
        """
        # Set vcc_all_bands_device ONLINE
        vcc_all_bands_device.adminMode = AdminMode.ONLINE
        
        # Check event
        assert_that(vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        # Set to READY obsState
        vcc_all_bands_device.ConfigureScan("")

        # Run Scan Test

        [[result_code], [scan_command_id]] = vcc_all_bands_device.Scan(0)
        assert result_code == ResultCode.QUEUED
        expected_events = [
            ("obsState", ObsState.SCANNING, ObsState.READY, 1),
            (
                "longRunningCommandResult",
                (
                    f"{scan_command_id}",
                    f'[{ResultCode.OK.value}, "Scan completed OK"]',
                ),
                None,
                1,
            ),
        ]

        # Assert Scan events have been completed
        for name, value, previous, n in expected_events:
            assert_that(vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

    @pytest.mark.parametrize(
        "not_allowed_obs_modes, \
        command_name, \
        command_param_type",  # |allowed_obs_modes IDLE, READY, SCANNING|,|command_param_type 1: str, 2: int, 3: empty arr|
        [
            (["READY", "SCANNING"], "UpdateSubarrayMembership", 2),
            (["IDLE", "READY"], "AutoSetFilterGains", 3),
        ],
    )
    def test_not_allowed(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        vcc_all_bands_event_tracer: TangoEventTracer,
        not_allowed_obs_modes: [str],
        command_name: str,
        command_param_type: int,
        event_timeout: int,
    ) -> None:
        """
        Test commands failing in incorrect state parametrized

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        :param vcc_all_bands_event_tracer: A TangoEventTracer used to recieve subscribed change
                            events from the device under test.
        """
        # Get command parameter
        command_param = ""
        match command_param_type:
            case 1:
                command_param = "test"
            case 2:
                command_param = 0
            case 3:
                command_param = []

        [[result_code], [command_id]] = vcc_all_bands_device.command_inout(
            command_name, command_param
        )
        # Test command not allowed in Offline Admin mode state
        assert_that(vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=vcc_all_bands_device,
            attribute_name="longRunningCommandResult",
            attribute_value=(
                f"{command_id}",
                f'[{ResultCode.NOT_ALLOWED.value}, "Command is not allowed"]',
            ),
        )
        for current_state in not_allowed_obs_modes:
            # Set state
            if current_state == "READY":
                vcc_all_bands_device.ConfigureScan("test")
            elif current_state == "SCANNING":
                vcc_all_bands_device.Scan(0)

            # Test command Not Allowed in State current_state
            [[result_code], [command_id]] = vcc_all_bands_device.command_inout(
                command_name, command_param
            )

            assert_that(vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
                attribute_name="longRunningCommandResult",
                attribute_value=(
                    f"{command_id}",
                    f'[{ResultCode.NOT_ALLOWED.value}, "Command is not allowed"]',
                ),
            )

    @pytest.mark.parametrize(
        "allowed_obs_modes, \
        command_name, \
        command_param_type",  # |allowed_obs_modes IDLE, READY, SCANNING|,|command_param_type [1: str], [2: int], [3: empty arr]|
        [
            (["SCANNING"], "AutoSetFilterGains", 3),
            (["IDLE"], "UpdateSubarrayMembership", 2),
        ],
    )
    def test_commands(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        vcc_all_bands_event_tracer: TangoEventTracer,
        allowed_obs_modes: [str],
        command_name: str,
        command_param_type: int,
        event_timeout: int,
    ) -> None:
        """
        Test all commands which do not require attribute change

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        :param vcc_all_bands_event_tracer: A TangoEventTracer used to recieve subscribed change
                            events from the device under test.
        """
        # Get command parameter
        command_param = ""
        match command_param_type:
            case 1:
                command_param = "test"
            case 2:
                command_param = 0
            case 3:
                command_param = []

        [[result_code], [command_id]] = vcc_all_bands_device.command_inout(
            command_name, command_param
        )
        # Set vcc_all_bands_device ONLINE
        vcc_all_bands_device.adminMode = AdminMode.ONLINE

        # Check event
        assert_that(vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        for current_state in allowed_obs_modes:
            # Set state
            if current_state == "READY":
                vcc_all_bands_device.ConfigureScan("test")
            elif current_state == "SCANNING":
                vcc_all_bands_device.ConfigureScan("test")
                vcc_all_bands_device.Scan(0)

            # Test command in current_state
            [[result_code], [command_id]] = vcc_all_bands_device.command_inout(
                command_name, command_param
            )

            assert result_code == ResultCode.QUEUED
            expected_events = [
                (
                    "longRunningCommandResult",
                    (
                        f"{command_id}",
                        f'[{ResultCode.OK.value}, "{command_name} completed OK"]',
                    ),
                    None,
                    1,
                ),
            ]

            # Assert command events have been completed
            for name, value, previous, n in expected_events:
                assert_that(vcc_all_bands_event_tracer).within_timeout(
                    event_timeout
                ).has_change_event_occurred(
                    device_name=vcc_all_bands_device,
                    attribute_name=name,
                    attribute_value=value,
                    previous_value=previous,
                    min_n_events=n,
                )
            # Reset state
            if current_state == "SCANNING":
                vcc_all_bands_device.EndScan()
            if current_state != "IDLE":
                vcc_all_bands_device.GoToIdle()

    @pytest.mark.parametrize(
        "allowed_obs_modes, \
        command_name, \
        command_param_type",  # |allowed_obs_modes IDLE, READY, SCANNING|,|command_param_type 1: str, 2: int, 3: empty arr|
        [
            (["IDLE"], "UpdateSubarrayMembership", 2),
            (["SCANNING"], "AutoSetFilterGains", 3),
        ],
    )
    def test_override_command_fail(
        self: TestVCCAllBandsSim,
        vcc_all_bands_device: Any,
        vcc_all_bands_event_tracer: TangoEventTracer,
        allowed_obs_modes: [str],
        command_name: str,
        command_param_type: int,
        event_timeout: int,
    ) -> None:
        """
        Test overriding command to fail

        :param vcc_all_bands_device: DeviceProxy to the device under test.
        :param vcc_all_bands_event_tracer: A TangoEventTracer used to recieve subscribed change
                             events from the device under test.
        """
        # Get command parameter
        command_param = ""
        match command_param_type:
            case 1:
                command_param = "test"
            case 2:
                command_param = 0
            case 3:
                command_param = []

        # Set vcc_all_bands_device ONLINE
        vcc_all_bands_device.adminMode = AdminMode.ONLINE

        # Check event
        assert_that(vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        # Override command to fail
        vcc_all_bands_device.simOverrides = json.dumps(
            {
                "commands": {
                    f"{command_name}": {
                        "result_code": "FAILED",
                        "message": f"{command_name} failed",
                    },
                }
            }
        )
        for current_state in allowed_obs_modes:
            # Set state
            if current_state == "READY":
                vcc_all_bands_device.ConfigureScan("test")
            elif current_state == "SCANNING":
                vcc_all_bands_device.ConfigureScan("test")
                vcc_all_bands_device.Scan(0)
            [[result_code], [command_id]] = vcc_all_bands_device.command_inout(
                command_name, command_param
            )
            assert result_code == ResultCode.QUEUED
            expected_events = [
                (
                    "longRunningCommandResult",
                    (
                        f"{command_id}",
                        f'[{ResultCode.FAILED.value}, "{command_name} failed"]',
                    ),
                    None,
                    1,
                ),
            ]

            # Check events
            for name, value, previous, n in expected_events:
                assert_that(vcc_all_bands_event_tracer).within_timeout(
                    event_timeout
                ).has_change_event_occurred(
                    device_name=vcc_all_bands_device,
                    attribute_name=name,
                    attribute_value=value,
                    previous_value=previous,
                    min_n_events=n,
                )
            # Reset state
            if current_state == "SCANNING":
                vcc_all_bands_device.EndScan()
            if current_state != "IDLE":
                vcc_all_bands_device.GoToIdle()
