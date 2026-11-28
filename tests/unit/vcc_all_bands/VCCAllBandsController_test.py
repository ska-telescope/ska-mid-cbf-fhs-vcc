# type: ignore[reportAttributeAccessIssue]
import json
import os
import time
from base64 import b64encode
from collections.abc import Generator
from unittest import mock

import pytest
import tango
from assertpy import assert_that
from ska_control_model import HealthState, ResultCode
from ska_control_model.future import AdminMode
from ska_mid_cbf_fhs_common import (
    LONG_RUNNING_COMMAND_RESULT_BUFFER_DEFAULT_MAX_SIZE,
    ConfigurableThreadedTestTangoContextManager,
    DeviceTestUtils,
    power_linear_to_db,
)
from ska_tango_testing.harness import TangoTestHarnessContext
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

EVENT_TIMEOUT = 30

TEST_MAPPING_PATH = "tests/test_data"

PWR_0_3_TO_DB = power_linear_to_db(0.3)
PWR_0_4_TO_DB = power_linear_to_db(0.4)
PWR_0_5_TO_DB = power_linear_to_db(0.5)
PWR_0_6_TO_DB = power_linear_to_db(0.6)
PWR_0_7_TO_DB = power_linear_to_db(0.7)
PWR_0_8_TO_DB = power_linear_to_db(0.8)
PWR_0_9_TO_DB = power_linear_to_db(0.9)


@pytest.fixture(scope="session")  # Use "session" scope for true constants
def event_timeout() -> int:
    """Event tracer timeout."""
    return 10


@pytest.fixture(name="vcc_all_bands_device")
def vcc_all_bands_device_fixture(
    test_context: TangoTestHarnessContext,
) -> tango.DeviceProxy:
    """Fixture that returns the device under test.

    Args:
        test_context (:obj:`TangoTestHarnessContext`): The context in which the tests run.

    Returns:
        :obj:`tango.DeviceProxy`: A proxy to the device under test.
    """
    return test_context.get_device("test/vccallbands/1")


@pytest.fixture(name="vcc_all_bands_event_tracer", autouse=True)
def vcc_all_bands_tango_event_tracer(
    vcc_all_bands_device: tango.DeviceProxy,
) -> Generator[TangoEventTracer]:
    """Fixture that returns a TangoEventTracer for pertinent devices.
    Takes as parameter all required device proxy fixtures for this test module.

    Args:
        device_under_test (:obj:`tango.DeviceProxy`): Proxy to the device under test.

    Returns:
        :obj:`TangoEventTracer`: An event tracer for the device under test.
    """
    tracer = TangoEventTracer(
        event_enum_mapping={
            "adminMode": AdminMode,
            "healthState": HealthState,
        }
    )

    change_event_attr_list = [
        "longRunningCommandResult",
        "adminMode",
        "state",
        "healthState",
        "subarrayID",
    ]
    for attr in change_event_attr_list:
        tracer.subscribe_event(vcc_all_bands_device, attr)

    yield tracer

    tracer.unsubscribe_all()
    tracer.clear_events()


