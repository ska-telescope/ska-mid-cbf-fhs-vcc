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
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_sim import SimVCCAllBandsController, VCC_SIM_DEFAULT_ATTRIBUTE_VALUES
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

from ska_mid_cbf_fhs_common.testing.configurable_test_context import ConfigurableThreadedTestTangoContextManager

# Path
test_data_path = os.path.dirname(os.path.abspath(__file__)) + "/../../data/"

# Disable garbage collection to prevent tests hanging
gc.disable()


@pytest.mark.forked
class TestVCCAllBandsSim:
    """Test class for VCCAllBandsSim."""

    @pytest.fixture(name="test_context", scope="module")
    def init_test_context(self):
        """Fixture to set up the VCC All Bands device for testing with a mock Tango database."""
        harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)

        harness.add_device(
            device_name="test/vccallbands/1",
            device_class=SimVCCAllBandsController,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
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
        sim_vcc_all_bands_device: Any,
        sim_vcc_all_bands_event_tracer: TangoEventTracer,
        event_timeout: int,
    ) -> bool:
        """Helper function that starts up and turns on the DUT.

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
            sim_vcc_all_bands_event_tracer (:obj:`TangoEventTracer`): Event tracer for the device under test.

        Returns:
            :obj:`bool`: True if AdminMode was successfuly set ONLINE, False otherwise.
        """
        # Set a given device to AdminMode.ONLINE and DevState.ON
        sim_vcc_all_bands_device.adminMode = AdminMode.ONLINE

        assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=sim_vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
        )

        assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=sim_vcc_all_bands_device,
            attribute_name="state",
            attribute_value=DevState.ON,
        )

        return sim_vcc_all_bands_device.adminMode == AdminMode.ONLINE

    def test_State(self: TestVCCAllBandsSim, sim_vcc_all_bands_device: Any) -> None:
        """Test the State attribute just after device initialization.

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
        """
        assert sim_vcc_all_bands_device.state() == DevState.ON

    def test_Status(self: TestVCCAllBandsSim, sim_vcc_all_bands_device: Any) -> None:
        """Test the Status attribute just after device initialization.

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
        """
        assert sim_vcc_all_bands_device.Status() == "ON"

    def test_adminMode(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
    ) -> None:
        """Test the adminMode attribute just after device initialization.

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
        """
        assert sim_vcc_all_bands_device.adminMode == AdminMode.OFFLINE

    @pytest.mark.parametrize(
        "attribute_name",
        [
            "expectedDishId",
            "requestedRFIHeadroom",
            "vccGains",
            "frequencyBand",
            "inputSampleRate",
            "frequencyBandOffset",
            "subarrayID",
        ],
    )
    def test_read_attributes(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
        attribute_name: str,
    ) -> None:
        """Test uploading delay model

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
            attribute_name (:obj:`str`): Name of the attribute to test.
        """
        attribute_value = VCC_SIM_DEFAULT_ATTRIBUTE_VALUES[attribute_name]
        assert getattr(sim_vcc_all_bands_device, attribute_name) == attribute_value

    @pytest.mark.parametrize(
        "attribute_name",
        [
            "expectedDishId",
            "requestedRFIHeadroom",
            "vccGains",
            # "frequencyBand", # TODO fix enum test
            "inputSampleRate",
            "frequencyBandOffset",
            "subarrayID",
        ],
    )
    def test_attribute_overrides(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
        attribute_name: str,
    ) -> None:
        """Test overriding attributes"""
        attribute_value = VCC_SIM_DEFAULT_ATTRIBUTE_VALUES[attribute_name]
        attribute_new_value = ""
        if isinstance(attribute_value, str):
            attribute_new_value = "test"
        elif isinstance(attribute_value, int):
            attribute_new_value = 1
        elif isinstance(attribute_value, list):
            attribute_new_value = [1]
        # TODO fix enum test
        # elif isinstance(attribute_value, str):
        #     attribute_new_value = "_2"

        # Override attribute with new value
        sim_vcc_all_bands_device.simOverrides2 = json.dumps(
            {
                "attributes": {
                    attribute_name: attribute_new_value,
                }
            }
        )

        # Check value change
        assert (
            getattr(sim_vcc_all_bands_device, attribute_name) == attribute_new_value
        )

    def test_ConfigureScan_override_fail(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
        sim_vcc_all_bands_event_tracer: TangoEventTracer,
        event_timeout: int,
    ) -> None:
        """Test overriding ConfigureScan command to fail, then resetting to default
        behaviour.

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
            sim_vcc_all_bands_event_tracer (:obj:`TangoEventTracer`): Event tracer used to recieve subscribed change
                events from the device under test.
        """
        # Store original override values to reset later
        original_overrides = sim_vcc_all_bands_device.simOverrides

        # Set sim_vcc_all_bands_device ONLINE
        sim_vcc_all_bands_device.adminMode = AdminMode.ONLINE

        # Check event
        assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=sim_vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        # sim_vcc_all_bands_device pushes attribute events if value changes
        old_sub_id = sim_vcc_all_bands_device.subarrayID
        new_sub_id = old_sub_id + 1
        sim_vcc_all_bands_device.simOverrides = json.dumps(
            {
                "attributes": {
                    "subarrayID": new_sub_id,
                }
            }
        )

        # Defaults to successful commands
        [[result_code], [configure_scan_command_id]] = (
            sim_vcc_all_bands_device.ConfigureScan("test")
        )
        assert result_code == ResultCode.QUEUED
        [[result_code], [go_to_idle_command_id]] = sim_vcc_all_bands_device.GoToIdle()
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
            assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=sim_vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

        # Override ConfigureScan command to fail
        sim_vcc_all_bands_device.simOverrides = json.dumps(
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
            sim_vcc_all_bands_device.ConfigureScan("test")
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
            assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=sim_vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

        # Reset overrides
        sim_vcc_all_bands_device.simOverrides = original_overrides
        [[result_code], [configure_scan_command_id]] = (
            sim_vcc_all_bands_device.ConfigureScan("test")
        )
        assert result_code == ResultCode.QUEUED
        [[result_code], [go_to_idle_command_id]] = sim_vcc_all_bands_device.GoToIdle()
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
            assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=sim_vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

        # Set sim_vcc_all_bands_device OFFLINE
        sim_vcc_all_bands_device.adminMode = AdminMode.OFFLINE

        expected_events = [
            ("adminMode", AdminMode.OFFLINE, AdminMode.ONLINE, 1),
        ]

        # Check events
        for name, value, previous, n in expected_events:
            assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=sim_vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

    def test_scan(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
        sim_vcc_all_bands_event_tracer: TangoEventTracer,
        event_timeout: int,
    ) -> None:
        """Test Scan command

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
            sim_vcc_all_bands_event_tracer (:obj:`TangoEventTracer`): Event tracer used to recieve subscribed change
                events from the device under test.
        """
        # Set sim_vcc_all_bands_device ONLINE
        sim_vcc_all_bands_device.adminMode = AdminMode.ONLINE
        
        # Check event
        assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=sim_vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        # Set to READY obsState
        [[result_code], [configure_scan_command_id]] = sim_vcc_all_bands_device.ConfigureScan("")
        [[result_code], [scan_command_id]] = sim_vcc_all_bands_device.Scan(0)
        assert result_code == ResultCode.QUEUED
        assert result_code == ResultCode.QUEUED
        expected_events = [
            ("obsState", ObsState.SCANNING, ObsState.READY, 1),
            ("obsState", ObsState.SCANNING, ObsState.READY, 1),
            (
                "longRunningCommandResult",
                (
                    f"{configure_scan_command_id}",
                    f'[{ResultCode.OK.value}, "ConfigureScan completed OK"]',
                ),
                None,
                1,
            ),
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

        for name, value, previous, n in expected_events:
            assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=sim_vcc_all_bands_device,
                attribute_name=name,
                attribute_value=value,
                previous_value=previous,
                min_n_events=n,
            )

    @pytest.mark.parametrize(
        "command_name, \
        not_allowed_obs_states, \
        command_param",
        [
            ("AutoSetFilterGains", [ObsState.IDLE, ObsState.READY], [3.0]),
            ("UpdateSubarrayMembership", [ObsState.READY, ObsState.SCANNING], 1),
        ],
    )
    def test_not_allowed(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
        sim_vcc_all_bands_event_tracer: TangoEventTracer,
        command_name: str,
        not_allowed_obs_states: list[ObsState],
        command_param: Any,
        event_timeout: int,
    ) -> None:
        """Test commands failing in incorrect state parametrized

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
            sim_vcc_all_bands_event_tracer (:obj:`TangoEventTracer`): Event tracer used to recieve subscribed change
                events from the device under test.
        """
        # Test command not allowed in AdminMode.OFFLINE
        [[result_code], [command_id]] = sim_vcc_all_bands_device.command_inout(
            command_name, command_param
        )
        assert result_code == ResultCode.QUEUED
        assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=sim_vcc_all_bands_device,
            attribute_name="longRunningCommandResult",
            attribute_value=(
                f"{command_id}",
                f'[{ResultCode.NOT_ALLOWED.value}, "Command is not allowed"]',
            ),
        )

        # Test command not allowed in particular states
        for obs_state in not_allowed_obs_states:
            # Set state if needed
            if obs_state == ObsState.READY:
                sim_vcc_all_bands_device.ConfigureScan("")
            elif obs_state == ObsState.SCANNING:
                sim_vcc_all_bands_device.Scan(0)

            [[result_code], [command_id]] = sim_vcc_all_bands_device.command_inout(
                command_name, command_param
            )
            assert result_code == ResultCode.QUEUED

            assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                event_timeout
            ).has_change_event_occurred(
                device_name=sim_vcc_all_bands_device,
                attribute_name="longRunningCommandResult",
                attribute_value=(
                    f"{command_id}",
                    f'[{ResultCode.NOT_ALLOWED.value}, "Command is not allowed"]',
                ),
            )

    @pytest.mark.parametrize(
        "command_name, \
        allowed_obs_states, \
        command_param", 
        [
            ("AutoSetFilterGains", [ObsState.SCANNING], [3.0]),
            ("UpdateSubarrayMembership", [ObsState.IDLE], 1),
        ],
    )
    def test_commands(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
        sim_vcc_all_bands_event_tracer: TangoEventTracer,
        command_name: str,
        allowed_obs_states: list[ObsState],
        command_param: int,
        event_timeout: int,
    ) -> None:
        """Test all commands which do not require attribute change

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
            sim_vcc_all_bands_event_tracer (:obj:`TangoEventTracer`): Event tracer used to recieve subscribed change
                events from the device under test.
        """
        # Set device ONLINE
        sim_vcc_all_bands_device.adminMode = AdminMode.ONLINE
        assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=sim_vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        # Test command in allowed states
        for obs_state in allowed_obs_states:
            # Set state if needed - device starts in IDLE
            if obs_state in [ObsState.READY, ObsState.SCANNING]:
                sim_vcc_all_bands_device.ConfigureScan("")
                if obs_state == ObsState.SCANNING:
                    sim_vcc_all_bands_device.Scan(0)

            [[result_code], [command_id]] = sim_vcc_all_bands_device.command_inout(
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
                assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                    event_timeout
                ).has_change_event_occurred(
                    device_name=sim_vcc_all_bands_device,
                    attribute_name=name,
                    attribute_value=value,
                    previous_value=previous,
                    min_n_events=n,
                )

    @pytest.mark.parametrize(
        "command_name, \
        allowed_obs_states, \
        command_param", 
        [
            ("AutoSetFilterGains", [ObsState.SCANNING], [3.0]),
            ("UpdateSubarrayMembership", [ObsState.IDLE], 1),
        ],
    )
    def test_override_command_fail(
        self: TestVCCAllBandsSim,
        sim_vcc_all_bands_device: Any,
        sim_vcc_all_bands_event_tracer: TangoEventTracer,
        command_name: str,
        allowed_obs_states: list[ObsState],
        command_param: int,
        event_timeout: int,
    ) -> None:
        """Test overriding command to fail

        Args:
            sim_vcc_all_bands_device (:obj:`DeviceProxy`): Proxy to the device under test.
            sim_vcc_all_bands_event_tracer (:obj:`TangoEventTracer`): Event tracer used to recieve subscribed change
                events from the device under test.
        """
        # Set device ONLINE
        sim_vcc_all_bands_device.adminMode = AdminMode.ONLINE
        assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
            event_timeout
        ).has_change_event_occurred(
            device_name=sim_vcc_all_bands_device,
            attribute_name="adminMode",
            attribute_value=AdminMode.ONLINE,
            previous_value=AdminMode.OFFLINE,
            min_n_events=1,
        )

        # Override command to fail
        sim_vcc_all_bands_device.simOverrides = json.dumps(
            {
                "commands": {
                    f"{command_name}": {
                        "result_code": "FAILED",
                        "message": f"{command_name} failed",
                    },
                }
            }
        )

        # Test command in allowed states
        for obs_state in allowed_obs_states:
            # Set state if needed - device starts in IDLE
            if obs_state in [ObsState.READY, ObsState.SCANNING]:
                sim_vcc_all_bands_device.ConfigureScan("")
                if obs_state == ObsState.SCANNING:
                    sim_vcc_all_bands_device.Scan(0)

            [[result_code], [command_id]] = sim_vcc_all_bands_device.command_inout(
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

            for name, value, previous, n in expected_events:
                assert_that(sim_vcc_all_bands_event_tracer).within_timeout(
                    event_timeout
                ).has_change_event_occurred(
                    device_name=sim_vcc_all_bands_device,
                    attribute_name=name,
                    attribute_value=value,
                    previous_value=previous,
                    min_n_events=n,
                )
