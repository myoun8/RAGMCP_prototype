---
doc_id: velocity_selector_operation
source_id: BT7-013
title: Velocity Selector Operation
instrument: BT7
workflow_stage: instrument_control
source_type: web_page
access_level: public
status: current
owner: NCNR
last_reviewed: 2026-07-02
source_url_or_path: https://www.nist.gov/ncnr/velocity-selector-operation
source_last_updated: 2021-06-02
citation_required: false
software: DAVE
---

# Velocity Selector Operation

An Astrium higher-order wavelength velocity selector has been installed in the reactor beam on BT-7. This velocity selector is designed to efficiently transmit the primary wavelength neutrons while suppressing second order, third order, and higher-order neutrons so that the incident beam from the Pyrolytic Graphite (PG) or Copper (Cu) crystals onto the sample is monochromatic. The suppression of higher orders produces a cleaner beam and reduces sample activation.

## Usage Guidelines

### Diffraction Experiments
For diffraction experiments, the recommended configuration is:
* **Energy:** 13.5–14.8 meV neutrons.
* **Suppression:** Combined with PG filters to suppress higher order wavelength neutrons. Additional PG filter material can be added to reach desired suppression levels.

### Inelastic Measurements
The velocity selector is best used for inelastic measurements where variable incident energies are required, as PG filters only work at selected energies. 

**Performance Highlights:**
* Reduces $\lambda/2$ by more than an order of magnitude over an energy range from 11.5 meV to 62.5 meV.
* Suppresses third and higher orders to negligible values.
* Reduces background levels similar to those obtained using a PG filter in the reactor beam.

### High Resolution Option
A "clean" option exists using the velocity selector with PG(004), which significantly increases the energy resolution of the monochromator system. This is available for incident energies from approximately 30.5 meV to 62.5 meV.

## Technical Operation and Performance

### Components
The installation in the reactor beam includes:
* **Variable Apertures:** Computer-controlled, located in a box on the right of the unit.
* **PG Filter:** A 3 cm thick PG filter that can be remotely moved into or out of the beam.

### Beam Corrections
* **$\lambda/2$ Contamination:** With the velocity selector and vertically focused monochromator, some $\lambda/2$ may remain. While usually not requiring correction for inelastic scattering, data is available if needed.
* **Higher Orders:** Corrections for $\lambda/3, \lambda/4, \dots$ are negligible.
* **Software Warning:** The monitor correction factor provided in **DAVE** is much larger and **must not be used** if the velocity selector is employed.
* **Flat Monochromator:** If the monochromator is vertically flat, no corrections are needed.

### Comparative Performance
* **At 14.7 meV:** The PG filter in the reactor beam performs better than the velocity selector.
* **At Higher Energies (e.g., 28, 30.5, 35 meV):** The velocity selector is superior to the PG filter because PG transmission of the primary wavelength is substantially reduced and higher-order rejection is less effective.

## Transmission Data

### PG(002) Transmission
The following table details transmission for primary and 2nd order wavelength neutrons using PG(002) with a full size beam (Aperture W: 86, H: 160).

| Sample | $E_i$ (meV) | Transmission for $\lambda$ (%) | Transmission for $\lambda/2$ (%) |
| :--- | :--- | :--- | :--- |
| Si | 11.5 | 62.6 | 6.34 |
| Si | 14.7 | 65.7 | 7.71 |
| Si | 20 | 69.5 | 7.17 |
| Si | 25 | 69.2 | 6.05 |
| Si | 28 | 69.8 | 6.23 |
| Si | 30.5 | 68.5 | 8.35 |
| Si | 41 | 67.8 | - |
| Si | 45 | 67.7 | - |
| Si | 50 | 67.1 | - |
| Si | 55 | - | - |
| Ge | 41 | - | 7.41 |
| Ge | 50 | - | 7.40 |
| Ge | 55 | - | 7.75 |

*Note: For $E_i > 41$ meV, Ge single crystal data was used for $\lambda/2$ as Si powder peaks were too small for reliable fitting.*

### PG(004) Transmission
For PG(004) as the primary wavelength, contaminations primarily arise from PG(002) and PG(006), corresponding to $2\lambda$ and $2/3\lambda$.

* **At $E_i = 40$ meV:**
    * Transmission $\lambda$: 63.6%
    * Transmission $2\lambda$: 2.29% (Flux ratio: 1.1%)
    * Transmission $2/3\lambda$: 29.1% (Flux ratio: 12%)
* **At $E_i = 46$ meV:**
    * Transmission $\lambda$: 64.6%
    * Transmission $2\lambda$: 1.16% (Flux ratio: 1.13%)
    * Transmission $2/3\lambda$: 20.2% (Flux ratio: 6.77%)

## Vertical Focusing Modes (PG002)

Restricting vertical divergence (using a flat monochromator rather than sagittal focus) significantly improves the rejection of $\lambda/2$.

| $E_i$ (meV) | Vertical Mode | Transmission for $\lambda$ (%) | Transmission for $\lambda/2$ (%) |
| :--- | :--- | :--- | :--- |
| 14.7 | Sagittal (focus) | 64.7 | 7.5 |
| 14.7 | Flat | 77.4 | 0.39 |
| 28 | Sagittal | 65.7 | 5.8 |
| 28 | Flat | 77.4 | < 0.3 |

<!-- Source: Velocity Selector Operation | NIST (https://www.nist.gov/ncnr/velocity-selector-operation). Removed site navigation, social media links, government website headers/footers, and descriptive image captions that were redundant to the technical text. -->
