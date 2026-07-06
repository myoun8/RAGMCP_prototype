---
doc_id: nice_trajectory_guide
source_id: COMMON-002
title: NICE Trajectory Guide
instrument: COMMON
workflow_stage: experiment_planning
source_type: manual
software: NICE
access_level: public
status: deprecated
owner: NCNR computing group
last_reviewed: 2026-06-12
source_url_or_path: https://www.nist.gov/ncnr/nice-help/trajectory-guide
source_last_updated: 2026-05-27
deprecation_notice: true
citation_required: false
---

# NICE Trajectory Guide

> DEPRECATION NOTICE: The source page carries the banner "This page is no longer being updated and the information may be out of date." Treat this content as deprecated/legacy and verify against current NICE documentation before relying on it.

NICE offers users a highly flexible system of collecting neutron counts, called a *trajectory*. A trajectory moves the instrument through a series of measurement states and performs a count at each one. The organization and format of data files are customizable. Unlike scripts, trajectories are deterministic*, allowing them to be previewed via a process called *dryrun*.

Every measurement state corresponds to a state of the instrument — such as motor positions, sample environment temperatures, etc. At each measurement state, NICE performs a count, writes data to disk, and broadcasts data to any listeners. This entire process is referred to as a *point*.

Trajectories offer convenient tools to describe the series of points to visit, such as "move motorX from 10 mm to 20 mm in 11 steps." Trajectories can be saved to files and then executed from the GUI, via the `runTrajectory` command, or from a sequence/script. As such, a trajectory is a compact, reusable "unit" for use in experiments.

*Runtime events such as communication failure cannot be predicted, nor can functions using random numbers.

## Trajectory Guide contents

This is the landing page for the multi-part Trajectory Guide. Detailed sub-pages include:

- 1. The Trajectory Editor — https://www.nist.gov/ncnr/nice-help/trajectory-guide/1-trajectory-editor
- 2. Anatomy of a Trajectory — https://www.nist.gov/ncnr/neutron-instruments/instrument-control-software-0/trajectory-guide/2-anatomy-trajectory
- 3. Trajectory Reference (https://www.nist.gov/ncnr/neutron-instruments/instrument-control-software-0/trajectory-guide/3-trajectory-reference), with sub-topics: Counter, Data-of-Interest, Expressions, File Output, File Rule (+ Appendix, Instrument-specific File Rules), Functions, Initialization, Lists, Loops, Namespace and Variables, Nested Loops, Parameterized Trajectories, Queue, Ranges, Reserved Words, SANS-type Scan, Sample, Skipping and Waiting.

## Related NICE Help pages

- NICE Help (book home): https://www.nist.gov/ncnr/nice-help
- Scripts: https://www.nist.gov/ncnr/nice-help/scripts
- Sequences: https://www.nist.gov/ncnr/nice-help/sequences
- The NICE Console / Common Commands (see COMMON-010): https://www.nist.gov/ncnr/nice-help/nice-console/common-commands

<!-- Source: Trajectory Guide | NIST (https://www.nist.gov/ncnr/nice-help/trajectory-guide). Created September 4, 2018; updated May 27, 2026. Page carries an explicit "no longer being updated" deprecation banner -> status set to deprecated. This is the landing page; the Trajectory Reference subtree (~18 child pages) holds the detailed reference and should be gathered separately if deeper trajectory docs are needed. Note: child reference pages live under a different URL path (/neutron-instruments/instrument-control-software-0/trajectory-guide/...). Navigation and sharing widgets removed. -->