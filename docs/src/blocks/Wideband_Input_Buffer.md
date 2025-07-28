# Wideband Input Buffer

Purpose is to replace missing packets (dropped, or otherwise) with packets containing default data (flagged). The output word rate is maintained at a constant value so that downstream processing can minimise its buffer usage.

## Error Conditions
- If the output sample rate is lower than the input sample rate (from packets) the buffer will overflow. 
- If the output sample rate is greater than the input sample rate (from packets) then the buffer will underflow. If this condition persists for more than 1 second, then the number of seconds is counted and reported as loss of signal. 

## Data Path Interface

### Input
- Stream of packets

### Output
- Stream of samples at the wideband sample rate.

## Low Level Driver API
### Structs
#### `struct config`
- expected_sample_rate : uint64_t
- noise_diode_transition_holdoff_seconds : float

#### `struct status`
- link_failure : boolean
- buffer_overflow : boolean
- loss_of_signal_seconds : uint32_t
- band_id : unit8_t

### Standard methods
#### `Constructor()`
- Set identity (name, address)

#### `recover()`
- enable reset.

#### `configure(struct config)`
- compute register values from `config`

#### `start()`
- enable processing. Activates on next PPS received.

#### `stop()`
- disable processing. Stops on next PPS received (excluding the PPS packet).

#### `deconfigure(struct config)`
- None

#### `status(clear: bool, struct &status)`
- populate the status struct:
    - meta_frame captured from the same and most recent packet.
- optionally clear the counters.