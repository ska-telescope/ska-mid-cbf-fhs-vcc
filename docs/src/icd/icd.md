# FHS-VCC All Bands Controller - ICD MCS to FHS-VCC
### Overview
This document serves as the internal ICD between MCS and the FHS-VCC. The FHS-VCC All Bands Controller provides the control layer between MCS and the subordinate FHS-VCC devices. Implemented as a Tango Device server using the 1.0.0+ version of the ska-tango-base classes.
### Scenario Diagram 
![alt text](../diagrams/VCC-scenario-diagram.png "Title")
### Device Attributes

| Name                  | Type                      | Read/Write | Description                                                                                                                                                  |
| --------------------- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `dishId`             | DevString                 | R        | Associated dish identifier                                                                                                                                   |
| `vccGains`           | `Array<Tango::DevDouble>` | R          | Read attribute for gain values                                                                                                                               |
| `frequencyBand`       | DevEnum                   | R          | Frequency band that is currently configured                                                                                                                  |
| `configID`            | DevString                 | R          | Identifier of the current scan configuration                                                                                                                 |
| `scanID`              | DevULong                  | R          | Identifier of the current scan                                                                                                                               |
| `inputSampleRate`     | DevULong64                | R          | Input sample rate read attribute                                                                                                                             |
| `frequencyBandOffset` | DevLong[2]                | R          | Frequency band offset, received during scan configuration<br><br>Length 2 since band 5 needs two values specified, other bands will only use the first value |


#### Device Properties
| Name                           | Type      | Description                                                                                                              | Length |
| ------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------ | ------ |
| `vcc12ChannelizerFQDN`        | DevString | Fully Qualified Domain name (FQDN) for the 1 & 2 OSPPFB Channelizer lower level device                                  |        |
| `vcc45ChannelizerFQDN`         | DevString | FQDN for the 5A/B OSPPFB Channelizer lower level device                                                                   |        |
| `fsSelectionFQDN`              | DevString | FQDN for the FS Selection lower level device                                                                             |        |
| `widebandFrequencyShifterFQDN` | DevString | FQDN for Wideband Frequency Shifter lower level device                                                                   |        |
| `widebandInputBufferFQDN`      | DevString | FQDN for Wideband Frequency Input Buffer lower level device                                                              |        |
| `macFQDN`                      | DevString | FQDN for Ethernet Media Access Control (MAC) lower level device likely only needed for testing purposes in loopback mode |        |
### Commands
| Name              | Input Type  | Input Parameter                    | Allowed in modes      | Description                                                                                                                                                                                                      |
| ----------------- | ----------- | ---------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Abort()`         | void        | n/a                                | IDLE, READY, SCANNING | Sets the device state to ABORTED and aborts all running/queued commands                                                                                                                                          |
| `ConfigureScan()` | JSON String | See below.                         | IDLE, READY           | Configure parameters for the next scan(s). Parameters are propagated down to low-level device servers. Sets the state to CONFIGURING, if the inputted JSON can be successfully parsed the state is set to READY. |
| `EndScan()`       | void        | n/a                                | SCANNING              | Completes the scan and changes the device back to the READY state.                                                                                                                                               |
| `GoToIdle()`      | void        | n/a                                | READY                 | Resets the device and changes the state to IDLE                                                                                                                                                                  |
| `ObsReset()`      | void        | n/a                                | ABORTED, FAULT        | Reset the observing device from a FAULT/ABORTED obsState to IDLE. Initially sets the state to RESETTING, resets the configuration of the device to the default and then sets the state to IDLE on completion.    |
| `Scan()`          | String      | The identifier of the current scan | READY                 | Start the scan using the last set of parameters passed via the `ConfigureScan()` command. The state is then set to SCANNING.                                                                                     |
### Command Parameter Definitions
#### `ConfigureScan()`
##### Parameters
| Name                                   | Type                                                                   | Description                                                                                                                                    | Range                                              |
| -------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `config_id`                            | string                                                                 | Identifier of the current scan configuration                                                                                                   |                                                    |
| `frequency_band`                       | string                                                                 | Frequency band for the current scan                                                                                                            | ("1","2","5a","5b")                                |
| `frequency_band_offset_stream_1`       | long                                                                   | See `frequencyBandOffset` attribute description                                                                                                | abs(value) MHz < Frequency Slice Bandwidth MHz / 2 |
| `frequency_band_offset_stream_2`       | long                                                                   | See `frequencyBandOffset` attribute description                                                                                                | abs(value) < Frequency Slice Bandwidth / 2         |
| `fsp`                                  | Array of JSON Objects (**FSPDescriptors**)                             | Requires a list of FSPs to configure the Frequency Slice Selector (FSS) to stream the relevant Frequency Slice to it’s matching FSP            |                                                    |
| `band_5_tuning or stream_tuning`       | Array of Floats                                                        | Center frequency for the band-of-interest. Required if band is 5a or 5b; not specified for other bands                                         | 5A: 5.85 to 7.25 GHz  <br>5B: 9.55 to 14.05 GHz    |
| `samples_per_frame`                    | uint32_t                                                               | Samples per frame used to determine the frame count                                                                                            |                                                    |
| `noise_diode_transition_holdoff_count` | float                                                                  | Number of sample frames that indicates the worst case state transition in the event of packet loss/corruption within the Wideband Input Buffer | 0 to 65535                                         |
| `dish_sample_rate`                     | uint64_t                                                               | Dish sample rate factoring in the frequency band and the freq_offset_k                                                                         | 3,960,001,800 to 11,891,998,800                    |
| `vcc_gain`                             | Array of DevDouble (size = `num_vcc_channels_` * `num_polarizations_`) | Specifies the gain of each channel in the VCC                                                                                                  |                                                    |

**FSP Descriptors Attribute Definition**:

| Name                 | Type   | Description                        |
| -------------------- | ------ | ---------------------------------- |
| `fsp_id`             | string | Identifier of the FSP              |
| `frequency_slice_id` | string | Identifier of the frequency slice  |

#### `Scan()`
##### Parameters
| Name     | Type   | Description                    |
| -------- | ------ | ------------------------------ |
| `scan_id` | string | Identifier of the current scan |

#### `GoToIdle()` 
##### Parameters
n/a
#### `EndScan()`
##### Parameters
n/a

#### `Abort()`
##### Parameters
n/a

#### `ObsReset()`
##### Parameters
n/a

### Design decisions
1. On the new Agilex architecture switching frequency bands for a VCC can be done by partial reconfiguration of the FPGA board, the previous design had a top level device controller and a device per band, with it now being easier to switch bands that design can be simplified to have one top level device per VCC. Thus for this ICD the functionality between what was previously the DS-VCC-Controller and the DSVccBand1and2 has been merged. The main function merger was  between the `ConfigureBand()` and the `SetInternalParameters()` functions, both of which were called in close sequence by the control software but, were previously on different devices servers. The attributes for both are now shared.
2. Also the need for a VCC base class has also been reduced at the top level therefore the attributes are merged into the one core class.
3. Following design decisions made for MCS, setting `AdminMode = ONLINE` will be utlized to handle previous `On()` command functionality and setting `AdminMode = OFFLINE` will be used to handle the functionality of the previously implemented `Disable()` command.
4. Implementation specific comments:
- All commands apart from power-related On/Off commands will be implemented as fast commands
- By implementing with PyTango it should allow the removal of the MCS VCC device, this will require changes to the MCS subarray device as commands will have to be changed to target the FHS device. Also threads will have to be allocated within the device to accomodate long runnning commands across multiple VCCs