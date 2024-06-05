# Frequency Slice Selection (Circuit Switch)

The circuit switch is used to select one of $N$ inputs to be copied to one or more of $M$ outputs. The selection is controlled by register, and is static (i.e. not packet switched).

No restrictions on $N$ or $M$.

It is a fairly generic component. Simply copies an input to an output. Any output can get data from any input - fully cross connected. Outputs can get data from the same input at the same time: duplicating a stream.
## Data Path Interface

### Input
$N$ input streams of whatever. All the same type. Could be sample streams (in the VCC), or packet streams (in visibility transport).

### Output
$M$ output streams, same type as input stream.

## Low Level Driver API
### Structs
#### `struct config`
- output: int, 
- input: int,

#### `struct status`
- num_inputs
- num_outputs
- connected : array\[num_outputs\] (struct cfg)
  - Negative input value == not connected.

### Standard methods
#### `Constructor()`
- Set identity (name, address)
- Constants retrievable from registers. _Emulator will need to specify this somehow in its bitstream configuration_.
  - "number_of_inputs"
  - "number_of_outputs"

#### `recover()`
- clear all configured output routes - no connect.

#### `configure(struct config)`
- connect`config.output` from `config.input`.
- Can call as many times as required. Connection made immediately.
- Multiple outputs can come from the same input. 
- One output may not come from multiple inputs. Error if attempting to connect a second input to an output.

#### `start()`
- null

#### `stop()`
- null

#### `deconfigure(struct config)`
- disconnect`config.output`
- Can call as many times as required. Disconnects immediately.

#### `status(clear: bool, struct &status)`
- for each lane in "number of outputs":
  - return the input.