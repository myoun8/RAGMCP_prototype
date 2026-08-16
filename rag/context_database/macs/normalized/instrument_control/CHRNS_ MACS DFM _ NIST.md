---
doc_id: chrns_macs_dfm
source_id: MACS-002
title: CHRNS: MACS DFM
instrument: MACS
workflow_stage: instrument_control
source_type: web_page
access_level: public
status: current
owner: MACS Operations
last_reviewed: 2026-08-16
source_url_or_path: https://www.nist.gov/ncnr/facilities-upgrades-during-unplanned-outage/chrns-macs-dfm
source_last_updated: 2023-01-30
citation_required: false
software: NICE
---

# CHRNS: MACS DFM

The double focusing monochromator (DFM) on MACS optimizes the use of the PeeWee cold source by focusing cold neutrons either on the sample to increase flux or on the detectors to enhance resolution.

## Technical Overview

The monochromator utilizes a collection of 32 motors to position HOPG crystals for:
* **Energy focusing**: In the scattering plane.
* **Sagittal focusing**: Out of the scattering plane.

### Legacy System
The original system consisted of independent motor controllers for each motor, bussed together using the RS485 electrical standard. A large Labview application was used to calculate motor angles for specific energy and focusing modes. This system was replaced due to obsolete motor controllers and inefficiencies in the supervisory application.

## Improvements and Upgrades

The control electronics were adapted to use the NCNR facility standard VIPER motor control application. Key improvements include:

* **Hardware**: Built adaptor boxes to route motor and feedback signals to VME-based indexers and associated stepper drivers.
* **Software Architecture**: 
    * Replaced the legacy Labview application with the standard NCNR motor control application.
    * The NCNR standard motor control application was rewritten as a compiled application using the Qt cross-platform development toolkit.
* **Performance and Stability**:
    * Increased responsiveness and stability.
    * Designed for easier deployment on modern Linux variants.
    * Multithreaded implementation to decrease overhead in motor positioning and event counting.
* **Interfaces and Timing**:
    * Supports both serial and Ethernet remote interfaces.
    * Emits motor positions with absolute timestamps in the IEEE-1588 (Precision Time Protocol) format.
* **Capabilities**: Supports coordinated focusing motions.

## Instrument Integration

The **NICE instrument control system** manages the DFM focusing along with all other instrument motions. NICE provides:
* A live cartoon representation of the entire instrument that updates in real-time.
* A detailed representation of the DFM showing every motor's position.
* Limit and positional information available via mouse-over.
* Top-down, focused blade projections/shadows.

<!-- Source: CHRNS: MACS DFM | https://www.nist.gov/ncnr/facilities-upgrades-during-unplanned-outage/chrns-macs-dfm. Removed site navigation, government banners, footer, and image placeholders. -->
