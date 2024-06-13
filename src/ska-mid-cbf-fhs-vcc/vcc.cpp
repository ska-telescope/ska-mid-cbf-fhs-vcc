#include "vcc.h"
#include <cmath>
#include <algorithm>

const uintptr_t VCC_20::config_pps_frame_count_addr_offset = 0x0;
const uintptr_t VCC_20::config_fs_sft_scl_addr_offset = 0x4;
const uint32_t VCC_20::fs_sft_bit_offset = 0;
const uint32_t VCC_20::fs_scl_bit_offset = 4;
const uint32_t VCC_20::channels_out = 10;

// Constructor to initialize name, base address
VCC_20::VCC_20(const std::string& init_name, uintptr_t base_addr) : 
    name(init_name), base_address(base_addr) {
}

void VCC_20::registerWrite(uintptr_t addr, uint32_t value) {
    *(volatile uint32_t*)(addr) = value;
}

uint32_t VCC_20::registerRead(uintptr_t addr) {
    uint32_t value = *(volatile uint32_t*)(addr);
    return value;
}

void VCC_20::recover() {
    // Create a default Config instance:
    Config config;

    // Set default expected sample rate (in default config), set all gains to default (1.0):
    for (uint8_t pol = 0; pol < 2; pol++) {
        for (uint16_t channel = 0; channel < 10; channel++) {
            config.channel = channel;
            config.pol = pol;
            configure(config);
        }
    }
}

void VCC_20::configure(const Config& config) {
    std::cout << "Configuring VCC " << name << " with sample_rate: " << config.sample_rate
            << ", pol: " << static_cast<int>(config.pol)
            << ", channel: " << config.channel
            << ", gain: " << config.gain << std::endl;

    // Set expected sample rate by writing to frame_count register:
    registerWrite(base_address + config_pps_frame_count_addr_offset, config.sample_rate / config.input_frame_size);

    // Set gain for one (pol, channel):
    // Calculate the shift and scale values to write to the config_fs_sft_scl register:
    float intrinsic_gain = 1.0 / (0.9475 * std::sqrt(2 * VCC_20::channels_out));
    // float intrinsic_gain = 1.0 / (0.9475 * std::sqrt(20.0f));        // maybe have to do this
    float comb_gain = config.gain / intrinsic_gain;
    uint32_t int_gain = std::clamp(static_cast<uint32_t>(std::ceil(std::log2(comb_gain))), 0U, 32767U);
    uint16_t shift = static_cast<uint16_t>(std::log2(int_gain));
    uint16_t scale = static_cast<uint16_t>((comb_gain / int_gain) * 65535);

    // Calculate the (pol, channel) index:
    uint32_t index = config.channel + config.pol * VCC_20::channels_out;

    // Write shift, scale values to frequency slice config register:
    uintptr_t w_addr = base_address + config_fs_sft_scl_addr_offset + index * 4;
    uint32_t w_val = ((shift & 0xF) << fs_sft_bit_offset) | ((scale & 0xFFFF) << fs_scl_bit_offset);
    registerWrite(w_addr, w_val);
}

void VCC_20::start()
{
    // Do nothing
}

void VCC_20::stop(bool force = false)
{
    //Do nothing
}


void VCC_20::deconfigure(Config config) {
    // Set gain to default (1.0) for one (pol, channel):
    std::cout << "Deconfiguring VCC " << name << " for channel: " << config.channel << ", pol: " << config.pol << std::endl;
    config.gain = 1.0f;

    configure(config);
}

void VCC_20::status(bool clear, Status& status) {
    // Return the sample rate and gains
    uintptr_t r_addr;
    uint32_t r_val;

    // Loop through register fields
    for (uint8_t pol = 0; pol < 2; pol++) {
        for (uint16_t channel = 0; channel < 10; channel++) {
            r_addr = base_address + config_fs_sft_scl_addr_offset + (channel + pol * VCC_20::channels_out) * 4;
            r_val = registerRead(r_addr);
            
            // Parse shift and scale values from the register
            uint16_t shift = (r_val >> fs_sft_bit_offset) & 0xF;
            uint16_t scale = (r_val >> fs_scl_bit_offset) & 0xFFFF;

            // Reverse the configure() calculations to get gain for this channel, pol:
            float int_gain = 1 << shift;
            float comb_gain = (scale / 65535.0f) * int_gain;
            float intrinsic_gain = 1.0f/(0.9475f * std::sqrt(2 * VCC_20::channels_out));
            // float intrinsic_gain = 1.0f/(0.9475f * std::sqrt(20.0f));
            float gain = comb_gain * intrinsic_gain;

            status.gains[channel + pol * 10] = gain;

            std::cout << "Read shift: " << shift << ", scale: " << scale
                      << ", calculated gain: " << gain << " for channel: " << channel 
                      << ", pol: " << static_cast<int>(pol) << std::endl;
        }
    }

    uint32_t frame_count_addr = base_address + config_pps_frame_count_addr_offset;
    uint32_t frame_count = registerRead(frame_count_addr);
    status.sample_rate = frame_count * 18;

    std::cout << "Read frame_count: " << frame_count << ". "
              << "Calculated sample_rate: " << status.sample_rate << std::endl;

}