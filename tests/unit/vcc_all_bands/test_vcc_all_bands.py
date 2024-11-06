
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
from tango import DevState
from ska_tango_testing import context
from ska_tango_testing.integration import TangoEventTracer
from ska_control_model import AdminMode, ObsState, ResultCode


from ska_mid_cbf_fhs_vcc.vcc_all_bands.vcc_all_bands_device import VCCAllBandsController


@pytest.fixture(name="test_context")
def pv_device():
    """
    Fixture to set up the packet validation device for testing with a mock Tango database.
    """
    harness = context.ThreadedTestTangoContextManager()
    
    harness.add_device(device_name="test/vcc123/1", 
                    device_class=B123VccOsppfbChanneliser, 
                    device_id="1",
                    device_version_num="1.0",
                    device_gitlab_hash="abc123",
                    config_location="../../resources/",
                    simulation_mode="1",
                    emulation_mode="0",
                    emulator_ip_block_id="b123vcc")
    
    harness.add_device(device_name="test/fss/1", 
                       device_class=FrequencySliceSelection,
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0",
                       emulator_ip_block_id="fs_selection_26_2_1",
                       emulator_id="vcc-emulator-1")
    
    harness.add_device(device_name="test/mac200/1", 
                       device_class=Mac200, 
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0",
                       emulator_ip_block_id="ethernet_200g",
                       emulator_id="vcc-emulator-1")
    
    harness.add_device(device_name="test/packet_validation/1", 
                       device_class=PacketValidation, 
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0",
                       emulator_ip_block_id="packet_validation",
                       emulator_id="vcc-emulator-1")

    harness.add_device(device_name="test/wfs/1", 
                       device_class=WidebandFrequencyShifter, 
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0",
                       emulator_ip_block_id="wideband_frequency_shifter",
                       emulator_id="vcc-emulator-1")
    
    harness.add_device(device_name="test/wib/1", 
                       device_class=WidebandInputBuffer, 
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="1",
                       emulation_mode="0",
                       emulator_ip_block_id="wideband_input_buffer",
                       emulator_id="vcc-emulator-1",
                       health_monitor_poll_interval="1"
                       )

    
    harness.add_device(device_name="test/vccallbands/1", 
                       device_class=VCCAllBandsController, 
                       device_id="1",
                       device_version_num="1.0",
                       device_gitlab_hash="abc123",
                       config_location="../../resources/",
                       simulation_mode="0",
                       emulation_mode="1",
                       mac_200_fqdn="test/mac200/1",
                       packet_validation_fqdn = "test/packet_validation/1",
                      vcc123_channelizer_fqdn ="test/vcc123/1",
                      vcc45_channelizer_fqdn = "vcc45", 
                      wideband_input_buffer_fqdn = "test/wib/1",
                      wideband_frequency_shifter_fqdn = "test/wfs/1",
                      circuit_switch_fqdn = "cs",
                      fs_selection_fqdn = "test/fss/1")

    with harness as test_context:
        yield test_context

def test_init(device_under_test):
    state = device_under_test.state()
    assert state == DevState.ON
    
def test_adminMode_online(device_under_test):
    
    prevAdminMode = device_under_test.read_attribute('adminMode')
    
    device_under_test.write_attribute('adminMode', 0)
    
    adminMode = device_under_test.read_attribute('adminMode')
    
    assert adminMode.value == AdminMode.ONLINE.value
        
# def test_configure(device_under_test):
#     invalid_json = '{"config_id":"1","expected_dish_id":"MKT005","dish_sample_rate":3960000000,"samples_per_frame":18,"vcc_gain":[1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],"frequency_band":"1","noise_diode_transition_holdoff_seconds":65536,"frequency_band_offset_stream_1":55.0,"frequency_band_offset_stream_2":0.0}'
#     valid_json = '{"config_id":"1","expected_dish_id":"MKT001","dish_sample_rate":3960000000,"samples_per_frame":18,"vcc_gain":[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],"frequency_band":"2","fsp":[{"fsp_id":1,"frequency_slice_id":1,"function_mode":"CORR"},{"fsp_id":4,"frequency_slice_id":4,"function_mode":"CORR"},{"fsp_id":2,"frequency_slice_id":2,"function_mode":"CORR"},{"fsp_id":3,"frequency_slice_id":3,"function_mode":"CORR"}],"noise_diode_transition_holdoff_seconds":0,"frequency_band_offset_stream_1":110,"frequency_band_offset_stream_2":56}'
#     result = device_under_test.command_inout("ConfigureScan", invalid_json)

#     time.sleep(10)
    
#     result = device_under_test.command_inout("ConfigureScan", valid_json)
    
#     time.sleep(10000)
    