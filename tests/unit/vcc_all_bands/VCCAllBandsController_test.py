import json
import time
from unittest import mock
from assertpy import assert_that
import pytest
from ska_mid_cbf_fhs_common.testing.device_test_utils import DeviceTestUtils
from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channelizer.b123_vcc_osppfb_channelizer_device import B123VccOsppfbChannelizer
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_device import FrequencySliceSelection
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_device import PacketValidation
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_device import WidebandFrequencyShifter
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_device import WidebandInputBuffer
from ska_mid_cbf_fhs_common import WidebandPowerMeter, FtileEthernet, MPFloat, DeviceTestUtils
from ska_mid_cbf_fhs_vcc.vcc_stream_merge.vcc_stream_merge_device import VCCStreamMerge
from tango import DevState
from ska_control_model import AdminMode, HealthState, ResultCode
from ska_mid_cbf_fhs_common import ConfigurableThreadedTestTangoContextManager
from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

EVENT_TIMEOUT = 30

@pytest.mark.forked
class TestVCCAllBandsController:

    @pytest.fixture(name="test_context", scope="module")
    def init_test_context(self):
        """
        Fixture to set up the VCC All Bands device for testing with a mock Tango database.
        """
        harness = ConfigurableThreadedTestTangoContextManager(timeout=30.0)

        harness.add_device(
            device_name="test/vcc123/1",
            device_class=B123VccOsppfbChannelizer,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="b123vcc",
            emulator_id="vcc-emulator-1",
        )

        harness.add_device(
            device_name="test/fss/1",
            device_class=FrequencySliceSelection,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="fs_selection_26_2_1",
            emulator_id="vcc-emulator-1",
        )

        harness.add_device(
            device_name="test/ethernet200g/1",
            device_class=FtileEthernet,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="ethernet_200g",
            emulator_id="vcc-emulator-1",
            health_monitor_poll_interval="1",
        )

        harness.add_device(
            device_name="test/packet_validation/1",
            device_class=PacketValidation,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="packet_validation",
            emulator_id="vcc-emulator-1",
        )

        harness.add_device(
            device_name="test/wfs/1",
            device_class=WidebandFrequencyShifter,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="wideband_frequency_shifter",
            emulator_id="vcc-emulator-1",
        )

        harness.add_device(
            device_name="test/wib/1",
            device_class=WidebandInputBuffer,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="wideband_input_buffer",
            emulator_id="vcc-emulator-1",
            health_monitor_poll_interval="1",
        )

        harness.add_device(
            device_name="test/b123wpm/1",
            device_class=WidebandPowerMeter,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="b123_wideband_power_meter",
            emulator_id="vcc-emulator-1",
        )

        harness.add_device(
            device_name="test/b45awpm/1",
            device_class=WidebandPowerMeter,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="b45a_wideband_power_meter",
            emulator_id="vcc-emulator-1",
        )

        harness.add_device(
            device_name="test/b5bwpm/1",
            device_class=WidebandPowerMeter,
            device_id="1",
            device_version_num="1.0",
            device_gitlab_hash="abc123",
            emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
            bitstream_path="../resources",
            bitstream_id="agilex-vcc",
            bitstream_version="0.0.1",
            simulation_mode="1",
            emulation_mode="0",
            emulator_ip_block_id="b5b_wideband_power_meter",
            emulator_id="vcc-emulator-1",
        )

        for i in range(1, 3):
            harness.add_device(
                device_name=f"test/vcc-stream-merge{i}/1",
                device_class=VCCStreamMerge,
                device_id="1",
                device_version_num="1.0",
                device_gitlab_hash="abc123",
                emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
                bitstream_path="../resources",
                bitstream_id="agilex-vcc",
                bitstream_version="0.0.1",
                simulation_mode="1",
                emulation_mode="0",
                emulator_ip_block_id=f"vcc_stream_merge{i}",
                emulator_id="vcc-emulator-1",
            )

        for i in range(1, 26 + 1):
            harness.add_device(
                device_name=f"test/fs{i}wpm/1",
                device_class=WidebandPowerMeter,
                device_id="1",
                device_version_num="1.0",
                device_gitlab_hash="abc123",
                emulator_base_url="emulators.ska-mid-cbf-emulators.svc.cluster.local:5001",
                bitstream_path="../resources",
                bitstream_id="agilex-vcc",
                bitstream_version="0.0.1",
                simulation_mode="1",
                emulation_mode="0",
                emulator_ip_block_id=f"fs_wideband_power_meter_{i}",
                emulator_id="vcc-emulator-1",
            )

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
            simulation_mode="0",
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

    def test_init(self, vcc_all_bands_device):
        state = vcc_all_bands_device.state()
        assert state == DevState.ON

    def test_adminMode_online(self, vcc_all_bands_device):
        prev_admin_mode = vcc_all_bands_device.read_attribute("adminMode")

        assert prev_admin_mode.value == AdminMode.OFFLINE.value

        vcc_all_bands_device.write_attribute("adminMode", 0)

        admin_mode = vcc_all_bands_device.read_attribute("adminMode")

        assert admin_mode.value == AdminMode.ONLINE.value

    def test_health_state_prop(self, vcc_all_bands_device, wib_device, wib_event_tracer):
        self.test_adminMode_online(vcc_all_bands_device)

        all_bands_health_state = vcc_all_bands_device.read_attribute("healthState")

        assert all_bands_health_state.value == HealthState.OK.value

        DeviceTestUtils.polling_test_setup(
            device_under_test=wib_device,
            event_tracer=wib_event_tracer,
            config_json_file="tests/test_data/device_config/wideband_input_buffer_health_failure.json",
            event_timeout=EVENT_TIMEOUT
        )

        time.sleep(3)

        health_state = wib_device.read_attribute("healthState")

        assert health_state.value is HealthState.FAILED.value

        vcc_health_state = vcc_all_bands_device.read_attribute("healthState")

        assert vcc_health_state.value is HealthState.FAILED.value

    def test_adminMode_offline(self, vcc_all_bands_device, wib_device, wib_event_tracer):
        self.test_health_state_prop(vcc_all_bands_device, wib_device, wib_event_tracer)
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
        vcc_all_bands_device,
        vcc_all_bands_event_tracer
    ):
        with mock.patch(
            "ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_component_manager.VCCAllBandsComponentManager.subarray_id",
            new_callable=mock.PropertyMock,
            return_value=current_subarray,
            create=True
        ):
            vcc_all_bands_device.command_inout("UpdateSubarrayMembership", new_subarray)
            
            DeviceTestUtils.assert_lrc_completed(
                vcc_all_bands_device,
                vcc_all_bands_event_tracer,
                EVENT_TIMEOUT,
                "UpdateSubarrayMembership",
                [expected_result]
            )

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
        vcc_all_bands_device,
        vcc_all_bands_event_tracer
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
            "tango.DeviceProxy.GetStatus",
            side_effect=[
                (None, (json.dumps({"avg_power_pol_x": measured_power[i], "avg_power_pol_y": measured_power[i + len(measured_power) // 2]}), None))
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
