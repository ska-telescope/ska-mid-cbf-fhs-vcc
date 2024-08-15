# < BLOCK TITLE >

Description of function

## Data Path Interface
The datapath does what

### Input

### Output

## Low Level Driver API
### Structs
#### `struct config`
- member : type

#### `struct status`
- member : type

### Standard methods
#### `Constructor()`
- Set identity (name, address)
- Constants retrievable from registers. _Emulator will need to specify this somehow in its bitstream configuration_.
  - constant

#### `recover()`
- 

#### `configure(struct config)`
- 

#### `start()`
- null

#### `stop()`
- null

#### `deconfigure(struct config)`
- 

#### `status(clear: bool, struct &status)`
- populate the status struct:
  - 