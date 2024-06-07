.. skeleton documentation master file, created by
   sphinx-quickstart on Thu May 17 15:17:35 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


.. HOME SECTION ==================================================

.. Hidden toctree to manage the sidebar navigation.

.. toctree::
  :maxdepth: 2
  :caption: Home
  :hidden:


.. README =============================================================

.. This project most likely has it's own README. We include it here.

.. toctree::
   :maxdepth: 2
   :caption: Readme

   ../../README

.. COMMUNITY SECTION ==================================================

..

.. toctree::
  :maxdepth: 2
  :caption: Package name
  :hidden:

  package/guide


Project-name documentation HEADING
==================================

These are all the packages, functions and scripts that form part of the project.

- :doc:`package/guide`


Firmware Interfaces
===================
Guides for the various Software controlable blocks in the Firmware. These describe the interface to higher level control software (a SW API). Behind this API is either
1. driver software that converts the configuration, control, and status commands to appropriate reads and writes to the FPGA registers.
2. emulator software that mimics the behaviour of the FPGA block.


.. image:: _static/img/Agilex_VCC.png

For the VCC-only stage of the bitstream, the APIs for the blocks in the top half of the image will exist:

* 200Gb :doc:`blocks/Ethernet MAC`
* Packet Validation
* Wideband Input Buffer
* Wideband Shifter
* B45VCC-OSPFFB Channeliser
* :doc:`blocks/B123VCC-OSPPFB_Channelizer`
* :doc:`blocks/Frequency_Slice_Selection`
* FS RFI Detection and Flagging

In addition for the VCC-PSS stage of the bitstream, the APIs for the blocks in the top two thirds of the image will exist, adding

* Frequency Slice Resampling and Delay Tracking
* PSS Channelizer
* PSS RFI Flagging/Corner Turn/Fine Channel Selection
* Jones Matric Correction

Finally for the VCC-PSS-TB stage of the bitstream, the APIs for the blocks in the top two thirds of the image will exist, adding

* Transient Buffer Requantization

.. toctree::
  :maxdepth: 2
  :caption: Package name
  :hidden:
  
  blocks/B123VCC-OSPPFB_Channelizer
  blocks/Frequency_Slice_Selection
  blocks/Ethernet_MAC