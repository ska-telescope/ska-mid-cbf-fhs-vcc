# FHS-VCC Design

## Introduction

### Purpose

This page will describe the initial design and flow of the HFS-VCC device servers with regards to the following:

1. Design of the top level VCC Tango Device Servers running on the FHS
2. The control interface between the MCS and FHS-VCC Controller
3. The Emulator configuration
4. Any design / implementation updates required by MCS

### Overview

In general, the initial design will not deviate much from that of the Talon-DX high level device servers. The main differences will be in the device server implementation which will be ported from C++ to Python using PyTango instead.

Along with this change is that the device servers will not run as stand-alone processes but instead will be running from within Docker containers.

The other major difference will be when the flow reaches the low-level device servers. This will be dependent on a new state of the system which will be emulation mode. If the system is running in emulation mode, instead of using the FW APIs in the low-level device servers to talk to the FW IP Blocks the data will be directed to use the Emulator APIs which will in turn communicate with the Emulator instead of the Agile-x hardware.

## Interface Parameters

## Configuration and Deployment

This section will outline how the high / low level device servers get configured and spun up as well as how in emulation mode the emulator also gets configured and run.

### Device Server Configuration and Deployment

The FHS device servers will be configured from .yaml files that outline the device servers and their properties. This will follow the same procedure as that of MCS for deploying and configuring device servers. Each VCC stack of device servers will be spun up in their own pod, this is to minimize overhead from having too many pods. Each VCC pod will container

- vcc_all_bands
- b123_vcc_osppfb_channelizer
- frequency_slice_selection
- mac
- packet_validation
- wideband_input_buffer
- wideband_freuqency_shifter

### Emulator Configuration

The Emulator engine requires that for each ip block needed to be emulated that an emulated version be created in python along with its state transition model. These will live in the same repos as the FW API’s and will be pulled in from the same location in each repo to the bitstream package on build.

A configuration file for the emulator will also be necessary that will outline the ip blocks needed and how they connect to each other in the emulator engine. This configuration should mimic that of the FW Ip blocks. This will also be required to be pulled into the bitstream package for use on setup.
Once the bitstream package is built, on configuration of the FHS the bitstream package will be downloaded and the emulator ip blocks and configuration placed in a location to be mounted by the emulator engine container.

The emulator engine will then use retrieve the configuration and emulator ip blocks, use the configuration file to initiate the emulator engine configuration and set up the ip blocks with the relevant rabbitmq connections / rest endpoints.

