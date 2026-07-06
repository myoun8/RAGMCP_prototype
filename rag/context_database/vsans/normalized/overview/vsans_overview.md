---
doc_id: vsans_overview
source_id: VSANS-001
title: VSANS — Very Small-Angle Neutron Scattering Diffractometer Overview
instrument: VSANS
workflow_stage: overview
source_type: presentation_pdf
access_level: public
status: archival
owner: NIST Center for Neutron Research
last_reviewed: 2026-06-15
source_url_or_path: vsans_overview.pdf
source_last_updated: 2014-11-21
citation_required: false
---

# VSANS — Very Small-Angle Neutron Scattering Diffractometer Overview

The Very Small-Angle Neutron Scattering (VSANS) diffractometer at NIST was presented as a new NCNR instrument intended to extend the accessible SANS q-range and add higher-throughput measurement modes. The presentation is dated November 19, 2014 and lists John Barker, Charlie Glinka, Jim Moyer, Nick Maliszewskyj, and Steve Kline from the NIST Center for Neutron Research.

## Purpose and motivation

VSANS was designed to improve measurement efficiency by extending the q-range of the 30 m NIST SANS instruments, so that many SANS experiments could be completed on a single instrument rather than moving between SANS and USANS configurations.

The instrument was also intended to add new measurement capabilities:

- selectable wavelength resolution: 2% graphite monochromator, 12.5% velocity selector, or a white-beam band;
- white-beam operation over approximately 4 Å <= wavelength <= 8 Å;
- expandable sample staging area of about 2 m;
- multiple detectors to extend the q-range captured in one measurement.

## Instrument concept

VSANS is described as a 45 m long SANS-like instrument with new optics, three detector carriages, and a high-resolution two-dimensional Anger camera. Initial operation was projected for fall 2016.

Major hardware elements shown in the presentation include:

- neutron guides;
- velocity selector;
- polarizing guide;
- RF flipper;
- focusing lenses and prisms;
- multiple converging apertures and slits;
- three moveable detector arrays.

The guidehall layout places VSANS near the HFBS and DCS instruments.

## Instrument characteristics

| Parameter | Value / description |
|---|---|
| Source guide | 60 mm wide x 150 mm tall |
| Wavelength range | 4 Å to 20 Å |
| Wavelength resolution | 2% graphite, 12.5% selector, or white beam over 4 Å <= wavelength <= 8 Å |
| Source-to-sample distance | 4 m to 22 m, in 2 m steps |
| Sample-to-detector distance | 0.6 m to 22.5 m, continuous |
| Collimation | circular pinholes; rectangular XY slits; 18 converging circular beams with lens and prism; 3 converging narrow rectangular beams with lens |
| Sample size | circular 1 mm to 30 mm diameter; rectangular width 1 mm to 18 mm and height 12 mm to 75 mm; converging beams typically 35 mm x 72 mm |
| Q-range | about 2e-4 Å^-1 to 1.0 Å^-1 in one measurement |
| Detectors | 1.2 mm FWHM 2D detector, 150 mm x 450 mm; 8 mm FWHM 2D tube detector with four 384 mm x 1000 mm panels; 8 mm FWHM 2D tube detector with four 384 mm x 500 mm panels |

## Detector system

The detector vessel contains three movable detector carriages. The front and middle carriages use 8 mm resolution detector panels. The back carriage uses a 1 mm resolution Anger camera.

Moveable 2D detector panels form a picture-frame arrangement:

- side panels: 384 mm x 1000 mm;
- top and bottom panels: 500 mm x 384 mm;
- one layer of 8 mm diameter helium-3 tubes.

This detector arrangement is described as extending q-range by a factor of 30. The presentation compares the concept to other multiple-carriage instruments, including D33 at ILL Grenoble and BILBY at ANSTO.

The high-resolution detector procurement slide describes an SNS-type Anger camera of 15 cm x 45 cm, with 1 mm-class position resolution. It also notes that the instrument was rotated 0.3 degrees to avoid reactor-core gamma rays.

## Collimation and q-range modes

The presentation highlights three main collimation options for extending the q-range from about 2e-4 Å^-1 to about 1 Å^-1 in one measurement:

| Mode | Source aperture | Sample aperture | Sample-to-detector | Wavelength | Approximate qmin | Approximate qmax | Beam current |
|---|---:|---:|---:|---:|---:|---:|---:|
| Narrow slit | 5 mm x 150 mm | 2.5 mm x 75 mm | 22.5 m | 6 Å | 2.3e-4 Å^-1 | 0.45 Å^-1 | 9.7e4 s^-1 |
| Converging beams | 6 mm diameter | 35 mm x 72 mm, with 10 mm diameter beams | 22.5 m | 7.5 Å | 1.9e-4 Å^-1 | 0.36 Å^-1 | 9.0e3 s^-1 |
| Large pinhole | 60 mm diameter | 30 mm diameter | 22.5 m | 6 Å | 2.8e-3 Å^-1 | 0.45 Å^-1 | 1.4e6 s^-1 |

