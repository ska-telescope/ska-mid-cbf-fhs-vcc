# DsVccController Design

## Introduction
The DsVccController is responsible for controlling the devices in the FHS-VCC. 

Its main objective is to put the server into its on state and take a configuration from the MCS that will initialize six band device servers (DsBands).  

These bands can be mixed between the following modes, bands 1/2/3 or bands 4/5 other band combinations will cause the system to fail. 

These are started as 6 threads each configured from the configuration received from MCS.



