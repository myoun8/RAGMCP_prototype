---
doc_id: ncnr_data_repository
source_id: COMMON-003
title: NCNR Instrument Data — Repository, Viewers, and Metadata Search
instrument: COMMON
workflow_stage: data_access
source_type: manual
access_level: public
status: current
owner: NCNR computing group
last_reviewed: 2026-06-12
source_url_or_path: https://ncnr.nist.gov/ncnrdata/
related_source_ids: COMMON-004
citation_required: false
---

# NCNR Instrument Data

The NCNR provides online tools for browsing, searching, and retrieving instrument data, plus a searchable metadata system and JSON API endpoints.

## Viewers

A number of online previewers are available:

- **BT1 browser** (https://ncnr.nist.gov/ncnrdata/view/bt1browser.html) — specifically for data taken by the BT1 instrument; not useful for any other instrument.
- **Database search** (https://ncnr.nist.gov/ncnrdata/search.php) — find files by date, comment, filename, etc.
- **Experiment browser** (https://ncnr.nist.gov/ncnrdata/view/experiment_browser.html) — for instruments running NICE, DCS, and HFBS; a searchable and sortable index of experiments by user, experiment ID, title, etc.
- **ICP browser** (https://ncnr.nist.gov/ncnrdata/view/icpbrowser.html) — for data from SPINS, BT4, and old data from reflectometers.
- **BT7 browser** (https://ncnr.nist.gov/ncnrdata/view/bt7browser.html) — plots column-format data from BT7, MACS, PHADES, etc.
- **HDF5 viewer** (https://ncnr.nist.gov/ncnrdata/view/nexus-hdf-viewer.html) — allows inspection of NeXus HDF5 data from any instrument that writes those (NICE instruments).
- **nexus-zip viewer** (https://ncnr.nist.gov/ncnrdata/view/nexus-zip-viewer.html) — allows inspection of NeXus-ZIP format data from any instrument that writes those (NICE instruments).

## Metadata Search System

Metadata is extracted from every datafile collected as it is moved into the data repository, and this metadata is searchable.

- Search experiment metadata: https://www.ncnr.nist.gov/ncnrdata/metadata/search/experiments/
- Search datafile metadata: https://www.ncnr.nist.gov/ncnrdata/metadata/search/datafiles/
- REST API documentation for experiment and datafile search: https://www.ncnr.nist.gov/ncnrdata/metadata/search/api_docs.html

## Helpers (JSON API endpoints)

API endpoints are provided for retrieving JSON data from the database about files:

- **ncnrdata/findRxCycle.php**
  - Optional parameter: `timestamp` (e.g., `https://ncnr.nist.gov/ncnrdata/findRxCycle.php?timestamp=1321321231`).
  - Returns the reactor cycle (rxcycle) that matches the current timestamp, or the provided timestamp.
- **https://ncnr.nist.gov/ncnrdata/listRxCycles.php**
  - Optional parameters: `start_timestamp`, `end_timestamp`.
  - Returns a list of all rxcycles (name, start_date, end_date) that fall within the start and end timestamps.
- **https://ncnr.nist.gov/ncnrdata/listftpfiles.php**
  - Required parameter: `pathlist[]` (e.g., `["cgd", "201809", "21237", "data"]`); defaults to `[""]`.
  - Accepts POST or GET.
  - Returns file and directory metadata for the provided pathlist, including a list of subdirectories and, for all data files in the pathlist, the filename, last-modified time, and sha256.

<!-- Source: NCNR Instrument Data (https://ncnr.nist.gov/ncnrdata/). This page also covers the metadata search system and REST API relevant to COMMON-004 (NeXus/metadata reference). Boilerplate/scripts removed during normalization. -->