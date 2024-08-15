# Wideband Frequency Shifter

This block applies a shift in frequency to the wideband signal of nominally up to +/- a half of the frequency slice bandwidth (-100MHz to +100MHz). This allows a particlar frequency, such as the start of a band, to be aligned with the start of a frequency slice - thus minimising the number of frequency slices required to cover the band's full bandwidth.

This is achieved my multiplying the signal with a sine wave.

## Data Path Interface
When samples are applied, they will drive the generation of a sine wave (using a numerically controlled oscillator). The sine wave will be multiplied with the samples and output.

### Input

* Receives complex valued samples
* with an input sample rate of approximately 3.96e9 samples per second.
* there are two polarisations, X and Y, (the samples are interleaved).

### Output

Same as the input.

## Low Level Driver API
### Structs
#### `struct config`
- shift_frequency : float

#### `struct status`
- shift_frequency : float

### Standard methods
#### `Constructor()`
- Set identity (name, address)

#### `recover()`
- set shift frequency back to default = 0.0 Hz.

#### `configure(struct config)`
Applied immediately.
- set the configured frequency shift.

#### `start()`
- null

#### `stop()`
- null

#### `deconfigure(struct config)`
- set shift frequency back to default = 0.0 Hz.

#### `status(clear: bool, struct &status)`
- populate the status struct:
  - read back the frequency shift.