@pytest.mark.forked
class TestVCCAllBandsController:
    @pytest.fixture(name="test_context", scope="module")
    def init_test_context(self):
        """
        Fixture to set up the VCC All Bands device for testing with a mock Tango database.
        """
        harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)
        os.environ["VCC_PRODUCT_PATH"] = TEST_MAPPING_PATH

        default_ip_block = {
            "emulator_ip_block_id": "n/a",
            "firmware_ip_block_id": "n/a",
        }
        ip_blocks = {
            "Ethernet200Gb": default_ip_block
            | {
                "ethernet_mode": "200GbE",
                "health_monitor_poll_interval": "60",
            },
            "B123VccOsppfbChannelizer": default_ip_block,
            "FrequencySliceSelection": default_ip_block,
            "PacketValidation": default_ip_block,
            "WidebandFrequencyShifter": default_ip_block,
            "WidebandInputBuffer": default_ip_block
            | {
                "health_monitor_poll_interval": "3",
            },
            "VCCStreamMerge1": default_ip_block,
            "VCCStreamMerge2": default_ip_block,
            "B123WidebandPowerMeter": default_ip_block,
            "B45AWidebandPowerMeter": default_ip_block,
            "B5BWidebandPowerMeter": default_ip_block,
            **{f"FS{i}WidebandPowerMeter": default_ip_block for i in range(1, 27)},
        }

        harness.add_device(
            device_name="test/vccallbands/1",
            device_class=VCCAllBandsController,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="n/a",
            emulator_port="5001",
            bitstream_path="tests/resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            logging_level="DEBUG",
            ip_blocks=b64encode(json.dumps(ip_blocks).encode("utf-8")).decode("ascii"),
            long_running_command_result_buffer_max_size=LONG_RUNNING_COMMAND_RESULT_BUFFER_DEFAULT_MAX_SIZE,
        )

        with harness as test_context:
            yield test_context

    def run_configure_scan(self, vcc_all_bands_device: tango.DeviceProxy, config_file_path: str = "tests/test_data/command_inputs/configure_scan.json"):
        with open(config_file_path) as config_file:
            config_str = config_file.read()
        vcc_all_bands_device.command_inout("ConfigureScan", config_str)

    def run_go_to_idle(self, vcc_all_bands_device: tango.DeviceProxy, config_file_path: str = "tests/test_data/command_inputs/go_to_idle.json"):
        with open(config_file_path) as config_file:
            config_str = config_file.read()
        vcc_all_bands_device.command_inout("GoToIdle", config_str)

    def test_init(self, vcc_all_bands_device: tango.DeviceProxy):
        assert vcc_all_bands_device.state() == DevState.ON

    def test_admin_mode_online(self, vcc_all_bands_device: tango.DeviceProxy):
        assert vcc_all_bands_device.adminMode == AdminMode.ONLINE

    @pytest.mark.parametrize(
        ("current_subarray", "new_subarray", "expected_result"),
        [
            pytest.param(0, 0, ResultCode.OK, id="unassign_from_unassigned_vcc_ok"),
            pytest.param(0, 1, ResultCode.OK, id="assign_to_unassigned_vcc_ok"),
            pytest.param(1, 0, ResultCode.OK, id="unassign_from_assigned_vcc_ok"),
            pytest.param(1, 2, ResultCode.REJECTED, id="assign_to_assigned_vcc_rejected"),
            pytest.param(0, 33, ResultCode.REJECTED, id="id_out_of_range_rejected"),
        ],
    )
    def test_update_subarray_membership(
        self,
        current_subarray: int,
        new_subarray: int,
        expected_result: ResultCode,
        vcc_all_bands_device: tango.DeviceProxy,
        vcc_all_bands_event_tracer: TangoEventTracer,
    ):
        # Setup for unassign cases by first assigning subarray membership
        instant_fail = True
        if current_subarray != 0:
            vcc_all_bands_device.command_inout("UpdateSubarrayMembership", current_subarray)
            DeviceTestUtils.assert_lrc_completed(vcc_all_bands_device, vcc_all_bands_event_tracer, EVENT_TIMEOUT, "UpdateSubarrayMembership", [ResultCode.OK])
            instant_fail = False
            assert_that(vcc_all_bands_event_tracer).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
                device_name=vcc_all_bands_device,  # type: ignore[reportCallIssue]
                attribute_name="subarrayID",
                attribute_value=current_subarray,
                previous_value=0,
            )

        # Update subarray membership
        vcc_all_bands_device.command_inout("UpdateSubarrayMembership", new_subarray)
        DeviceTestUtils.assert_lrc_completed(
            vcc_all_bands_device,
            vcc_all_bands_event_tracer,
            EVENT_TIMEOUT,
            "UpdateSubarrayMembership",
            [expected_result],
            instant_fail_on_non_passing_result=instant_fail,
        )
        if expected_result == ResultCode.OK:
            assert_that(vcc_all_bands_event_tracer).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
                device_name=vcc_all_bands_device,  # type: ignore[reportCallIssue]
                attribute_name="subarrayID",
                attribute_value=new_subarray,
                previous_value=current_subarray,
            )
        else:
            assert vcc_all_bands_device.subarrayID == current_subarray

    def test_configure_scan(
        self,
        vcc_all_bands_device: tango.DeviceProxy,
        vcc_all_bands_event_tracer: TangoEventTracer,
    ):
        self.run_configure_scan(vcc_all_bands_device)
        DeviceTestUtils.assert_lrc_completed(
            vcc_all_bands_device,
            vcc_all_bands_event_tracer,
            EVENT_TIMEOUT,
            "ConfigureScan",
            passing_result_codes=[ResultCode.OK],
        )

    def test_power_meter_polling_no_gain_results_in_averaged_values_success(
        self,
        vcc_all_bands_device: tango.DeviceProxy,
        vcc_all_bands_event_tracer: TangoEventTracer,
    ):
        def mock_status(slf, clear: bool = False):
            if getattr(slf, "iter", 0) == 0:
                setattr(slf, "iter", 1)
                return {
                    "timestamp": 0,
                    "avg_power_pol_x": 0.5,
                    "avg_power_pol_y": 0.5,
                    "nd_on_power_pol_x": 0.5,
                    "nd_on_power_pol_y": 0.5,
                    "nd_off_power_pol_x": 0.5,
                    "nd_off_power_pol_y": 0.5,
                    "nd_trn_power_pol_x": 0.5,
                    "nd_trn_power_pol_y": 0.5,
                    "flag": False,
                    "overflow": 0,
                    "measured_sample_fraction": 0.5,
                    "flagged_sample_fraction": 0.0,
                }
            else:
                setattr(slf, "iter", 0)
                return {
                    "timestamp": 0,
                    "avg_power_pol_x": 0.9,
                    "avg_power_pol_y": 0.8,
                    "nd_on_power_pol_x": 0.7,
                    "nd_on_power_pol_y": 0.6,
                    "nd_off_power_pol_x": 0.4,
                    "nd_off_power_pol_y": 0.3,
                    "nd_trn_power_pol_x": 0.2,
                    "nd_trn_power_pol_y": 0.1,
                    "flag": False,
                    "overflow": 0,
                    "measured_sample_fraction": 0.5,
                    "flagged_sample_fraction": 0.0,
                }

        with mock.patch(
            "ska_mid_cbf_fhs_common.WidebandPowerMeterSimulator.status",
            side_effect=mock_status,
            autospec=True,
            create=True,
        ):
            self.run_configure_scan(vcc_all_bands_device, config_file_path="tests/test_data/command_inputs/configure_scan_pwr_nogain.json")
            DeviceTestUtils.assert_lrc_completed(
                vcc_all_bands_device,
                vcc_all_bands_event_tracer,
                EVENT_TIMEOUT,
                "ConfigureScan",
                passing_result_codes=[ResultCode.OK],
            )
            time.sleep(8)

            wb_power1 = vcc_all_bands_device.read_attribute("widebandPower1")
            wb_power2 = vcc_all_bands_device.read_attribute("widebandPower2")
            fs_power_total = vcc_all_bands_device.read_attribute("vccPower")
            fs_power_on = vcc_all_bands_device.read_attribute("ndOnPower")
            fs_power_off = vcc_all_bands_device.read_attribute("ndOffPower")
            headrooms = vcc_all_bands_device.read_attribute("headrooms")

            for wb_power in (wb_power1, wb_power2):
                assert PWR_0_4_TO_DB < wb_power.value[0][0] < PWR_0_5_TO_DB, (
                    f"WB polX ND-OFF power was: {round(wb_power.value[0][0], 8)}, expected to be between: {round(PWR_0_4_TO_DB, 8)}, {round(PWR_0_5_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < wb_power.value[0][1] < PWR_0_7_TO_DB, (
                    f"WB polX ND-ON power was: {round(wb_power.value[0][1], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_7_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < wb_power.value[0][2] < PWR_0_9_TO_DB, (
                    f"WB polX TOTAL power was: {round(wb_power.value[0][2], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_9_TO_DB, 8)}"
                )
                assert PWR_0_3_TO_DB < wb_power.value[1][0] < PWR_0_5_TO_DB, (
                    f"WB polY ND-OFF power was: {round(wb_power.value[1][0], 8)}, expected to be between: {round(PWR_0_3_TO_DB, 8)}, {round(PWR_0_5_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < wb_power.value[1][1] < PWR_0_6_TO_DB, (
                    f"WB polY ND-ON power was: {round(wb_power.value[1][1], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_6_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < wb_power.value[1][2] < PWR_0_8_TO_DB, (
                    f"WB polY TOTAL power was: {round(wb_power.value[1][2], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_8_TO_DB, 8)}"
                )

            for fs_id in range(1, 6):
                attr_fs_idx = fs_id - 1
                assert PWR_0_4_TO_DB < fs_power_off.value[0][attr_fs_idx] < PWR_0_5_TO_DB, (
                    f"FS {fs_id} polX ND-OFF power was: {round(fs_power_off.value[0][attr_fs_idx], 8)}, expected to be between: {round(PWR_0_4_TO_DB, 8)}, {round(PWR_0_5_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < fs_power_on.value[0][attr_fs_idx] < PWR_0_7_TO_DB, (
                    f"FS {fs_id} polX ND-ON power was: {round(fs_power_on.value[0][attr_fs_idx], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_7_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < fs_power_total.value[0][attr_fs_idx] < PWR_0_9_TO_DB, (
                    f"FS {fs_id} polX TOTAL power was: {round(fs_power_total.value[0][attr_fs_idx], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_9_TO_DB, 8)}"
                )
                assert PWR_0_3_TO_DB < fs_power_off.value[1][attr_fs_idx] < PWR_0_5_TO_DB, (
                    f"FS {fs_id} polY ND-OFF power was: {round(fs_power_off.value[1][attr_fs_idx], 8)}, expected to be between: {round(PWR_0_3_TO_DB, 8)}, {round(PWR_0_5_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < fs_power_on.value[1][attr_fs_idx] < PWR_0_6_TO_DB, (
                    f"FS {fs_id} polY ND-ON power was: {round(fs_power_on.value[1][attr_fs_idx], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_6_TO_DB, 8)}"
                )
                assert PWR_0_5_TO_DB < fs_power_total.value[1][attr_fs_idx] < PWR_0_8_TO_DB, (
                    f"FS {fs_id} polY TOTAL power was: {round(fs_power_total.value[1][attr_fs_idx], 8)}, expected to be between: {round(PWR_0_5_TO_DB, 8)}, {round(PWR_0_8_TO_DB, 8)}"
                )

                assert headrooms.value[0][attr_fs_idx] == pytest.approx(-fs_power_total.value[0][attr_fs_idx])  # X
                assert headrooms.value[1][attr_fs_idx] == pytest.approx(-fs_power_total.value[1][attr_fs_idx])  # Y

            for fs_id in range(6, 9):
                attr_fs_idx = fs_id - 1
                assert fs_power_off.value[0][attr_fs_idx] == pytest.approx(PWR_0_4_TO_DB) or fs_power_off.value[0][attr_fs_idx] == pytest.approx(
                    PWR_0_5_TO_DB
                )  # ND OFF X
                assert fs_power_on.value[0][attr_fs_idx] == pytest.approx(PWR_0_5_TO_DB) or fs_power_on.value[0][attr_fs_idx] == pytest.approx(
                    PWR_0_7_TO_DB
                )  # ND ON X
                assert fs_power_total.value[0][attr_fs_idx] == pytest.approx(PWR_0_5_TO_DB) or fs_power_total.value[0][attr_fs_idx] == pytest.approx(
                    PWR_0_9_TO_DB
                )  # TOTAL X
                assert fs_power_off.value[1][attr_fs_idx] == pytest.approx(PWR_0_3_TO_DB) or fs_power_off.value[1][attr_fs_idx] == pytest.approx(
                    PWR_0_5_TO_DB
                )  # ND OFF Y
                assert fs_power_on.value[1][attr_fs_idx] == pytest.approx(PWR_0_5_TO_DB) or fs_power_on.value[1][attr_fs_idx] == pytest.approx(
                    PWR_0_6_TO_DB
                )  # ND ON Y
                assert fs_power_total.value[1][attr_fs_idx] == pytest.approx(PWR_0_5_TO_DB) or fs_power_total.value[1][attr_fs_idx] == pytest.approx(
                    PWR_0_8_TO_DB
                )  # TOTAL Y

                assert headrooms.value[0][attr_fs_idx] == pytest.approx(-fs_power_total.value[0][attr_fs_idx])  # X
                assert headrooms.value[1][attr_fs_idx] == pytest.approx(-fs_power_total.value[1][attr_fs_idx])  # Y
