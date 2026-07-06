---
doc_id: nice_overview
source_id: COMMON-001
title: NICE Instrument Control Overview
instrument: COMMON
workflow_stage: instrument_control
source_type: manual
software: NICE
access_level: public
status: current
owner: NCNR computing group
last_reviewed: 2026-06-12
source_url_or_path: https://www.nist.gov/ncnr/nice-help
source_last_updated: 2024-11-07
citation_required: false
---

# NICE Instrument Control Overview

NICE (the Neutron Instrument Control Environment) is a software package developed in-house at NCNR for controlling the neutron instruments. It has a client-server architecture.

## Server

- High reliability, designed to run continuously through a reactor beam cycle.
- Recoverable from power loss and network instability.
- Hardware operation is modeled as a directed node-graph for handling constraints and dependencies between elements.
- Produces NeXus (HDF5) rich data files, in addition to other formats.
- In production since 2012.

## Client

- Can run from anywhere inside the NIST firewall — for connecting from dedicated instrument workstations or office PCs.
- Self-updating, simple binary installation (installation link is only valid inside the NIST firewall).
- Simple point-and-click graphical interface for:
  - moving the instrument components;
  - controlling high-level physical quantities (Q, [H,K,L], E_i, E_f, etc.);
  - setting up templated scans ("trajectories");
  - viewing real-time plots of measurements.

## Related NICE Help sections

The NICE Help book includes detailed sub-pages that map to other sources in this pack, including:

- The NICE Console and Common Commands (read, move, ct, FindPeak) — see COMMON-010.
- Trajectory Guide (trajectory editor, anatomy of a trajectory, trajectory reference) — see COMMON-002.
- FAQ — relevant to COMMON-008.
- Devices, Nodes, Queue, Editor Window, Sample System, and related operational pages.

## Contacts

Support contacts for NICE DAQ are listed on the source page under "Contacts." Refer to the live page for current names and contact details.

<!-- Source: NICE Help | NIST. Created September 13, 2018; updated November 7, 2024. Navigation, sharing widgets, and personal contact details removed during normalization. -->