---
doc_id: jres.117.002
source_id: BT7-003
title: Double-Focusing Thermal Triple-Axis Spectrometer at the NCNR
instrument: BT7
workflow_stage: overview
source_type: paper
access_level: public
status: current
owner: NCNR
last_reviewed: 2026-07-02
source_url_or_path: jres.117.002.pdf
source_last_updated: 2012-02-02
citation_required: true
software: DAVE
---

# Double-Focusing Thermal Triple-Axis Spectrometer at the NCNR

The new thermal triple-axis spectrometer at the NIST Center for Neutron Research (NCNR) is located at the BT-7 beam port. The 165 mm diameter reactor beam is equipped with a selection of Söller collimators, beam-limiters, and a pyrolytic graphite (PG) filter to tailor the beam for the dual 20×20 cm² double-focusing monochromator system that provides monochromatic fluxes exceeding $10^8$ n/cm²/s onto the sample. 

## 1. Introduction
The BT-7 instrument is designed to modernize the thermal neutron spectrometers at NCNR, taking full advantage of the large 165 mm diameter beam tubes. It utilizes two interchangeable 20×20 cm² double focusing monochromators (PG(002) and Cu(220)), providing incident energies from 5 meV to above 500 meV. The analyzer system uses PG with horizontal focusing capabilities in various configurations.

## 2. Overview of the Design
The spectrometer layout consists of the following sequence:
*   **Experimental Beam Shutter:** Located within the biological shield; open (6.4 cm wide at exit, 16 cm vertical) or closed.
*   **Variable Apertures:** Four blades (two horizontal, two vertical) composed of compressed $^6\text{LiF}$ on the source side with a 10 cm thick aluminum frame filled with $\text{B}_4\text{C}$.
*   **Filter:** A tunable pyrolytic graphite (PG) filter system.
*   **Rotating Collimator-Exchanger:** Houses three Söller-slit collimations (6.4 cm wide, 17.8 cm tall) with FWHM angular acceptances of 10', 25', and 50', plus an 9×18 cm² "Open" position.

## 3. Detailed Specifications

### 3.1 Monochromator Drum
*   **Dimensions:** 213 cm diameter; 40.6 cm inner diameter.
*   **Angular Range:** Straight-through to 115° scattering angle (practical range $\approx 17^\circ$ to $\approx 75^\circ$ on BT-7).
*   **Monochromators:** 
    *   PG(002) and cold-pressed Cu(220) are installed.
    *   Each consists of 100 squares ($2\times 2 \text{ cm}^2$ each) for a total area of $20 \times 20 \text{ cm}^2$.
    *   Incident energy range: 5 meV (PG) to 500 meV (Cu).
*   **Beam Optics:** Söller-slit collimations of 10', 25', 50', and 80' FWHM, or open channels for horizontal focusing. Beam width with collimation is 3.8 cm.
*   **Sample Size:** Max $\approx 3 \text{ cm wide}$ and $\approx 5 \text{ cm high}$.

**Table 1: Absolute flux values for the PG(002) and Cu(220) monochromators**

