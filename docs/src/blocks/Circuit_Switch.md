# Circuit Switch

A circuit switch is used to select one of $N$ inputs to be copied to one or more of $M$ outputs. The selection is controlled by register, and is static (i.e. not packet switched).

The values of $N$ and $M$ are positive integers greater or equal to 1.

This is a fairly generic component. It simply copies an input to an output. An output can only get data from a single input.

Different outputs can get data from the same input at the same time: duplicating a stream.

## Data Path Interface
The datapath transports streams of data of a generic type `T`. 
Where `T` could be complex sample streams (as in the VCC), or packet streams (in visibility transport) as two examples.

### Input
$N$ input streams of type `T`.
.
### Output
$M$ output streams of type `T`.

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
- populate the status struct:
  - for each stream in "number of outputs":
    - return the input.