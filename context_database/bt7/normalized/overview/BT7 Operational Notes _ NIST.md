---
doc_id: bt7_operational_notes
source_id: BT7-006
title: BT7 Operational Notes
instrument: BT7
workflow_stage: overview
source_type: web_page
access_level: public
status: current
owner: [contact details omitted]
last_reviewed: 2026-07-02
source_url_or_path: https://www.nist.gov/ncnr/bt7-operational-notes-0
source_last_updated: 2023-06-09
citation_required: false
software: DAVE
---

# BT7 Operational Notes

The BT7 instrument features the choice of either a Cu(220) or PG(002) doubly-focusing monochromator, providing a continuous incident neutron energy range from 5 to 500 meV. The $400\text{ cm}^2$ reflecting area for each monochromator yields as much as an order-of-magnitude gain of neutrons onto the sample compared with old thermal triple-axis spectrometers. The reactor beam and post monochromatic beam elements offer a wide range of choices to optimize the resolution and intensity of the instrument, with available fluxes well into the $10^8\text{ n/cm}^2\text{/s}$ range.

## Hardware Components

### Sample Stage
The sample stage includes:
* Two coaxial rotary tables: one for sample rotation and one for the independent rotation of magnetic field coils.
* Computer controlled sample goniometer and elevator.
* $\text{He}^3$ cells to provide full polarization capability with both monochromators and the PG analyzer.

### Analyzer System
The analyzer system consists of a multi-strip PG(002) analyzer array with 13 individual blades (2 cm wide and 15 cm tall). It can be operated in:
* Horizontally focused mode.
* Flat configuration (used with either a linear position-sensitive detector or conventional Söller collimators).

**Warning:** The blades are mounted in perfect Si single crystals (replacing original Al backings) for low background. These are extremely fragile. **DO NOT TOUCH ANYTHING INSIDE THE ANALYZER**; user intervention can cause catastrophic damage.

All analyzer options are under computer control and can be interchanged by the experimenter without mechanical changes.

### Detectors
* **Diffraction Detector:** Located in front of the analyzer for Bragg peak measurements.
* **Monitoring Detectors:** A series of 11 detectors embedded in the shielding behind the analyzer to continuously monitor neutron flux. These can be used for measurements of the instantaneous correlation function or with a radial collimator for diffraction patterns over limited angular ranges.
* **Position Sensitive Detector (PSD):** Can be used with a radial collimator for higher resolution diffraction patterns or instantaneous correlation functions.

## General Specifications

| Parameter | Specification |
| :--- | :--- |
| **Monochromators** | Double focusing PG(002) ($d=3.35416\text{ \AA}$) or Cu(220) ($d=1.273\text{ \AA}$); $20\times20\text{ cm}^2$; $30'$ nominal mosaic FWHM |
| **Filters** | PG filter in reactor beam, remotely insertable |
| **Velocity Selector** | Available in reactor beam to suppress higher order neutrons and reduce fast background |
| **Analyzer System** | Flat PG or horizontally focused PG (13 blades, $15\text{ cm} \times 2\text{ cm}$); $30'$ nominal mosaic FWHM |
| **Polarization** | $\text{He}^3$ polarizers; computer controlled vertical or horizontal guide field at sample position |
| **Monochromator Take-off Angles ($2\theta_M$)** | $16^\circ$ to $75^\circ$ |
| **Incident Energy Range** | $5.0$ to $\approx 500\text{ meV}$ |
| **Scattering Angles** | $0^\circ$ to $120^\circ$ |
| **Söller Slit Collimation** | Reactor beam: $10', 25', 50', \text{Open}$. <br>Before/after sample: $10', 25', 50', 80', \text{Open}$. <br>Before detector: $25', 50', 120', \text{Open}$. |
| **Radial Collimators** | $40'$ and $80'$ before analyzer; $80'$ after analyzer |
| **Detectors** | Single low-background detector; series of detectors behind analyzer; 48-wire PSD |

### Instrument Dimensions
* **Source to Monochromator:** $488\text{ cm}$
* **Monochromator to Sample:** $206\text{ cm}$
* **Sample to Analyzer:** Variable, $165\text{ cm}$ to $229\text{ cm}$
* **Analyzer (center) to detector:** $35\text{ cm}$

## Data Reduction and Corrections

* **Monitor Correction Factor:** Available in DAVE. This correction factor should be used **only if the velocity selector is NOT employed**. If the velocity selector is used, correction is typically unnecessary, though a small correction may be applied at the lowest energies.

## Fluxes

Measured neutron fluxes at the sample position:

### PG(002) Monochromator
* $40\text{ meV}$, $\text{Open}'\text{-}50'$ (no filter): $1.0 \times 10^8\text{ n/cm}^2\text{/s}$
* $40\text{ meV}$, $\text{Open}'\text{-}80'$ (no filter): $1.4 \times 10^8\text{ n/cm}^2\text{/s}$
* $40\text{ meV}$, Double Focus: $1.8 \times 10^8\text{ n/cm}^2\text{/s}$
* $14.7\text{ meV}$, $\text{Open}'\text{-}50'$ (PG filter): $2.4 \times 10^7\text{ n/cm}^2\text{/s}$
* $14.7\text{ meV}$, $\text{Open}'\text{-}80'$ (PG filter): $3.4 \times 10^7\text{ n/cm}^2\text{/s}$
* $13.7\text{ meV}$, Double Focus (PG filter): $4.6 \times 10^7\text{ n/cm}^2\text{/s}$

### Cu(220) Monochromator
* $100\text{ meV}$, $\text{Open}'\text{-}50'$: $2.0 \times 10^7\text{ n/cm}^2\text{/s}$
* $50\text{ meV}$, Double Focus: $6.1 \times 10^7\text{ n/cm}^2\text{/s}$

<!-- Source: BT7 Operational Notes | NIST (https://www.nist.gov/ncnr/bt7-operational-notes-0). Removed site navigation, footer, social media links, and personal contact details. -->
