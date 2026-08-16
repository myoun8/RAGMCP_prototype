---
doc_id: bt-8-ancillary-equipment
source_id: BT8-001
title: BT-8 Ancillary Equipment
instrument: BT8
workflow_stage: sample_environment
source_type: web_page
access_level: public
status: current
owner: NCNR
last_reviewed: 2026-08-16
source_url_or_path: https://www.nist.gov/ncnr/bt-8-ancillary-equipment
source_last_updated: 2023-02-15
citation_required: false
---

# BT-8 Ancillary Equipment

## Sample Stage
Two stages for sample positioning and sample orientation are available:

*   **Small to Medium Weight Samples (<10 kg):** Mounted on a large phi-chi goniometer with a custom XYX-table. This setup eliminates the need for sample remounting and the table can function as a sample changer for high-throughput texture measurements.
*   **Large Samples (up to 250 kg):** Measured using the base XYZ-table after the top goniometer is removed.

## Uniaxial Load Frame
The uniaxial load frame has a capacity of 100 kN. Custom grips can be utilized to accommodate specimen shapes and materials where standard grips are not feasible.

## Multi-axial Loading Devices
Multi-axial deformation is critical for analyzing sheet metal forming, as these processes often involve combinations of straining modes or path changes (e.g., bi-axial stretching followed by bending/plane-strain deformation). Because these stresses cannot be derived from sequential uniaxial straining or obtained via load sensor readings, neutron diffraction is used for direct measurement.

### Octo-Strain
Octo-Strain is an 8-arm loading device designed to measure the multi-axial yield function of industrial sheet metals.

*   **Control Modes:** Each arm is independently controlled via force (load cell), grip displacement, or strain (via Digital Image Correlation).
*   **Capabilities:**
    *   Effective rotation range of 180° about the scattering vector to determine principal stress axes.
    *   Higher strain range compared to cruciform machines (which use only two pairs of opposing arms).
    *   Capable of path changes along 45° directions.
*   **Technical Specifications:**
    *   **Sample Area:** A central circular recess (machined or spotweld-sandwiched) limits the neutron exposed area.
    *   **Load Capacity:** Initial maximum actuator force was 15 kN; an upgraded version provides up to 40 kN per arm, enabling tests on advanced high strength steels (AHSS).
*   **Operation:** Samples are deformed continuously at a low strain rate to avoid creep. Neutron measurements are taken at discrete rotation angles, while DIC measurements occur at the starting angle of each rotation cycle.
*   **Operational Range:** Primarily operates in strain space where $\epsilon_2 > -\epsilon_1$ due to buckling limits for compressive loads.

### Shear Device
The shear device was developed to access shear modes in sheet metal deformation (specifically regions where $\epsilon_2 = -\epsilon_1$) that are inaccessible to Octo-Strain due to buckling.

*   **Capabilities:**
    *   Two independent actuators allowing modes from pure shear to mixed modes (with added compression or tension).
    *   Capable of performing uniaxial tests.
    *   Rotation range of 135°, sufficient for tracking principal axis rotations.
*   **Technical Specifications:**
    *   **Load Capacity:** Up to 40 kN.
    *   **Typical Dimensions:** Shear areas are typically 10 mm $\times$ 40 mm; neutron illuminated areas are typically 6 mm squares.

## Digital Image Correlation System (DIC)
Because strains in multi-axial deformation are inherently inhomogeneous (due to edge proximity, grips, or the Octo-Strain recess), DIC is used to resolve the local tensor of plastic strains in real time.

*   **Function:** Analyzes speckle patterns to identify regions of sufficient homogeneity suitable for neutron diffraction.
*   **Integration:**
    *   Outputs strain data in analog or digital form to the Octo-Strain and shear device controllers, enabling true strain control.
    *   Since straining is performed continuously to prevent creep, strain accumulates during neutron measurements.
    *   **Data Synchronization:** The DIC and neutron data collection are separate systems. Matching occurs in the PF analysis software via time-stamping, where strain data are binned and averaged over the duration of the neutron measurement.

## Contacts
[contact details omitted]

<!-- Source: BT-8 Ancillary Equipment (https://www.nist.gov/ncnr/bt-8-ancillary-equipment). Removed site navigation, footer, government website banners, and specific contact personal info. -->