The front and middle detector carriages use four panels each. The back carriage uses an approximately 150 mm wide x 450 mm tall Anger camera.

## Count-rate and flux rationale

The presentation argues that VSANS can offer large measurement-rate gains compared with USANS-like approaches. For an example comparison using a lens configuration with sample-to-detector distance 15 m and wavelength 8.1 Å, the presentation states that SANS with lenses can obtain the same statistics about 10,000 times faster than USANS under the stated assumptions of equal sample thickness, transmission, and 8 mm radius sample aperture.

For VSANS at qmin = 2e-4 Å^-1, the presentation estimates:

- narrow-slit collimation: up to 100,000 times faster;
- converging-beam collimation: up to 1,000 times faster.

The broader flux argument is that neutron sources have much lower brilliance than some X-ray synchrotron sources, so VSANS aims to recover usable count rate by using larger samples, larger wavelength bandwidth, larger detector solid angle, and multiple collimation options.

## Converging beams and optics

The converging-beam option uses 18 beams with:

- prisms to counter gravity;
- lenses for focusing;
- intermediate masks to stop crosstalk.

The presentation estimates a gain of about 200 for 18 converging beams with lenses, using an 18 x (10 mm / 3 mm)^2 scaling. It also cites Saclay, France and V16 in Berlin, Germany as other converging-beam instruments.

Additional optics and beam-conditioning components include:

- graphite crystal monochromator;
- choice of pinhole apertures;
- double-V polarizing guide;
- normal guide;
- XY slits;
- single circular aperture;
- beam scraper;
- electrical connector panels inside the pre-sample vacuum vessel.

## Narrow-slit mode and smearing

The narrow-slit option is presented as a high-count-rate mode with significant resolution smearing. The example configuration uses:

- source aperture: 150 mm x 5 mm;
- sample aperture: 75 mm x 2.5 mm;
- detector width: 320 mm.

The slide illustrates slit-smearing effects for spherical particles of 5,000 Å radius, ignoring wavelength smearing.

## White-beam option

The white-beam option uses a beryllium filter to cut wavelengths below 4 Å and a cut-off mirror to cut wavelengths above 8 Å. The presentation states a factor-of-five gain from this mode, but with additional smearing.

The white-beam band is compared with:

- NVS selector mode at Δλ/λ = 12.5%;
- graphite monochromator mode at Δλ/λ = 2%.

## Sample area and cells

The presentation emphasizes larger sample-area capability and a new VSANS sample area without a sample chamber. The sample table has about 1.5 m travel, and the new sample area is described as about 2 m.

Example liquid-cell areas listed in the presentation include:

| Cell type | Dimensions | Approximate area |
|---|---:|---:|
| Current Ti cell | 19 mm diameter | 284 mm^2 |
| Medium Ti cell | 28 mm diameter | 616 mm^2 |
| Helma cell 404 | 18.5 mm x 38 mm | 703 mm^2 |
| Large Ti cell | 40 mm diameter | 1260 mm^2 |
| Custom quartz cell | 35 mm x 72 mm | 2500 mm^2 |

## Polarization and automated optics

The new capabilities summary lists automated optics including:

- graphite monochromator with Δλ/λ = 2%;
- double-V polarizer with P > 99%, used with RF flipper and helium-3 analyzer.

## Capability summary

The presentation summarizes VSANS capabilities as:

- factor-of-four smaller q enabled by the high-resolution 1 mm detector;
- higher beam current through converging beams and larger sample sizes;
- narrow-slit and white-beam modes for higher count rate, with additional smearing;
- extended q-range through three independent detector carriages, with qmax/qmin = 2,000;
- larger sample area of about 2 m;
- automated optics for monochromation and polarization.

The final prediction is that many experiments with weak scattering or small samples would choose narrow-slit or white-beam operation to increase count rate, but that signal-to-noise would not necessarily improve.

## Source-cleaning notes

This Markdown file condenses a 24-page presentation PDF into a text-first instrument overview. Slide imagery, decorative drawings, page-layout artifacts, and repeated visual labels were removed. Instrument specifications, q-range and detector details, collimation modes, count-rate arguments, sample-area details, polarization notes, and the final capabilities summary were preserved. Personal author names from the title slide were retained because they are part of the static presentation citation context; no live contact details were present in the source PDF.
