.. doctest-skip-all
.. _B123VCC-OSPPFB_Channeliser:

.. todo::
    - Insert todo's here

B123VCC-OSPPFB Channeliser 
###########################


This block is an oversampling polyphase filter bank (OSPPFB). It breaks a 'wideband' signal into multiple (e.g. 10) channels each representing an equal proportion of the input spectrum. 

The `oversampling_factor` (e.g. 10/9). This means that the total bandwidth out is (e.g. 1.1111 times) more than the input. The transition bands (where the filter frequency response transitions from the stop band to the pass band) of a output channels' spectrum, overlaps with the pass band of the adjacent channel. This allows the recover of the full bandwidth across the "frequency slices", ignoring the transition bands.

Data Path Interface
*******************

Input
=====

* receives complex valued samples
* with an input sample rate of approximately 3.96e9 samples per second.
* input sample rate must be a multiple of 18.
* there are two polarisations, X and Y, (the samples are interleaved).

Output
======

* 10 parallel complex valued streams. `number_of_output_streams = 10`
* each output stream
* `output_sample_rate = input_sample_rate * oversampling_factor / number_of_output_streams / 2`. This is approximately 220e6 samples per second.
* dual polarisation output (interleaved).
* complex values.

Behaviour
=========
Channeliser is always running (has no external reset). Samples input generate samples out at the output sample rate (according to the input sample rate). Since it is oversampling the aggregate output rate across all outputs is more than the input rate.

If the input sample rate is not the same as the expected sample rate, then the output samples are 'flagged' as invalid.

* The expected number of samples is provided by a FW register. The default expected sample rate is 3.96e9. This should be configured by the control software to match the sample rate expected from the receptor upstream.
* FW block determines the received sample rate by counting samples between PPS inputs.

  * It must see two PPS inputs, with the correct number of samples between, for it to output correct (non-flagged) samples.

If an input sample is flagged then X samples at the output are flagged, X/2 before and X/2 after. Where X is TBD (on the order of 20).

The last stage of the channeliser FW applies a gain value to the output samples on a per channel, and per polarisation basis (20 different gains).

* If that gain causes the output sample's value to saturate (-1.0 \<= sample \<=  1.0) then the sample is flagged.
 
Common Terms
------------
* 'sample'
  * one value of data - usually complex (real and imaginary).
  * values usually look gaussian distributed, with a mean of 0, and standard deviation.
  * has a precision in bits - usually fixed-point and less than 18b.
  * has an associated timestamp. This timestamp is represented as a count of samples since some epoch at the current sample rate. Will be a big number - u_int64_t.
  * has a PPS (pulse per second) marker - marks the first sample at the start of a new second.
  * has an associated flag (see 'flagged')
  * is part of a 'stream' with an associated sample rate. This sample rate is guaranteed to be an integer number of samples per second. 

* 'flagged'
  * sample is valid, but contains questionable data.
  * samples maintain the timing, but their flag is contagious. If used in signal processing, any samples that are calculated using a flagged sample are also flagged. For example in a FIR filter of length 15, The flagged sample will infect 15 other output samples (7 before and 7 after) as it moves through the FIR filter's delay line.
  * flagging is contagious between polarisations, if one polarisation is flagged, then both are flagged.

Low-level Driver API
====================

Structs
-------

`struct config`
^^^^^^^^^^^^^^^
- sample_rate : u_int32_t
	- zero = no-config
- pol: u_int8_t,  valid 0 = 'X', 1 = 'Y'
- channel : u_int16_t, valid 0 to num_channels-1
- gain: float32

`struct status`
^^^^^^^^^^^^^^^
- sample_rate : sample_rate : u_int32_t
- num_channels : int
- num_polarisations : int
- gains : array[num_channels * num_polarisations] config

Standard methods
----------------

`Constructor()`
^^^^^^^^^^^^^^^
- Set identity (name, address)

`recover()`
^^^^^^^^^^^
- Set gains to 1.0
- Set default expected sample rate.

`configure(struct config)`
^^^^^^^^^^^^^^^^^^^^^^^^^^

 - Set expected sample rate.
 - Set gain for one (pol, channel).

`start()`
^^^^^^^^^
	Do nothing

`stop(bool force = False)`
^^^^^^^^^^^^^^^^^^^^^^^^^^
	Do nothing

`deconfigure(struct config)`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Set gain to default (1.0)

`status(bool clear, struct &status)`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
	return sample rate and gains mapping.

