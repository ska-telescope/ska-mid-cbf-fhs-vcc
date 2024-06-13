#ifndef VCC_H
#define VCC_H

#include <cstdint>
#include <stdexcept>
#include <iostream>
#include <string>
#include <vector>
#include <cmath>
#include <algorithm>

struct Config {
    uint32_t sample_rate = 3963619800;   // 0 = no-config
    uint8_t  pol = 0;                    // valid 0 = 'X', 1 = 'Y'
    uint16_t channel = 0;                // valid 0 to num_channels-1
    uint32_t input_frame_size = 18;
    float    gain = 1.0;
};

struct Status {
    uint32_t sample_rate;
    int      num_channels;
    int      num_polarisations;
    std::vector<float> gains;   // Array of gains with size num_channels*num_polarisations
};

class VCC_20 {
private:
    uintptr_t base_address;
    std::string name;
    
    // Define register address offsets:
    static const uintptr_t config_pps_frame_count_addr_offset;
    static const uintptr_t config_fs_sft_scl_addr_offset;

    // Define field offsets within the config_fs_sft_scl register:
    static const uint32_t fs_sft_bit_offset;
    static const uint32_t fs_scl_bit_offset;

    static const uint32_t channels_out;

public:
    VCC_20(const std::string& init_name, uintptr_t base_addr);

    void registerWrite(uintptr_t addr, uint32_t value);

    uint32_t registerRead(uintptr_t addr);

    void recover();

    void configure(const Config& config);

    void start();

    void stop(bool force = false);

    void deconfigure(Config config);

    void status(bool clear, Status& status);

};

#endif // VCC_H