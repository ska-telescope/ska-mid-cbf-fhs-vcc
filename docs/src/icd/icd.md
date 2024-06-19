## FHS-VCC top level device - ICD (DRAFT)

### Design decisions:
On the new Agilex architecture switching band device for a VCC can be done without reimaging, with that in mind the need for a VCC controller that has many Band devices is not required. Thus for this ICD the functionality between what was previously the DS-VCC-Controller and the DSVccBand1and2 has been merged namely the `ConfigureBand()` merged with the `SetInternalParameters()` function as they were called in close sequence by the control software and attributes for both are now shared.

Also the need for a VCC base class has also been reduced at the top level therefore the attributes are merged into the one core class. The need for inheritance may be occur for a base class for channelizer devices and composition when the PSS is further explored.
### Device Attributes
Potentially not required = (?)

| Name                           | Type                                                                                                                                                        | Read/Write | Description                                                                                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `num_vcc_channels`(?)          | uint8_t                                                                                                                                                     | W          | Number of 220MHz frequency slice channels produced for the VCC in Bands 1,2 & 3 `n=10` and for Bands 4&5 `n=15`                                              |
| `num_polarizations` (?)        | uint8_t                                                                                                                                                     | W          | Number of Polarizations                                                                                                                                      |
| `num_vcc_gains` (?)            | uint8_t                                                                                                                                                     | W          | Number of gains values required for the number of channels relative to the number of polarization:  `num_vcc_channels * num_polarizations`                   |
| `vcc_gains`                    | `Array<Tango::DevDouble>`                                                                                                                                   | R          | Read attribute for gain values                                                                                                                               |
| `sample_rate_` (?)             | uint64_t                                                                                                                                                    | W          | Input sample rate in GSPS. Used to determine the frame count                                                                                                 |
| `samples_per_frame_` (?)       | uint32_t                                                                                                                                                    | W          | Samples per frame used to determine the frame count                                                                                                          |
| `frequencyBand`                | DevEnum                                                                                                                                                     | R          | Frequency band that is currently configured                                                                                                                  |
| `configID`                     | DevString                                                                                                                                                   | R          | Identifier of the current scan configuration                                                                                                                 |
| `scanID`                       | DevULong                                                                                                                                                    | R          | Identifier of the current scan                                                                                                                               |
| `inputSampleRate`              | DevULong64                                                                                                                                                  | R          | Input sample rate read attribute                                                                                                                             |
| `frequencyBandOffset`          | DevLong[2]                                                                                                                                                  | R          | Frequency band offset, received during scan configuration<br><br>Length 2 since band 5 needs two values specified, other bands will only use the first value |
| `obsState`                     | DevEnum<br>- EMPTY<br>- RESOURCING<br>- IDLE<br>- CONFIGURING<br>- READY<br>- SCANNING<br>- ABORTING<br>- ABORTED<br>- RESETTING<br>- FAULT<br>- RESTARTING | R          | Observing state                                                                                                                                              |
| `vcc123ChannelizerFQDN`        | DevString                                                                                                                                                   | R          | Fully Qualified Domain name (FQDN) for the 1,2& 3 OSPPFB Channelizer lower level device                                                                      |
| `vcc45ChannelizerFQDN`         | DevString                                                                                                                                                   | R          | FQDN for the 4&5 OSPPFB Channelizer lower level device                                                                                                       |
| `fsSelectionFQDN`              | DevString                                                                                                                                                   | R          | FQDN for the FS Selection lower level device                                                                                                                 |
| `widebandFrequencyShifterFQDN` | DevString                                                                                                                                                   | R          | FQDN for Wideband Frequency Shifter lower level device                                                                                                       |
| `widebandInputBufferFQDN`      | DevString                                                                                                                                                   | R          | FQDN for Wideband Frequency Input Buffer lower level device                                                                                                  |

### Functions
#### `ConfigureScan()`
 Configure parameters for the next scan(s). Parameters are propagated down to low-level device servers. Sets the state to CONFIGURING, if the inputted JSON can be successfully parsed the state is set to READY.
##### Parameters:

| name                             | type                                                                                 | description                                                                                                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config_id`                      | string                                                                               | Identifier of the current scan configuration                                                                                                                  |
| `frequency_band` (?)             | string                                                                               | May not be REQUIRED as it's should have been set by `ConfigureBand()` prior                                                                                   |
| `frequency_band_offset_stream_1` | long                                                                                 | See `frequencyBandOffset` attribute description                                                                                                               |
| `frequency_band_offset_stream_2` | long                                                                                 | See `frequencyBandOffset` attribute description                                                                                                               |
| `fsp`                            | `FSPDescriptor[]{fsp_id: string, frequency_slide_id: string, function_mode: string}` | Requires a list of FSPs to configure the Frequency Slice Selector (FSS) to stream the relevant Frequency Slice to it's matching FSP via the `fsp.id` with FSS |
| `band_5_tuning or stream_tuning` | Array of Floats                                                                      | Center frequency for the band-of-interest. Required if band is 5a or 5b; not specified for other bands                                                        |
| `rfi_flagging_mask`              | placeholder                                                                          |                                                                                                                                                               |

#### `Scan()`
**Description**: Start the scan using the last set of parameters passed via the `ConfigureScan()` command. The state is then set to SCANNING.
##### Parameters:
| Name     | Type   | Description                    |
| -------- | ------ | ------------------------------ |
| `scanId` | string | Identifier of the current scan |

#### `ConfigureBand()`
**Description**: Configure the VCC device for a specific band and connect to the relevant lower level devices specifically the relevant band channelizer. Sets the state to ON.
##### Parameters

| name                | type                                                                   | description                                                                                                                     |
| ------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `frequency_band`    | DevEnum ${0 < band =< 5}$                                              | Frequency band to configure the VCC.<br><br>Mapping:<br>- 0 = Band 1<br>- 1 = Band 2<br>- ...<br>- 4 = Band 5a<br>- 5 = Band 5b |
| `dish_sample_rate`  | int                                                                    | Dish sample rate factoring in the frequency band and the freq_offset_k                                                          |
| `samples_per_frame` | int                                                                    | Samples per data frame relative to the frequency band                                                                           |
| `vcc_gain`          | Array of DevDouble (size = `num_vcc_channels_` * `num_polarizations_`) | Specifies the gain of each channel in the VCC                                                                                   |
#### `On()`
**Description**: Sets the device state to ON
##### Parameters:
n/a
#### `Unconfigure()` 
**Description**: Resets the device and changes the state to IDLE.
No parameters
##### Parameters:
n/a
#### `EndScan()`
**Description**: Completes the scan and changes the device back to the READY state.
##### Parameters:
n/a

#### `Disable()`
**Description**: Sets the device state to DISABLE
##### Parameters:
n/a

