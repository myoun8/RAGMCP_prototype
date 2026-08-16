---
doc_id: neutron_imaging_facility_nif
source_id: BT2NIF-002
title: Neutron Imaging Facility (NIF)
instrument: BT2NIF
workflow_stage: overview
source_type: web_page
access_level: public
status: current
owner: Neutron Physics Group
last_reviewed: 2026-08-16
source_url_or_path: https://www.nist.gov/laboratories/tools-instruments/neutron-imaging-facility-nif
source_last_updated: 2025-03-19
citation_required: false
---

# Neutron Imaging Facility (NIF)

The NIST Neutron Imaging Facility provides users with a unique “plug and play” approach to imaging operating fuel cells, electrolyzers, and lithium-ion batteries. The first NIST-NeXT system was installed at BT2, allowing simultaneous neutron/X-ray tomography of complex materials and systems such as batteries, concrete, shales, and two-phase flow in granular media.

## Beamline Description

The NIST Neutron Imaging Facility (NNIF) is located at Beam Tube 2 (BT-2) at the NIST Center for Neutron Research (NCNR), providing an extremely intense source of thermal neutrons. 

The NNIF offers multiple sample positions from 2 m to 6 m distances from the beam defining aperture:
* **2 m location:** Offers the highest intensity.
* **6 m location:** Offers the largest beam diameter and simultaneous neutron/X-ray tomography capability.

The image sharpness (L/D ratio) is defined by the sample distance and the aperture diameter, following pinhole optics. A higher L/D ratio results in a sharper image but increases image acquisition time.

### General Beam Characteristics

| L (m) | Aperture d (cm) | L/d | Beam diameter (cm) | 15 cm bismuth filter Fluence Rate (cm⁻² s⁻¹) | No filter Fluence Rate (cm⁻² s⁻¹) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2 | 2 | 100 | 8 | 5.1 × 10⁷ | 3.0 × 10⁸ |
| 3 | 2 | 150 | 13 | 3.4 × 10⁷ | 2.0 × 10⁸ |
| 4 | 2 | 200 | 17 | 2.5 × 10⁷ | 1.5 × 10⁸ |
| 6 | 2 | 300 | 26 | 1.7 × 10⁷ | 1.0 × 10⁸ |
| 6 | 1.5 | 400 | 26 | 1.0 × 10⁷ | 5.9 × 10⁷ |
| 6 | 1.0 | 600 | 26 | 4.3 × 10⁶ | 2.5 × 10⁷ |
| 6 | 0.5 | 1200 | 26 | 1.0 × 10⁶ | 5.9 × 10⁶ |
| 6 | 0.1 | 6000 | 26 | 4.3 × 10⁴ | 2.5 × 10⁵ |

*Note: Apertures listed are typical; custom sizes can be installed upon special request.*

## Detector Specifications

The NNIF offers multiple detectors to tailor spatial and temporal resolution. The most common system is a lens-coupled CMOS camera viewing a scintillator, though all NIST imaging detectors can be utilized at the facility.

## Sample Interfacing with the Instrument

The NNIF uses imperial fasteners for sample mounting, typically utilizing optical breadboards and optical posts with ¼”-20 or #8-32 threads.

### Supported Sample Sizes and Weights

#### Typical High-Resolution Tomography (with height translation)
* **Max weight:** 23 kg (50 lbs)
* **Sample size:** Typically 1-3 cm diameter (determined by resolution and transmission)
* **Vertical translation:** Up to 25 cm (10 in)

#### Tomography of Larger Objects
* **Max weight:** 90 kg (200 lbs)
* **Sample size:** Determined by resolution requirements and transmission

#### Neutron Radiography
* **With translation stages:**
    * Max weight (X-Y stages): 90 kg (200 lbs)
    * Distance below beam center: 58 cm (23 in)
    * Distance above beam center: 106 cm (42 in)
* **No translation stages:**
    * Max weight: 230 kg (500 lbs)
    * Distance below beam center: 71 cm (28 in)
    * Distance above beam center: 106 cm (42 in)
    * Max field-of-view: Limited by beam diameter of 26 cm

### Environmental and Ancillary Support
* **Equipment:** Space is available inside and outside the shielded enclosure for user-supplied equipment, featuring pass-throughs for cabling and fluid connections.
* **Temperature:** Low and high temperatures are supported. NCNR orange cryostats are used for cryogenic requirements.
* **Safety:** Flammable gases (other than hydrogen) and corrosive liquids may be supported following a safety review.

## Facility Infrastructure and Equipment

### Hydrogen and Battery Infrastructure
Specific details are available on the fuel cell and lithium-ion battery project pages.

### Specialized Equipment
* **Gamry Reference 3000:**
    * Single channel, +/- 15 V @ +/- 3 A
    * EIS from 10 µHz to 1 MHz
    * 2, 3, 4 electrode measurements
    * Reference 30K booster: +20 V, -2.5V @ +/-30 A
* **Pressure Cell (Geology):**
    * Core size: 1.5 inch diameter, length 5.5 to 6.5 inch (others possible)
    * Confining pressure: 1600 psi
    * Materials: PEEK and PFA wetted components for acid compatibility; Aluminum pressure vessel (X-ray compatible)
* **Humidity Control Cell (High-Resolution Tomography):**
    * Sample diameters: Up to 15 mm
    * Gas flow: Air or nitrogen up to 10 lpm (dry or fully humidified)
    * Pressure: Controllable to 400 kPa
    * Beam windows: Aluminum or quartz (X-ray compatible)
* **ISCO 260D Syringe Pumps:**
    * Capacity: 266 ml
    * Flow rate: 0.001 mL/min to 10⁷ mL/min
    * Pressure range: 10 psi to 7500 psi
    * Configuration: 4 pumps with two controllers; can be paired for continuous flow
* **Circulators:**
    * Huber Unistat Petit Fleur: -40 to 200°C (±0.01°C stability), typically for $D_2O$ coolant.
    * Huber Unistat 405: -45 to 250°C (±0.01°C stability), typically for Fluorinert coolants.

## Data Acquisition and Analysis

* **Acquisition:** Fully automated via **DataScripting**, a software package developed by the Neutron Imaging Team.
* **Analysis:** Users have access to source code and compiled data analysis packages written in Matlab.

## Contacts
[contact details omitted]

<!-- Source: Neutron Imaging Facility (NIF) | NIST (https://www.nist.gov/laboratories/tools-instruments/neutron-imaging-facility-nif). Removed site navigation, header/footer, and personal contact information. -->
