---
doc_id: cold_neutron_imaging_instrument
source_id: CNII-001
title: Cold Neutron Imaging Instrument
instrument: CNII
workflow_stage: overview
source_type: web_page
access_level: public
status: current
owner: Neutron Physics Group
last_reviewed: 2026-08-16
source_url_or_path: https://www.nist.gov/laboratories/tools-instruments/cold-neutron-imaging-instrument
source_last_updated: 2025-03-18
citation_required: false
software: none
---

# Cold Neutron Imaging Instrument

The Cold Neutron Imaging Instrument (CNII) was designed to be a flexible space to test, develop, and employ novel neutron imaging methods to realize different sources of image contrast [1]. The initial motivation for the instrument was to be the home of the first neutron microscope based on Wolter optics. 

The instrument is capable of polarized neutron imaging, and the first neutron images of an electric field were acquired at the CNII. INFER is a large multi-disciplinary team working to develop dark-field imaging to create multi-scale images that can be thought of as “3D-SANS”.

Using a double crystal monochromator, CNII provides users with Bragg-edge imaging to map strain [2] or crystalline phase fractions, for instance in transformation induced plasticity steels [3] or in lead acid batteries. As part of the NCNR cold source upgrade project, the NG6 guide system will be modernized and the new instrument is expected to be available in March 2027.

## Beam Characteristics

CNII sits at the end position of the neutron guide 6 (NG6). NG6 consists of straight mirrors coated with Ni-58. There is no filter material in the beam which would lower the fluence rate. 

*   **Fluence Rate (Flux):**
    *   Entrance to enclosure: $\sim 2 \times 10^9 \text{ cm}^{-2}\text{s}^{-1}$ (thermal equivalent).
    *   Sample position (9 m downstream): $\sim 2 \times 10^8 \text{ cm}^{-2}\text{s}^{-1}$ for a collimation ratio $L/D$ of about 200.
*   **Beam Area:** $10 \text{ cm} \times 10 \text{ cm}$ (uniform wavelength and intensity).
*   **Collimation:** Variable aperture diameters can be installed to yield larger collimation ratios.

### Energy Selection
The energy of the beam can be selected via two primary methods:

1.  **Double Crystal Monochromator:** Consists of highly oriented pyrolytic graphite with mosaic spread of 0.4° ($5 \text{ cm} \times 5 \text{ cm}$) or 0.7° ($5 \text{ cm} \times 7 \text{ cm}$).
2.  **Neutron Velocity Selector:**
    *   **Velocity Range:** $1275 \text{ m/s}$ to $79 \text{ m/s}$.
    *   **Wavelength Range:** $0.31 \text{ nm}$ to $50 \text{ nm}$.
    *   **Input Beam Size:** $\sim 6 \text{ cm} \times 10 \text{ cm}$.
    *   **Transmission:** $\sim 90\%$.
    *   **Resolution:** $\sim 16\%$.
    *   **Exclusions:** Rotor vibrations exclude wavelengths in the ranges $0.77 \text{ nm}$ to $1.046 \text{ nm}$ and $1.52 \text{ nm}$ to $2.69 \text{ nm}$.
    *   **Application:** Due to coarser resolution compared to mosaic crystals ($\sim 2\%$), the resulting intensity is much greater, making it suitable for dark-field and phase imaging. It also acts as a band-pass filter to eliminate artifacts from Bragg edge imaging measurements.

## Detectors, Scintillators, and Lenses
The CNII makes use of all of the NIST neutron imaging detectors.

## Sample Manipulation
A wide variety of motorized stages for rotation, tip/tilt, and translation are available for complete 6-axis motion. All motorized stages are interfaced with the NIST neutron imaging acquisition software “DataScripting.” Sample environments developed for BT2/NeXT are also available for use at CNII.

## Simultaneous Dual Mode Tomography
Similar to the BT2 facility, CNII offers simultaneous neutron and X-ray tomography (“NeXT”). The X-ray generator is a tungsten Bremsstrahlung micro-focus source with:
*   **Maximum electron acceleration:** $150 \text{ kV}$
*   **Spot size:** $\sim 7 \text{ \mu m}$

## Neutron Optical Components
CNII is designed for the installation of neutron optical components at any point along the beamline. Available components include:
*   A pair of curved neutron polarizers [4].
*   A Talbot-Lau neutron interferometer [5].
*   A suite of transmission and phase gratings to realize 2- and 3-grating far-field neutron interferometers [6, 7].
*   Vacuum tubes wrapped with wire to create a solenoidal guide field (optional installation).

## Data Acquisition and Analysis
*   **Acquisition:** Fully automated through a software package called **Data Scripting**, written by the Neutron Imaging Team.
*   **Analysis:** Users have access to both source code and compiled data analysis packages written in Matlab by the Neutron Imaging Team.

## References
[1] D. S. Hussey et al., “A New Cold Neutron Imaging Instrument at NIST,” in *Physics Procedia*, 2015. doi: 10.1016/j.phpro.2015.07.006.

[2] J. W. Sowards, D. S. Hussey, D. L. Jacobson, S. Ream, and P. Williams, “Correlation of Neutron-Based Strain Imaging and Mechanical Behavior of Armor Steel Welds Produced with the Hybrid Laser Arc Welding Process,” *Journal of Research of the National Institute of Standards and Technology*, vol. 123, no. 123011, pp. 1–8, 2018, doi: 10.6028/jres.123.011.

[3] W. Woo, J. Kim, E.-Y. E.-Y. E. Y. Kim, S.-H. S.-H. H. Choi, V. Em, and D. S. D. S. Hussey, “Multi-scale analyses of constituent phases in a trip-assisted duplex stainless steel by electron back diffraction, in situ neutron diffraction, and energy selective neutron imaging,” *Scripta Materialia*, vol. 158, pp. 105–109, Jan. 2019, doi: 10.1016/j.scriptamat.2018.08.040.

[4] A. M. Micherdzinska et al., “Polarized neutron beam properties for measuring parity-violating spin rotation in liquid 4He,” *Nucl Instrum Methods Phys Res A*, vol. 631, no. 1, pp. 80–89, Mar. 2011, doi: 10.1016/j.nima.2010.11.105.

[5] S. W. Lee, D. S. Hussey, D. L. Jacobson, C. M. Sim, and M. Arif, “Development of the grating phase neutron interferometer at a monochromatic beam line,” *Nucl. Instrum. Methods Phys. Res., Sect. A*, vol. 605, no. 1–2, pp. 16–20, 2009.

[6] D. A. A. Pushin et al., “Far-field interference of a neutron white beam and the applications to noninvasive phase-contrast imaging,” *Phys Rev A (Coll Park)*, vol. 95, no. 4, pp. 1–7, 2017, doi: 10.1103/PhysRevA.95.043637.

[7] D. Sarenac et al., “Three Phase-Grating Moiré Neutron Interferometer for Large Interferometer Area Applications,” *Phys Rev Lett*, vol. 120, no. 11, p. 113201, 2018, doi: 10.1103/PhysRevLett.120.113201.

## Contact Information
*   **Daniel S. Hussey:** [contact details omitted]
*   **David L. Jacobson:** [contact details omitted]
*   **Jacob LaManna:** [contact details omitted]

<!-- Source: Cold Neutron Imaging Instrument | NIST (https://www.nist.gov/laboratories/tools-instruments/cold-neutron-imaging-instrument). Removed site navigation, footer, header chrome, and specific contact emails/phones. -->
