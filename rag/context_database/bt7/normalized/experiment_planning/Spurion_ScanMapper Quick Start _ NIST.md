---
doc_id: spurion_scanmapper_quick_start
source_id: BT7-011
title: Spurion/ScanMapper Quick Start
instrument: BT7
workflow_stage: experiment_planning
source_type: web_page
access_level: public
status: current
owner: NIST Center for Neutron Research
last_reviewed: 2026-07-02
source_url_or_path: https://www.nist.gov/ncnr/spurionscanmapper-quick-start
source_last_updated: 2019-03-28
citation_required: false
software: DAVE
---

# Spurion/ScanMapper Quick Start

'Spurion' has been incorporated into DAVE and is now called **TAS Scan Mapper**. It can be found under TAS Tools in the Planning section.

## Overview
TAS Scan Mapper is used to generate plots of the scattering plane, accessible reciprocal space, and aluminum diffraction lines. The program can trace wave vectors and energies for various higher-order scattering processes.

### Capabilities
* **Reciprocal Space Output:** Produces hardcopy output of reciprocal space and energy plots.
* **Sample Holder Interference:** Ability to add aluminum or copper powder lines to the reciprocal space plot.
* **Higher-Order Processes:** Traces second, third, and fourth order processes on the reciprocal space plot and their corresponding energy ranges on the energy plot.
* **Incoherent Scattering:** Indicates incoherent scattering processes.
* **Visualization:** Plots can be zoomed and output to a color postscript file for printing.
* **Interface:** Features a GUI interface with detailed internal help.

The most efficient way to begin is by inputting a previously collected data file that contains the instrumental configuration and lattice information.

## Background

A neutron incident on a sample with wave vector $k_i$ and energy $E_i$ is scattered into a final wave vector $k_f$ and final energy $E_f$. Total momentum and energy must be conserved, resulting in a corresponding change in the crystal momentum and energy. The changes in wave vector $\mathbf{Q}$ and energy $\Delta E$ are defined as:

$$ \mathbf{Q} = \mathbf{k}_i - \mathbf{k}_f \quad (1) $$
$$ \Delta E = E_i - E_f \quad (2) $$

### Higher-Order Scattering
Since monochromators and analyzers can scatter higher-order wavelength neutrons, Equation (1) can be generalized as:

$$ \mathbf{Q} = n\mathbf{k}_i - m\mathbf{k}_f \quad (3) $$
$$ \Delta E = nE_i - mE_f \quad (4) $$

When performing a scan using Equations (1) and (2) (where $n=m=1$), higher-order processes are scanned simultaneously. While filters or specific monochromators/analyzers (e.g., silicon or germanium) with systematic absences can eliminate some of these, some processes typically remain. TAS Scan Mapper identifies where these processes occur in reciprocal space and energy.

### Incoherent Scattering
Spurious processes can also occur via incoherent scattering from the monochromator, analyzer crystal, or holder:
1. An incident wave vector $\mathbf{k}_i$ can scatter from the analyzer such that $\mathbf{k}_i = \mathbf{k}_f$ via incoherent scattering.
2. A neutron can scatter incoherently from the monochromator and then undergo Bragg scattering from the analyzer.

This is elastic scattering. If the difference is close to a reciprocal lattice vector, it can produce a spurious peak, despite the incoherent cross section being orders-of-magnitude smaller than Bragg scattering. TAS Scan Mapper warns the user of this condition by color-coding the elastic Bragg condition in **red**.

<!-- Source: Spurion/ScanMapper Quick Start | https://www.nist.gov/ncnr/spurionscanmapper-quick-start. Removed site navigation, social media sharing links, and government website boilerplate. -->
