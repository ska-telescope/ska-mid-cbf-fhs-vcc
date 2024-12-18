import time
from unittest import mock
from assertpy import assert_that
import pytest
from ska_mid_cbf_fhs_vcc.b123_vcc_osppfb_channeliser.b123_vcc_osppfb_channeliser_device import B123VccOsppfbChanneliser
from ska_mid_cbf_fhs_vcc.frequency_slice_selection.frequency_slice_selection_device import FrequencySliceSelection
from ska_mid_cbf_fhs_vcc.mac.mac_200_device import Mac200
from ska_mid_cbf_fhs_vcc.packet_validation.packet_validation_device import PacketValidation
from ska_mid_cbf_fhs_vcc.wideband_frequency_shifter.wideband_frequency_shifter_device import WidebandFrequencyShifter
from ska_mid_cbf_fhs_vcc.wideband_input_buffer.wideband_input_buffer_device import WidebandInputBuffer
from ska_mid_cbf_fhs_vcc.wideband_power_meter.wideband_power_meter_device import WidebandPowerMeter
from ska_mid_cbf_fhs_vcc.packetizer.packetizer_device import Packetizer
from tango import DevState
from ska_tango_testing import context
from ska_tango_testing.integration import TangoEventTracer
from ska_control_model import AdminMode, HealthState, ObsState, ResultCode
from ska_tango_testing.integration import TangoEventTracer


from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController

EVENT_TIMEOUT = 30


@pytest.fixture(name="test_context" )
def pv_device():
    """
    Fixture to set up the packet validation device for testing with a mock Tango database.
    """
    harness = context.ThreadedTestTangoContextManager()

    harness.add_device(
        device_name="test/vcc123/1",
        device_class=B123VccOsppfbChanneliser,
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
        device_name="test/mac200/1",
        device_class=Mac200,
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
        device_name="fhs/b123wpm/1",
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
        device_name="fhs/b45awpm/1",
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
        device_name="fhs/b5bwpm/1",
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

    for i in range(1, 26 + 1):
        harness.add_device(
            device_name=f"fhs/fs{i}wpm/1",
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
        mac_200_fqdn="test/mac200/1",
        packet_validation_fqdn="test/packet_validation/1",
        vcc123_channelizer_fqdn="test/vcc123/1",
        vcc45_channelizer_fqdn="vcc45",
        wideband_input_buffer_fqdn="test/wib/1",
        wideband_frequency_shifter_fqdn="test/wfs/1",
        circuit_switch_fqdn="cs",
        fs_selection_fqdn="test/fss/1",
        b123_wideband_power_meter_fqdn="fhs/b123wpm/1",
        b45a_wideband_power_meter_fqdn="fhs/b45awpm/1",
        b5b_wideband_power_meter_fqdn="fhs/b5bwpm/1",
        fs_wideband_power_meter_fqdn="fhs/fs<multiplicity>wpm/1",
        packetizer_fqdn="fhs/packetizer/1",
    )

    with harness as test_context:
        yield test_context


def test_init(vcc_all_bands_device):
    state = vcc_all_bands_device.state()
    assert state == DevState.ON


def test_adminMode_online(vcc_all_bands_device):
    prevAdminMode = vcc_all_bands_device.read_attribute("adminMode")

    assert prevAdminMode.value == AdminMode.OFFLINE.value

    vcc_all_bands_device.write_attribute("adminMode", 0)

    adminMode = vcc_all_bands_device.read_attribute("adminMode")

    assert adminMode.value == AdminMode.ONLINE.value


def test_health_state_prop(vcc_all_bands_device, wib_device, wib_event_tracer):
    test_adminMode_online(vcc_all_bands_device)

    allBandsHealthState = vcc_all_bands_device.read_attribute("healthState")

    assert allBandsHealthState.value == HealthState.OK.value

    config_json = '{"expected_sample_rate": 3920000000, "noise_diode_transition_holdoff_seconds": 1.0, "expected_dish_band": 1}'

    # Invoke the command
    result = wib_device.command_inout("Configure", config_json)

    assert wib_device.read_attribute("obsState").value is ObsState.READY.value

    result = wib_device.command_inout("Start")

    # Extract the result code and message
    result_code = result[0][0]

    # Assertions
    assert result_code == ResultCode.QUEUED.value, f"Expected ResultCode.QUEUED ({ResultCode.QUEUED.value}), got {result_code}"

    assert_that(wib_event_tracer).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
        device_name=wib_device,
        attribute_name="longRunningCommandResult",
        attribute_value=(
            f"{result[1][0]}",
            f'[{ResultCode.OK.value}, "Start Called Successfully"]',
        ),
    )

    time.sleep(10)

    healthState = wib_device.read_attribute("healthState")

    assert healthState.value is HealthState.FAILED.value

    vccHealthState = vcc_all_bands_device.read_attribute("healthState")

    assert vccHealthState.value is HealthState.FAILED.value


def test_adminMode_offline(vcc_all_bands_device, wib_device, wib_event_tracer):
    test_health_state_prop(vcc_all_bands_device, wib_device, wib_event_tracer)
    prevAdminMode = vcc_all_bands_device.read_attribute("adminMode")

    assert prevAdminMode.value == AdminMode.ONLINE.value

    vcc_all_bands_device.write_attribute("adminMode", 1)

    adminMode = vcc_all_bands_device.read_attribute("adminMode")

    assert adminMode.value == AdminMode.OFFLINE.value