| Monochromator | d-spacing (Å) | Energy (meV) | Collimation | PG filter | Flux ($10^7 \text{ n/cm}^2\text{/s}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| PG(002) | 3.3542 | 40 | Open-50' | No | 10 |
| PG(002) | 3.3542 | 40 | Double Focus | No | 18 |
| PG(002) | 3.3542 | 14.7 | Open-50' | Yes | 2.4 |
| PG(002) | 3.3542 | 13.7 | Double Focus | Yes | 4.6 |
| Cu(220) | 1.273 | 100 | Open-50' | No | 2.0 |
| Cu(220) | 1.273 | 50 | Double Focus | No | 6.1 |
| Ge(311) | 1.702 | - | - | - | (Under development) |

### 3.2 Sample Stage
*   **Design:** Cantilevered from the monochromator drum.
*   **Axes:** Three concentric non-magnetic Huber axes for sample rotation, horizontal field magnet axis, and scattering angle ($2\theta$).
*   **Travel:** 35 cm along the monochromatic beam direction.
*   **Environment:** Accommodates Huber x-y tilt/translation goniometers.
*   **Shielding:** Sample surrounded by borated aluminum neutron absorbing shielding ($\approx 77 \text{ cm diameter} \times 76 \text{ cm tall}$).
*   **Beam Stop:** Pb and polyethylene laminate separated by 0.125 cm borated Al. Includes 15 cm of single crystal Bi to attenuate gammas.

### 3.3 Analyzer/Detector Systems
The analyzer system is modular and mounted on air pads for rapid interchangeability.
*   **Standard Analyzer:** 13 vertical blade pyrolytic graphite (PG) system. Each PG element is 2 cm wide and 15 cm high, mounted on 1 mm thick Si single crystals.
*   **Detectors:**
    *   **Single Detector:** Three $^3\text{He}$ detectors (2.5 cm diameter, 15 cm high).
    *   **PSD:** Ordela 1348N linear position-sensitive detector (48 wires, 36° active area, 16.5 cm height).
    *   **Diffraction Detector:** Identical to the single detector, positioned in front of the analyzer.
    *   **Monitor Detectors:** Eleven $5\times 15 \text{ cm}^2$ $^3\text{He}$ detectors embedded in the door.
*   **S-A Optics:** X-rail for beam-limiter slits, PG filters, $\text{LN}_2$-cooled Be filter, and polyethylene shields. Söller collimations (10', 25', 50', 80') and radial collimators (40', 80').

## 4. Analyzer Modes of Operation

| Mode | Description | Primary Use |
| :--- | :--- | :--- |
| **Diffraction Detector** | Detector placed in front of crystal analyzer. | Alignment, wavelength calibration, Bragg peak intensities. |
| **Diffraction with PSD** | Radial collimator + PSD in straight-through position. | Simultaneous measurement along reciprocal space arcs; powder diffraction. |
| **Conventional TAS** | Flat analyzer configuration with Söller collimators. | Standard single (Q, E) point measurements. |
| **Horizontal Energy Focusing** | Radial S-A collimator + PG array in focusing mode. | Increased signal (up to 3x) by relaxing wave vector resolution. |
| **Flat Analyzer with PSD (Q-E)** | Radial S-A collimator + flat PG array + PSD. | Simultaneous measurement of a range of (Q, E). |
| **Constant-$E_f$ Mode** | Analyzer array rotated away from horizontal focus. | Constant-energy scan where each blade corresponds to a different Q. |

## 5. Performance
*   **Distances:**
    *   Source to Monochromator: 488 cm
    *   Monochromator to Sample: 206 cm
    *   Sample to Analyzer: 165 cm to 229 cm (variable)
    *   Analyzer to Detector: 35 cm
*   **Sample Environment:** Temperatures from 20 mK to 2000 K; magnetic fields up to 15 Tesla.

## 6. Polarized Beam Option
Utilizes $^3\text{He}$ polarizers immediately before and after the sample.
*   Capable of measuring all eight conventional polarized neutron cross sections.
*   Includes two spin rotators and a computer-controlled adjustable guide field at the sample position.

## 7. Operational Notes
Electronics are distributed:
*   **Monochromator Drum:** Controls for beam conditioning, sample table, drum, and scattering angle.
*   **Analyzer:** Controls for analyzer motors, detector electronics, and air-pad systems.
*   **Software:** Visualization and analysis are performed using **DAVE**.

## 8. Future Options
*   **Velocity Selectors:** Potential integration of velocity selectors for a cleaner monochromatic beam up to 60 meV.
*   **Four-Circle Goniometer:** Planned implementation to increase capability for determining crystal/magnetic structures and excitations in different scattering planes.

<!-- Source: Double-Focusing Thermal Triple-Axis Spectrometer at the NCNR (http://dx.doi.org/10.6028/jres.117.002). Removed author names, emails, and redundant page headers/footers. -->
