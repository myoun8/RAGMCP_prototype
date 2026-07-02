---
doc_id: fitting_polarized_neutron_reflectometry_data_beginners_guide
source_id: COMMON-012
title: Fitting Polarized Neutron Reflectometry Data: A Beginner's Guide
instrument: COMMON
workflow_stage: data_analysis
source_type: web_page
access_level: public
status: current
owner: NCNR
last_reviewed: 2026-07-02
source_url_or_path: https://www.nist.gov/ncnr/fitting-polarized-neutron-reflectometry-data-beginners-guide
source_last_updated: 2023-06-09
citation_required: false
software: Refl1D
---

# Fitting Polarized Neutron Reflectometry Data: A Beginner's Guide

This guide is intended to provide NIST Center for Neutron Research (NCNR) users with a non-rigorous introduction to fitting polarized neutron reflectometry (PNR) data, focusing mainly on the practical elements of analyzing PNR with the Refl1D software.

For users seeking a more detailed treatment or derivation of PNR formalism starting from the wave equations, the following resources are available on the NCNR website:
* Work of Majkrzak, O’Donovan, and Berk
* Work of Fitzsimmons and Majkrzak

For questions regarding this guide or general fitting inquiries, contact: [contact details omitted].

## Installing and Running Refl1D

Instructions for setting up and running Refl1D and its full detailed documentation are available via the provided links in the source material.

## PNR Analysis Basics

This section covers the features that appear in PNR data and the information contained within those features. It outlines "best practices" for fitting data, including:
* Distinguishing between a good fit and a bad fit.
* Determining sensitivity to specific fitting parameters.
* Properly evaluating uncertainty.

Key topics include:
* Understanding PNR Data Features
* PNR Models and Fitting Basics
* Fitting Tips and Best Practices
* Evaluating Fits and Uncertainty Analysis

## Refl1D Fitting Examples

To analyze PNR data with the Refl1D program, users must load an analysis script. This Python-based script defines the theoretical model used for fitting by:
* Determining the number of layers within the thin film structure.
* Setting initial guesses for parameters (e.g., thicknesses).
* Selecting which parameters will be fit.
* Constraining parameters to user-selected ranges.

The following example scripts are provided to help users learn Refl1D syntax or modify scripts for their own needs. These examples are presented in order of increasing complexity.

*Note: These models may be simplified for instructional purposes and may deviate from models used in formal publications. Modeling choices may be informed by supplemental measurements such as X-ray reflectometry, X-ray diffraction, bulk magnetometry, or magnetic X-ray spectroscopy.*

### Simple Models
* Simple film and magnetic dead layers
* Multilayer magnetic heterostructure
* Multilayer magnetic heterostructure with spin-flip scattering
* Magnetic superlattice

### Advanced Models
* User-defined functional shapes
* Spline with control points
* Dataset with multiple temperatures
* Sample with multiple distinct regions

<!-- Source: Fitting Polarized Neutron Reflectometry Data: A Beginner's Guide (https://www.nist.gov/ncnr/fitting-polarized-neutron-reflectometry-data-beginners-guide). Removed site navigation, header/footer chrome, social media links, and personal email address. -->
