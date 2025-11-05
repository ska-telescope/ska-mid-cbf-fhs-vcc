from base64 import b64encode
from collections.abc import Generator
import json
from unittest import mock
import pytest
from assertpy import assert_that
from ska_mid_cbf_fhs_common.testing.device_test_utils import DeviceTestUtils
from ska_mid_cbf_fhs_common import MPFloat, DeviceTestUtils, WidebandPowerMeterStatus
from tango import DevState
from ska_control_model import AdminMode, HealthState, ObsState, ResultCode
from ska_mid_cbf_fhs_common import ConfigurableThreadedTestTangoContextManager
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.harness import TangoTestHarnessContext

EVENT_TIMEOUT = 30


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

        default_ip_block = {
            "emulator_ip_block_id": "n/a",
            "firmware_ip_block_id": "n/a",
        }
        ip_blocks = {
            "Ethernet200Gb": default_ip_block | {
                "ethernet_mode": "200GbE",
                "health_monitor_poll_interval": "60",
            }, 
            "B123VccOsppfbChannelizer": default_ip_block,
            "FrequencySliceSelection": default_ip_block,
            "PacketValidation": default_ip_block,
            "WidebandFrequencyShifter": default_ip_block,
            "WidebandInputBuffer": default_ip_block | {
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
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="tests/resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            logging_level="DEBUG",
            ip_blocks=b64encode(json.dumps(ip_blocks).encode("utf-8")).decode("ascii"),
        )

        with harness as test_context:
            yield test_context

    def test_init(self, vcc_all_bands_device: VCCAllBandsController):
        state = vcc_all_bands_device.state()
        assert state == DevState.ON

    def test_admin_mode_online(self, vcc_all_bands_device: VCCAllBandsController):
        prev_admin_mode = vcc_all_bands_device.read_attribute("adminMode")

        assert prev_admin_mode.value == AdminMode.OFFLINE.value

        vcc_all_bands_device.write_attribute("adminMode", 0)

        admin_mode = vcc_all_bands_device.read_attribute("adminMode")

        assert admin_mode.value == AdminMode.ONLINE.value

    def test_admin_mode_offline(self, vcc_all_bands_device: VCCAllBandsController):
        self.test_admin_mode_online(vcc_all_bands_device)
        prev_admin_mode = vcc_all_bands_device.read_attribute("adminMode")

        assert prev_admin_mode.value == AdminMode.ONLINE.value

        vcc_all_bands_device.write_attribute("adminMode", 1)

        admin_mode = vcc_all_bands_device.read_attribute("adminMode")

        assert admin_mode.value == AdminMode.OFFLINE.value

    @pytest.mark.parametrize(
        ("current_subarray", "new_subarray", "expected_result"),
        [
            pytest.param(0, 0, ResultCode.OK, id="unassign_from_unassigned_vcc_ok"),
            pytest.param(0, 1, ResultCode.OK, id="assign_to_unassigned_vcc_ok"),
            pytest.param(1, 0, ResultCode.OK, id="unassign_from_assigned_vcc_ok"),
            pytest.param(1, 2, ResultCode.REJECTED, id="assign_to_assigned_vcc_rejected"),
            pytest.param(0, 33, ResultCode.REJECTED, id="id_out_of_range_rejected"),
        ]
    )
    def test_update_subarray_membership(
        self,
        current_subarray: int,
        new_subarray: int,
        expected_result: ResultCode,
        vcc_all_bands_device: VCCAllBandsController,
        vcc_all_bands_event_tracer: TangoEventTracer,
    ):
        # Setup for unassign cases by first assigning subarray membership
        instant_fail = True
        if current_subarray != 0:
            vcc_all_bands_device.command_inout("UpdateSubarrayMembership", current_subarray)
            DeviceTestUtils.assert_lrc_completed(
                vcc_all_bands_device,
                vcc_all_bands_event_tracer,
                EVENT_TIMEOUT,
                "UpdateSubarrayMembership",
                [ResultCode.OK]
            )
            instant_fail = False
            assert_that(vcc_all_bands_event_tracer).within_timeout(
                EVENT_TIMEOUT
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
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
            instant_fail_on_non_passing_result=instant_fail
        )
        if expected_result == ResultCode.OK:
            assert_that(vcc_all_bands_event_tracer).within_timeout(
                EVENT_TIMEOUT
            ).has_change_event_occurred(
                device_name=vcc_all_bands_device,
                attribute_name="subarrayID",
                attribute_value=new_subarray,
                previous_value=current_subarray,
            )
        else:
            assert vcc_all_bands_device.subarrayID == current_subarray

    @pytest.mark.parametrize(
        ("measured_power", "headroom", "expected_multipliers", "expected_result"),
        [
            pytest.param(
                [
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4
                ],
                [3.0],
                [
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.119360569284169805977475"),
                ],
                ResultCode.OK,
                id="default_headroom_all_measurements_equal_ok"
            ),
            pytest.param(
                [
                    0.4,
                    0.5,
                    0.6,
                    0.7,
                    0.4,
                    0.5,
                    0.6,
                    0.7,
                    0.4,
                    0.5,
                    0.6,
                    0.7,
                    0.4,
                    0.5,
                    0.6,
                    0.7,
                    0.4,
                    0.5,
                    0.6,
                    0.7
                ],
                [3.0],
                [
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.001186529700906718108588"),
                    MPFloat("0.9139540776458376348589872"),
                    MPFloat("0.8461570553535996445330887"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.001186529700906718108588"),
                    MPFloat("0.9139540776458376348589872"),
                    MPFloat("0.8461570553535996445330887"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.001186529700906718108588"),
                    MPFloat("0.9139540776458376348589872"),
                    MPFloat("0.8461570553535996445330887"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.001186529700906718108588"),
                    MPFloat("0.9139540776458376348589872"),
                    MPFloat("0.8461570553535996445330887"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("1.001186529700906718108588"),
                    MPFloat("0.9139540776458376348589872"),
                    MPFloat("0.8461570553535996445330887"),
                ],
                ResultCode.OK,
                id="default_headroom_differing_measurements_ok"
            ),
            pytest.param(
                [
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4
                ],
                [6.0],
                [
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("0.7924465962305567426010507"),
                ],
                ResultCode.OK,
                id="custom_headroom_ok"
            ),
            pytest.param(
                [
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4
                ],
                [
                    3.0,
                    6.0,
                    3.0,
                    6.0,
                    3.0,
                    6.0,
                    3.0,
                    6.0,
                    3.0,
                    6.0,
                ],
                [
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                    MPFloat("1.119360569284169805977475"),
                    MPFloat("0.7924465962305567426010507"),
                ],
                ResultCode.OK,
                id="multiple_headrooms_ok"
            ),
            pytest.param(
                [
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4
                ],
                [
                    3.0,
                    6.0,
                ],
                [
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                ],
                ResultCode.REJECTED,
                id="invalid_num_headrooms_rejected"
            ),
            pytest.param(
                [
                    -0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4,
                    0.4
                ],
                [3.0],
                [
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                    MPFloat("1.0"),
                ],
                ResultCode.FAILED,
                id="bad_power_reading_failed"
            ),
        ]
    )
    def test_auto_set_filter_gains(
        self,
        measured_power: list[float],
        headroom: list[float],
        expected_multipliers: list[MPFloat],
        expected_result: ResultCode,
        vcc_all_bands_device: VCCAllBandsController,
        vcc_all_bands_event_tracer: TangoEventTracer,
    ):
        with open("tests/test_data/device_config/vcc_all_bands.json", "r") as f:
            config_json = f.read()

        vcc_all_bands_device.write_attribute("adminMode", 0)

        vcc_all_bands_device.command_inout("ConfigureScan", config_json)
            
        DeviceTestUtils.assert_lrc_completed(
            vcc_all_bands_device,
            vcc_all_bands_event_tracer,
            EVENT_TIMEOUT,
            "ConfigureScan",
        )

        with mock.patch(
            "ska_mid_cbf_fhs_common.ip_blocks.wideband_power_meter.wideband_power_meter_manager.WidebandPowerMeterManager.status",
            side_effect=[
                WidebandPowerMeterStatus(
                    0,
                    measured_power[i],
                    measured_power[i + len(measured_power) // 2],
                    0, 0, 0, 0, 0, 0, False, 0
                )
            for i in range(len(measured_power) // 2)],
            create=True,
        ):
            requested_headrooms_before = vcc_all_bands_device.read_attribute("requestedRFIHeadroom")

            vcc_all_bands_device.command_inout("AutoSetFilterGains", headroom)

            DeviceTestUtils.assert_lrc_completed(
                vcc_all_bands_device,
                vcc_all_bands_event_tracer,
                EVENT_TIMEOUT,
                "AutoSetFilterGains",
                [expected_result]
            )

            multipliers = vcc_all_bands_device.read_attribute("vccGains")
            assert len(multipliers.value) == len(expected_multipliers)
            for multiplier, expected_multiplier in zip(multipliers.value, expected_multipliers):
                MPFloat.assert_almosteq(multiplier, expected_multiplier, rel_tolerance=1e-12, abs_tolerance=1e-14)

            requested_headrooms_after = vcc_all_bands_device.read_attribute("requestedRFIHeadroom")
            expected_headrooms = headroom if expected_result == ResultCode.OK else requested_headrooms_before.value
            assert len(requested_headrooms_after.value) == len(expected_headrooms)
            assert all(
                requested_headroom == expected_headroom
                for requested_headroom, expected_headroom in zip(requested_headrooms_after.value, expected_headrooms)
            )