For more detailed information please see the ska-mid-cbf-emulators [readthedocs](https://readthedocs.org/projects/ska-telescope-ska-mid-cbf-emulators/)

#### Emulator Configuration .JSON Example

```
{
  "id": "vcc",
  "version": "0.0.1",
  "ip_blocks": [
    {
      "id": "dish",
      "display_name": "DISH",
      "type": "dish",
      "downstream_block_ids": [
        "ethernet_200g"
      ]
    },
    {
      "id": "ethernet_200g",
      "display_name": "200Gb Ethernet MAC",
      "type": "ethernet_mac",
      "downstream_block_ids": [
        "packet_validation"
      ],
      "constants": {
        "num_fibres": 4,
        "num_lanes": 4
      }
    },
    {
      "id": "packet_validation",
      "display_name": "Packet Validation",
      "type": "packet_validation",
      "downstream_block_ids": [
        "wideband_input_buffer"
      ],
      "constants": {
        "expected_ethertype": 65261
      }
    },
    {
      "id": "wideband_input_buffer",
      "display_name": "Wideband Input Buffer",
      "type": "wideband_input_buffer",
      "downstream_block_ids": [
        "wideband_frequency_shifter"
      ]
    },
    {
      "id": "wideband_frequency_shifter",
      "display_name": "Wideband Frequency Shifter",
      "type": "wideband_frequency_shifter",
      "downstream_block_ids": [
        "b123vcc"
      ]
    },
    {
      "id": "b123vcc",
      "display_name": "B123VCC-OSPPFB Channelizer",
      "type": "b123vcc_osppfb_channelizer",
      "downstream_block_ids": [
        "fs_selection_26_2_1"
      ]
    },
    {
      "id": "fs_selection_26_2_1",
      "display_name": "Frequency Slice Selection 26 x 2:1 MUX",
      "type": "frequency_slice_selection",
      "downstream_block_ids": [
        "fs_selection_26_6"
      ],
      "constants": {
        "num_inputs": 52,
        "num_outputs": 26
      }
    },
    {
      "id": "fs_selection_26_6",
      "display_name": "Frequency Slice Selection 26:6 MUX",
      "type": "frequency_slice_selection",
      "downstream_block_ids": [],
      "constants": {
        "num_inputs": 26,
        "num_outputs": 6
      }
    }
  ],
  "first": "dish"
}
```

### Firmware Configuration

In the current implementation, when both simulation and emulation mode is turned off, this means firmware mode is enabled.

First, the firmware API wrapper will download any resources needed and bootstrap itself. This currently includes downloading the bitstream `.tar.gz` from CAR, and unzipping it in the python source code tree. The version number and package name to download is configured in the device `lowLevel` helm configuration.

The FW api will use the `device_id` provided by the helm chart to initialize the (tarball) provided `Py_Driver_Initializer`, this is responsible for reading the appropriate device settings from its internal DeTri representation and initializing the correct low level firmware driver with the appropriate register set definitions.

## Low-Level Device Servers APIs

The main change between low-level device servers on the Talon HPS and new Agile-x FHS is that the register maps are no longer generated by registerDef and accessed through attributes in the device server.

These have been moved out into tango-agnostic C++ API’s. These C++ APIs are then converted using pybind to create python bindings for the API which can be used by the pytango device server.

In turn a corresponding emulator api that matches the C++ API functions is also needed to be created to call the relevant emulator endpoints.

The low level component manager must be provided with references to all three API implementations (simulator/mock, emulator, firmware), and it will select the appropriate one based on the tango device properties.

Depending on whether the system is in emulation mode or not, the wrapper will instantiate the correct API. If in emulator mode the emulator API , if not the FW API. This allows the device server to continue to work as required by abstracting the API behaviour underneath.

### Device Server Emulator REST APIs

The device server emulator API's use the same interface as the FW but when the device server is in emulation mode all commands get routed to the emulator.

The emulator is running as a service on the cluster and the emulator APIs communicate with it using the services url which is outlined below:

```
<emulator-id>.emulators.ska-mid-cbf-emulators.svc.cluster.local:5001/<ip-block-id>/<command>
```

and an example of how this might look when sending a command to the emulator:

```
emulator-1.emulators.ska-mid-cbf-emulators.svc.cluster.local:5001/fs_selection_26_2_1/configure

```

### Device Server Firmware Tarball Structure

The tarball uploaded to CAR for use in the firmware api is required to have the following structure:

```
.
├── drivers
│   ├── py_driver_initializer.py
│   ├── py_drivers.py
│   ├── talon_dx_tdc_base_tdc_vcc_pst_processing.o
│   ├── talon_dx_tdc_base_tdc_vcc_pst_processing.so
├── emulators
│   └── 0.0.1.json
```

The `py_driver_initializer.py` is responsible for reading `py_drivers`, which provides the module name to access the shared objects and provides configuation to initialize the internal drivers. The interface should be `Py_Driver_Initializer(instance_name=device_id, memory_map_file="/dev/mem", logger=logger)`.

### Low-Level Device Servers

The low level device servers are communicated with using the VCC All bands device. These are the devices that will, depending on the mode talk to either the FW or Emulator through the APIs.

This section will give a brief description of each, the common structure and base class inheritance and commands / schemas

## Architechture Design

### High-Level FHS-VCC Design

![High level FHS-VCC Design Diagram](images/fhs-vcc_high-level-design.png)

## Design Considerations

### Multi threaded / process for Band Devices

It could be beneficial for band devices that instead of spinning up multiple device servers in k8s pods that are controlled by the DsVccController process as threads running the band device servers. This will allow for better control over the band devices and save resource usage by not needing a container and pod for each band device.

### Single Pod for Each VCC

To minimize overhead and pod clutter the VCC stack of Device Servers will be loaded into a single pod. This pod will include:
