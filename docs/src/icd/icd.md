# ICD (WIP)
Potentially not required = (?)
### Device Attributes
| Name                           | Type                                                                                                                                                        | Read/Write | Description                                                                                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `num_vcc_channels`(?)          | uint8_t                                                                                                                                                     | W          | Number of 220MHz frequency slice channels produced for the VCC in Bands 1,2 & 3 `n=10` and for Bands 4&5 `n=15`                                              |
| `num_polarizations` (?)        | uint8_t                                                                                                                                                     | W          | Number of Polarizations                                                                                                                                      |
| `num_vcc_gains` (?)            | uint8_t                                                                                                                                                     | W          | Number of gains values required for the number of channels relative to the number of polarization:  `num_vcc_channels * num_polarizations`                   |
| `vcc_gains`                    | `Array<Tango::DevDouble>`                                                                                                                                   | R          | Read attribute for gain values                                                                                                                               |
| `sample_rate_` (?)             | uint64_t                                                                                                                                                    | W          | Input sample rate in GSPS. Used to determine the frame count                                                                                                 |
| `samples_per_frame_` (?)       | uint32_t                                                                                                                                                    | W          | Samples per frame used to determine the frame count                                                                                                          |
| `frequencyBand`                |                                                                                                                                                             | R          | Frequency band that is currently configured                                                                                                                  |
| `configID`                     |                                                                                                                                                             | R          | Identifier of the current scan configuration                                                                                                                 |
| `scanID`                       |                                                                                                                                                             | R          | Identifier of the current scan                                                                                                                               |
| `inputSampleRate`              |                                                                                                                                                             | R          | Input sample rate read attribute                                                                                                                             |
| `frequencyBandOffset`          | DevLong[2]                                                                                                                                                  | R          | Frequency band offset, received during scan configuration<br><br>Length 2 since band 5 needs two values specified, other bands will only use the first value |
| `obsState`                     | DevEnum<br>- EMPTY<br>- RESOURCING<br>- IDLE<br>- CONFIGURING<br>- READY<br>- SCANNING<br>- ABORTING<br>- ABORTED<br>- RESETTING<br>- FAULT<br>- RESTARTING | R          | Observing state                                                                                                                                              |
| `vcc123ChannelizerFQDN`        | string                                                                                                                                                      |            |                                                                                                                                                              |
| `vcc45ChannelizerFQDN`         | string                                                                                                                                                      |            |                                                                                                                                                              |
| `fsSelectionFQDN`              | string                                                                                                                                                      |            |                                                                                                                                                              |
| `widebandFrequencyShifterFQDN` | string                                                                                                                                                      |            |                                                                                                                                                              |
| `widebandInputBufferFQDN`      | string                                                                                                                                                      |            |                                                                                                                                                              |

### Functions
#### `ConfigureScan()`
 Configure parameters for the next scan(s). Parameters are propagated down to low-level device servers.
##### Parameter Table
| name                                                                      | type            | description                                                                                                                                                   |
| ------------------------------------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config_id`                                                               | string          | Identifier of the current scan configuration                                                                                                                  |
| `frequency_band`                                                          |                 |                                                                                                                                                               |
| `frequency_band_offset_stream_1`                                          | long            |                                                                                                                                                               |
| `frequency_band_offset_stream_2`                                          | long            |                                                                                                                                                               |
| `fsps{fsp_id: string, frequency_slide_id: string, function_mode: string}` | FSPDescriptor[] | Requires a list of FSPs to configure the Frequency Slice Selector (FSS) to stream the relevant Frequency Slice to it's matching FSP via the `fsp.id` with FSS |
| `band_5_tuning or stream_tuning`                                          | Array of Floats | Center frequency for the band-of-interest. Required if band is 5a or 5b; not specified for other bands                                                        |
| `rfi_flagging_mask`                                                       | placeholder     |                                                                                                                                                               |

#### `Scan()`
Start the scan using the last set of parameters passed via the ConfigureScan command. The state set to SCANNING by this command.
##### Parameters:
| Name     | Type   | Description                    |
| -------- | ------ | ------------------------------ |
| `scanId` | string | Identifier of the current scan |

#### `ConfigureBand()`
Configure the VCC device for a specific band and connect to the relevant lower level devices specifically relevant band channelizer. 

**Design decision**:
`ConfigureBand()` on the Talon hardware was defined in the VCC Controller Device Server however, due to the shift on the Agilex whereby, the band can be changed without reimaging the FPGA the need for a separate device per band was reduced therefore, functionality per VCC between the controller and the previous band device have been merged. 

Therefore, `ConfigureBand()` has been moved into the single VCC class and merged with the pervious band function `SetInternalParameters()` function both of which were called by the control software previous in close sequence. 

| name                | type                                                                   | description                                                                                                                     |
| ------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `frequency_band`    | DevEnum ${0 < band =< 5}$                                              | Frequency band to configure the VCC.<br><br>Mapping:<br>- 0 = Band 1<br>- 1 = Band 2<br>- ...<br>- 4 = Band 5a<br>- 5 = Band 5b |
| `dish_sample_rate`  | int                                                                    | Dish sample rate factoring in the frequency band and the freq_offset_k                                                          |
| `samples_per_frame` | int                                                                    | Samples per data frame relative to the frequency band                                                                           |
| `vcc_gain`          | Array of DevDouble (size = `num_vcc_channels_` * `num_polarizations_`) | Specifies the gain of each channel in the VCC                                                                                   |

#### `Unconfigure()` 
Resets the device and changes the state to Unconfigured.

