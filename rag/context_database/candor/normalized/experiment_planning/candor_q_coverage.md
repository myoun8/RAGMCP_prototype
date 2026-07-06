---
doc_id: candor_q_coverage
source_id: CANDOR-004
title: CANDOR Q-Coverage Calculator
instrument: CANDOR
workflow_stage: experiment_planning
source_type: web_calculator
access_level: public
status: current
owner: NCNR
last_reviewed: 2026-06-15
source_url_or_path: https://pages.nist.gov/reflectometry-calculators/candor_q.html
source_last_updated: 2026-04-23
citation_required: true
---

# CANDOR Q-Coverage Calculator

This page provides an interactive Q-coverage calculator for the CANDOR instrument. The calculator plots momentum transfer, **Q**, against detector angle in radians, using the CANDOR wavelength and detector-angle configuration encoded in the page JavaScript.

The saved HTML contains little explanatory prose. The technical details below are extracted from the page title, footer, visible controls, axis labels, and embedded calculator code.

## Purpose

The calculator is intended for CANDOR experiment planning. It visualizes which Q values are covered by the configured detector-angle positions and wavelength channels, helping users estimate accessible Q coverage for a proposed measurement geometry.

## Plot / Interface

- Plot x-axis: **Q**
- Plot y-axis: **detector angle (radians)**
- Visible control: **detector count**
- Detector-count options: **1**, **4**, and **20**
- Default selected detector count in the saved page: **20**
- The plot supports zoom/scroll behavior through the embedded chart code.
- A y-slice interactor highlights an angular band. The detector-count control changes the vertical span of this band.

## Embedded Calculator Configuration

Detector-angle configuration:

- Start angle: **0.001 degrees**
- Step size: **0.131 degrees**
- Number of angle positions: **80**
- Derived final angle: **10.35 degrees**
- Approximate angular range in radians: **0.00001745 to 0.18064 rad**

Wavelength configuration:

- Start wavelength: **4.0 Å**
- End wavelength: **6.0 Å**
- Number of wavelength channels: **54**
- Wavelength step: **(6.0 − 4.0) / (54 − 1) ≈ 0.0377358 Å**

Derived plotted grid:

- Angle positions × wavelength channels: **80 × 54 = 4,320 plotted Q/angle points**
- Approximate Q range from the encoded configuration: **1.83 × 10⁻⁵ Å⁻¹ to 0.283 Å⁻¹**

## Calculation Used

The calculator converts detector angles from degrees to radians and computes Q for each detector-angle/wavelength pair using:

```text
Q = (4π / wavelength) × sin(detector_angle / 2)
```

where wavelength is in Å and detector_angle is in radians. Under this convention, Q is in Å⁻¹.

## Detector-Count Band Behavior

The detector-count selector changes the y-slice band span according to the angle step and selected detector count:

```text
band_span = detector_count × 0.131 degrees
```

Configured selector values:

- 1 detector: **0.131 degrees**, approximately **0.002286 rad**
- 4 detectors: **0.524 degrees**, approximately **0.009146 rad**
- 20 detectors: **2.62 degrees**, approximately **0.045728 rad**

The initial y-slice setting in the embedded code is approximately **2.5 degrees**, or **0.043633 rad**, which is close to the 20-detector band.

## Citation / Attribution

The page footer requests citation of the web calculator publication:

- Citation DOI: https://doi.org/10.6028/jres.122.034
- BibTeX entry: https://pages.nist.gov/reflectometry-calculators/doc/webcalc.bib

The footer identifies the website owner as **NCNR** and gives the last modified timestamp as **04/23/2026 16:04:30**.

## Implementation Notes Preserved from HTML

The page is implemented as an interactive browser calculator using D3 and d3-science components. The embedded script imports or references:

- D3 v7
- d3-science v0.5.0
- jQuery / jQuery UI
- jQuery layout

The plot uses a D3-science `xyChart` and a `ySliceInteractor`. The point colors are assigned with a `jet` colormap across the 54 wavelength-channel index positions.

<!-- Source: CANDOR Q coverage / CANDOR Q-coverage calculator. Source URL inferred from the CANDOR overview sidebar link and saved calculator filename/assets: https://pages.nist.gov/reflectometry-calculators/candor_q.html. HTML footer last modified timestamp: 04/23/2026 16:04:30. Citation requested by footer via DOI https://doi.org/10.6028/jres.122.034 and BibTeX link https://pages.nist.gov/reflectometry-calculators/doc/webcalc.bib. Navigation/layout wrappers, CSS, scripts, generated SVG axes/points, Cloudflare beacon, image colorbar, and UI-resizer markup removed. Personal maintainer name present in meta/footer omitted during normalization; organizational owner NCNR preserved. -->
