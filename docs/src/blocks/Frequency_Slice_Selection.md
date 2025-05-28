# Frequency Slice Selection

The Freqency Slice Selection module is implemented as 2:1 muxes, that connects the VCC channelizers to the outputs.

It has 10 inputs from the B123_Channelizer and 15 inputs each from the two B45 Channelizers. These 40 inputs are selected to 26 outputs with some heavy restrictions.
1. select from either the B123_Channelizer, OR the B45 Channelizers.
2. select the range of channels from the B45 Channelizers.

## Data Path Interface
The datapath transports streams of complex samples. Selecting which of two possible inputs goes to an output.

### Input
40 input streams of type `T`.
.
### Output
26 output streams of type `T`.

## Low Level Driver API
### Structs
#### `struct config`
- band_select: int, range 1 to 5;
- band_start_channel : int[2], range 0 to 2;

#### `struct status`
return the same as struct config.

### Standard methods
#### `Constructor()`
- Set identity (name, address)

#### `recover()`
- clear all configured output routes to default = band1.

#### `configure(struct config)`
- update mux values according to config.
- setting takes immediate effect.

#### `start()`
- null

#### `stop()`
- null

#### `deconfigure(struct config)`
- recover()

#### `status(clear: bool, struct &status)`
- read registers and determine what configuration is applied.
- populate status struct
  