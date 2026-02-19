###########
Change Log
###########

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

UNRELEASED CHANGES
******************
* CIP-4349: tested UpdateSubarrayMembership command pushing subarrayID change events in standalone simulation
* CIP-2768: Use dataclass for VCC controller config 
* CIP-4496: Updates to Wideband Input Buffer manager to support emulator changes
* CIP-4382: Upgrade ska-tango-base to version 1.3.2, disable PV if bitstream download disabled

0.3.2
******
* Update make submodule to fix SKA pipeline bug

0.3.1
******
* CIP-4104: Update FHS-VCC sim and tests for override queueing
* CIP-4159: Update to use common linter

0.3.0
******
* CIP-4104: Update FHS-VCC sim and tests for override queueing
* CIP-3737, CIP-4014, CIP-4015, CIP-4053, CIP-4054, CIP-4058: Refactor to use new common base classes which eliminate all low-level Tango devices.

0.2.2
******
* CIP-3286: added field to values.yaml that allows for changing the storage class type for the pv
* CIP-3286: updated makefile so on minikube=true default the storage class to minikubes standards storage class

0.2.1
******
* CIP-3690: Updates for Poetry v2
* CIP-2856: remove frequency band offset for stream2 from required schema
* CIP-3707: Update WIB Device to include Link failure and packet loss handling
* CIP-3286: Fixed a bug when creating physical volume and updated naming of pods

0.2.0
******
* CIP-3575: Add AutoSetFilterGains command & related attributes + test updates
* CIP-3265: Updated helm chart deployment to be by vcc units and fixed helm chart bugs

0.1.1
******
* CIP-3473: FHS-Common - Update Low Level DS Base class to remove obs state
* CIP-3524: FHS VCC-MCS ICD - Updates for FDR
* CIP-3153: FHS VCC SW - Packetizer Design
* CIP-3232: Update VCC DD - Section 6
* CIP-3145: Create common repository for shared FHS tango devices
* CIP-3113: FHS Infrastructure - Refactor deployment to use InitContainers
* CIP-3172: H1 - Update FHS System Tests for Power Meter + Packetizer integration
* CIP-3174: FHS VCC - Power meter Tango Device implementation
* CIP-3141: Update Boogie image to SKA version

0.1.0
******
* CIP-3106: FHS VCC - ObsReset implementation
* CIP-3109: FHS Bitstreams - Update deployment to handle multiple bitstreams
* CIP-3045: FHS VCC - Initial HealthState implementation (WIB)
* CIP-3104: H1 - Reconfigure from FAILURE test
* CIP-3018: FHS VCC - Abort command implementation
* CIP-3102: FHS VCC -  DishID conversion unit tests
* CIP-3105: H1 - Split configuration test
* CIP-3059: FHS VCC ConfigureScan - Error handling & cleanup on failure
* CIP-3052: FHS VCC & Tests- Attribute updates & DishID conversion port
* CIP-3044: FHS VCC: override adminMode to push change events and update H1 tests

0.0.2
******
* CIP-3052: FHS VCC & Tests- Attribute updates
* CIP-2920: H1 - Reporting implementation
* CIP-3019: H1 - Scan failure tests
* CIP-3032: FHS VCC - Refactor helm charts
* CIP-2993: FHS VCC - Drivers update for Agilex Detri definition
* CIP-3010: Initial DishID implementation
* CIP-2957: H1 - Implement test runner + initial tests
* CIP-2989: FHS VCC - GoToIdle implementation
* CIP-2954: Investigate volumes for storing bitstream tar
* CIP-2574: Create initial ICD for top-level FHS VCC devices
* CIP-2975: FHS VCC - Update FHS stack / Emulators to use volumes for bitstream
* CIP-2888: H1 - Develop deployment validation tests
* CIP-2449: FW API - VCC-VCC software-firmware interface definition
* CIP-2834: Initial FHS-VCC Tango Device server unit tests
* CIP-2882: Document FW workspace integration emulator & drivers

0.0.1
******
* Initial release.
