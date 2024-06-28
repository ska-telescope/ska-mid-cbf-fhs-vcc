# VCC Controller - ICD
#### Diagram:
![alt text](../diagrams/VCC-scenario-diagram.png "Title")
#### Questions:
1. Are there any functions that need to be run at the VCC Unit level (6-VCCs) or at the level of FPGA encompassing 3-VCCs? Say any power switch actions
2. Not seeing a receptorID or a subarray attribute does that need to be added?
### Device Attributes

| Name                           | Type                      | Read/Write | Description                                                                                                                                                  |
| ------------------------------ | ------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `vcc_gains`                    | `Array<Tango::DevDouble>` | R          | Read attribute for gain values                                                                                                                               |
| `frequencyBand`                | DevEnum                   | R          | Frequency band that is currently configured                                                                                                                  |
| `configID`                     | DevString                 | R          | Identifier of the current scan configuration                                                                                                                 |
| `scanID`                       | DevULong                  | R          | Identifier of the current scan                                                                                                                               |
| `inputSampleRate`              | DevULong64                | R          | Input sample rate read attribute                                                                                                                             |
| `frequencyBandOffset`          | DevLong[2]                | R          | Frequency band offset, received during scan configuration<br><br>Length 2 since band 5 needs two values specified, other bands will only use the first value |


#### Device Constants
| Name                           | Type      | Description                                                                                                              | Length |
| ------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------ | ------ |
| `vcc123ChannelizerFQDN`        | DevString | Fully Qualified Domain name (FQDN) for the 1,2& 3 OSPPFB Channelizer lower level device                                  |        |
| `vcc45ChannelizerFQDN`         | DevString | FQDN for the 4&5 OSPPFB Channelizer lower level device                                                                   |        |
| `fsSelectionFQDN`              | DevString | FQDN for the FS Selection lower level device                                                                             |        |
| `widebandFrequencyShifterFQDN` | DevString | FQDN for Wideband Frequency Shifter lower level device                                                                   |        |
| `widebandInputBufferFQDN`      | DevString | FQDN for Wideband Frequency Input Buffer lower level device                                                              |        |
| `macFQDN`                      | DevString | FQDN for Ethernet Media Access Control (MAC) lower level device likely only needed for testing purposes in loopback mode |        |
### Commands
| Name              | Input Type  | Input Parameter                    | Allowed in modes | Description                                                                                                                                                                                                      |
| ----------------- | ----------- | ---------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ConfigureBand()` | JSON String | See below.                         |                  | Configure the VCC device for a specific band and connect to the relevant lower level devices specifically the relevant band channelizer. Sets the state to ON.                                                   |
| `ConfigureScan()` | JSON String | See below.                         |                  | Configure parameters for the next scan(s). Parameters are propagated down to low-level device servers. Sets the state to CONFIGURING, if the inputted JSON can be successfully parsed the state is set to READY. |
| `Scan()`          | String      | The identifier of the current scan |                  | Start the scan using the last set of parameters passed via the `ConfigureScan()` command. The state is then set to SCANNING.                                                                                     |
| `On()`            | void        | n/a                                |                  | Sets the device state to ON                                                                                                                                                                                      |
| `Unconfigure()`   | void        | n/a                                |                  | Resets the device and changes the state to IDLE                                                                                                                                                                  |
| `EndScan()`       | void        | n/a                                |                  | Completes the scan and changes the device back to the READY state.                                                                                                                                               |
| `Disable()`       | void        | n/a                                |                  | Sets the device state to DISABLE.                                                                                                                                                                                |
| `ObsReset()`      | void        | n/a                                |                  | Reset the observing device from a FAULT/ABORTED obsState to IDLE. Initially sets the state to RESETTING, resets the configuration of the device to the default and then sets the state to IDLE on completion.    |
### Command Parameter Definitions
#### `ConfigureScan()`
##### Parameters:

| name                               | type                                   | description                                                                                                                         |
| ---------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `config_id`                        | string                                 | Identifier of the current scan configuration                                                                                        |
| `frequency_band`                   | string                                 | Potentially NOT REQUIRED as it should have been set by `ConfigureBand()` command prior                                              |
| `frequency_band_offset_stream_1`   | long                                   | See `frequencyBandOffset` attribute description                                                                                     |
| `frequency_band_offset_stream_2`   | long                                   | See `frequencyBandOffset` attribute description                                                                                     |
| `fsp`                              | Array of JSON Objects (FSPDescriptors) | Requires a list of FSPs to configure the Frequency Slice Selector (FSS) to stream the relevant Frequency Slice to it's matching FSP |
| `band_5_tuning or stream_tuning`   | Array of Floats                        | Center frequency for the band-of-interest. Required if band is 5a or 5b; not specified for other bands                              |
| `sample_rate`                      | uint64_t                               | Input sample rate in GSPS. Used to determine the frame count                                                                        |
| `samples_per_frame`                | uint32_t                               | Samples per frame used to determine the frame count                                                                                 |
| `rfi_flagging_mask`                | placeholder                            | **Need input**                                                                                                                      |
| `NoiseDiodeTransitionHoldoffCount` | placeholder                            | **Need input**                                                                                                                      |

**FSP Descriptors Attribute Definition**:

| Name                 | Type   | Description                        |
| -------------------- | ------ | ---------------------------------- |
| `fsp_id`             | string | Identifier of the FSP              |
| `frequency_slice_id` | string | Identifier of the frequency slice  |
| `function_mode`      | string | Function mode of the specified FSP |

#### `Scan()`
##### Parameters:
| Name     | Type   | Description                    |
| -------- | ------ | ------------------------------ |
| `scanId` | string | Identifier of the current scan |

#### `ConfigureBand()`
##### Parameters

| name                | type                                                                   | description                                                                                                                     |
| ------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `frequency_band`    | DevEnum ${0 < band =< 5}$                                              | Frequency band to configure the VCC.<br><br>Mapping:<br>- 0 = Band 1<br>- 1 = Band 2<br>- ...<br>- 4 = Band 5a<br>- 5 = Band 5b |
| `dish_sample_rate`  | int                                                                    | Dish sample rate factoring in the frequency band and the freq_offset_k                                                          |
| `samples_per_frame` | int                                                                    | Samples per data frame relative to the frequency band                                                                           |
| `vcc_gain`          | Array of DevDouble (size = `num_vcc_channels_` * `num_polarizations_`) | Specifies the gain of each channel in the VCC                                                                                   |
#### `On()`
##### Parameters:
n/a
#### `Unconfigure()` 
##### Parameters:
n/a
#### `EndScan()`
##### Parameters:
n/a

#### `Disable()`
##### Parameters:
n/a

#### `ObsReset()`
##### Parameters:
n/a

### Design decisions:
1. On the new Agilex architecture switching frequency bands for a VCC can be done without reimaging the device, the previous design had a top level device controller and a device per band, with it now being easier to switch bands that design can be simplified to have one top level device per VCC. Thus for this ICD the functionality between what was previously the DS-VCC-Controller and the DSVccBand1and2 has been merged. The main function merger was  between the `ConfigureBand()` and the `SetInternalParameters()` functions, both of which were called in close sequence by the control software but, were previously on different devices servers. The attributes for both are now shared.
2. Also the need for a VCC base class has also been reduced at the top level therefore the attributes are merged into the one core class.
3. I decided not to merge the functionality between the `Unconfigure()` commands in the the Controller and the band device because that would mean setting the device state to `IDLE` and then immediately setting it to `DISABLE`. Therefore, the control software will have to additionally call disable if it wants to disable the VCC device in future.
