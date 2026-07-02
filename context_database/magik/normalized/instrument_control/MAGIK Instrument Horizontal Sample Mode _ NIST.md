---
doc_id: magik_instrument_horizontal_sample_mode
source_id: MAGIK-003
title: MAGIK Instrument Horizontal Sample Mode
instrument: MAGIK
workflow_stage: overview
source_type: web_page
access_level: public
status: current
owner: NCNR
last_reviewed: 2026-07-02
source_url_or_path: https://www.nist.gov/ncnr/magik-instrument-horizontal-sample-mode
source_last_updated: 2023-04-27
citation_required: false
---

# MAGIK Instrument Horizontal Sample Mode

In the summer and fall of 2019, the MAGIK neutron reflectometer was upgraded to implement the original monochromator and a vertically mobile monochromator on a horizontal translation stage, allowing the user to swap between configurations. 

The newly installed monochromator assembly, which can be translated vertically, provides a smooth and relatively constant beam for any incident angle. This experimental setup allows the sample environment to reside on a fixed stage for reflectivity measurements. This horizontally-modified MAGIK setup is currently under beta testing.

## Geometry and Configuration

In the horizontally-staged configuration:
* **Neutron Beam:** Passes through the new monochromator with an optimized wavelength of $5\text{ Å}$.
* **Collimation:** The beam is collimated on a horizontally-staged sample at an incident angle $\alpha_i$ using:
    * Two pre-sample slits of width $w_i$.
    * One aperture slit $a_i$.
* **Reflection:** The beam reflects off the sample and passes through a third slit (slit 3) at a reflected angle $\alpha_f$ toward the point source detector, where $\alpha_i = \alpha_f$.
* **Motion:** Pre-sample slits 1 and 2, and post-sample slit 3, translate vertically along the z-direction to reach the sample interface.

### Future Enhancements
Planned modifications include the implementation of a second post-sample slit (slit 4) to further collimate the reflected beam and suppress background scattering.

## Schematic Summary (Figure 1)
The horizontal MAGIK setup consists of a monochromatic neutron beam collimated by pre-sample slits 1 and 2 moving in the z-direction to direct the beam at incident angle $\alpha_i$ onto the sample. The slit widths $w_i$ and aperture $a_i$ determine the beam footprint $F_b$ on the sample. A post-sample slit 3, also moving in the z-direction, is positioned in front of the detector to capture the neutron beam at a reflected angle $\alpha_f$ equal to $\alpha_i$.

## Contacts
[contact details omitted]

<!-- Source: MAGIK Instrument Horizontal Sample Mode | https://www.nist.gov/ncnr/magik-instrument-horizontal-sample-mode. Removed site navigation, footer, social media links, and personal contact details. -->
