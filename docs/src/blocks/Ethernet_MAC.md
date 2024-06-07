# Ethernet Media Access Control (MAC)

Receives packets of data from the ethernet network.
- Checks the packet for errors using the Frame Check Sequence (FCS). If an error detected marks the packet as errored.

Transmits packets of data to the ethernet network.
- Applies the FCS to the packets, 4 additional bytes per packet.

Provides status of its connectivity to the network.

Provides statistics on the packets that are transmitted.

Can be configured in loopback mode, so that it transmits packets to itself (and the network).

There may be several versions of this, depending on the network interface speed (100GbE, 200GbE, 400GbE)

## Data Path Interface
Once a successful connection to the network has been made, the datapath receives a stream of packets from the network and passes them to the downstream FW block. Packets may be received with errors. Errored packets are also passed downstream to the FW block, but marked as errored. The downstream block is responsible for doing something sensible with errored packets.

Similarly, packets received from an upstream FW block are transmitted onto the network. If the MAC is not connected to the network then those packets are lost. If a packet marked as errored is provided, this packet will be transmitted but the FCS will be inverted to indicate to the network the packet is errored.

### Input
- Stream of packets received from the network.
- Stream of packets to be transmitted.

### Output
- Stream of packets that were received.
- Stream of packets transmitted to the network.

## Low Level Driver API
### Structs
#### `struct config`
- rx_loopback_enable : boolean
    - default False.

#### `struct status`
- phy: struct
  - rx_loopback : boolean
  - rx_freq_lock : array[num_fibres] boolean
  - rx_word_lock : array[num_lanes] boolean
- fec: struct
  - rx_corrected_code_words : uint32_t
  - rx_uncorrected_code_words : uint32_t
- mac: struct :
  - rx_fragments : uint32_t
  - rx_runt : uint32_t
  - rx_64_bytes : uint32_t
  - rx_65_to_127_bytes : uint32_t
  - rx_128_to_255_bytes : uint32_t
  - rx_256_to_511_bytes : uint32_t
  - rx_512_to_1023_bytes : uint32_t
  - rx_1024_to_1518_bytes : uint32_t
  - rx_1519_to_max_bytes : uint32_t
  - rx_oversize : uint32_t
  - rx_frame_octets_ok : uint32_t
  - rx_crcerr : uint32_t
  - tx_fragments : uint32_t
  - tx_runt : uint32_t
  - tx_64_bytes : uint32_t
  - tx_65_to_127_bytes : uint32_t
  - tx_128_to_255_bytes : uint32_t
  - tx_256_to_511_bytes : uint32_t
  - tx_512_to_1023_bytes : uint32_t
  - tx_1024_to_1518_bytes : uint32_t
  - tx_1519_to_max_bytes : uint32_t
  - tx_oversize : uint32_t
  - tx_frame_octets_ok : uint32_t
  - tx_crcerr : uint32_t

where "rx" means received from, and "tx" means transmitted onto the network.

### Standard methods
#### `Constructor()`
- Set identity (name, address)
- Constants retrievable from registers. _Emulator will need to specify this somehow in its bitstream configuration_.
  - num_fibres : int 
    - the number of lanes on the network interface - depends on speed of interface (100G, 200G, 400G) and speed of the fibre (25G, 50G, 100G).
  - num_lanes  : int 
    - the number of virtual lane in the network interface. Each lane is 5Gbps. Depends on the interface speed (100G, 200G, 400G).

#### `recover()`
- enable reset.

#### `configure(struct config)`
- Apply loopback

#### `start()`
- disable reset

#### `stop()`
- enable reset

#### `deconfigure(struct config)`
- remove loopback

#### `status(clear: bool, struct &status)`
- populate the status struct:
    - byte counters have a snapshot function, so that the counters all reflect a moment in time.
- optionally clear the counters.