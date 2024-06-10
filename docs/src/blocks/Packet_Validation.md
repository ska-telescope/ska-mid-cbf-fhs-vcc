# Packet Validation

Processes packets from the ethernet interface and filters out packets that do not match the expected ethertype field. This should be none in a production system where the ethernet is a point to point link with a DISH, however in a test setup it may be connected to a switch so may receive unexpected packets from the wider network.

The Validator will also collect information from the dish packet headers and make them available to higher level software to vaildate.


## Data Path Interface

### Input
- Stream of packets

### Output
- Stream of packets that match the expected ethertype (`0xFEED`).

## Low Level Driver API
### Structs
#### `struct config`
- none? 

#### `struct status`
- packet_crc_error_count : uint32_t
- packet_ethertype_error_count : uint32_t
- packet_seq_error_count : uint32_t
- meta_frame -- Perhaps more general to just capture the headers (first 128 bytes or so) and make that avialable for SW decode.
  - ethertype : unit16_t 
  - band_id : uint8_t
  - sample_rate : uint64_t
  - dish_id : uint16_t
  - time_code : uint32_t
  - hardware_id : uint64_t

### Standard methods
#### `Constructor()`
- Set identity (name, address)
- Constants retrievable from registers. _Emulator will need to specify this somehow in its bitstream configuration_.
  - expected_ethertype = `0xFEED`

#### `recover()`
- enable reset.

#### `configure(struct config)`
- None

#### `start()`
- enable reception (stop dropping all packets). Activates on next PPS received.

#### `stop()`
- disable reception. Stops on next PPS received (excluding the PPS packet).

#### `deconfigure(struct config)`
- None

#### `status(clear: bool, struct &status)`
- populate the status struct:
    - meta_frame captured from the same and most recent packet.
- optionally clear the counters.