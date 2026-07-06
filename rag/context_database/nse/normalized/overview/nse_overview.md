---
doc_id: nse_overview
source_id: NSE-001
title: Neutron Spin Echo Spectroscopy (NSE) Overview
instrument: NSE
workflow_stage: instrument_overview_and_training
source_type: presentation_pdf
access_level: public
status: historical_reference
owner: NCNR / NIST
last_reviewed: 2026-06-15
source_url_or_path: nse_overview.pdf
source_last_updated: 2005-06-30
citation_required: false
---

# Neutron Spin Echo Spectroscopy (NSE) Overview

This note summarizes a 15-slide NCNR/NIST presentation titled **Neutron Spin Echo Spectroscopy (NSE)** by A. Faraone, D. P. Bossev, S. R. Kline, and L. Kneller. It preserves the core technical concepts, instrument layout, equations, measurement workflow, and example applications while omitting presentation chrome and direct contact details.

## Source metadata

- **Original file:** `nse_overview.pdf`
- **Original document title:** `Microsoft PowerPoint - Summer_school_NSE_instrument.ppt`
- **Author metadata:** `afaraone`
- **Created:** 2005-06-30
- **Pages:** 15
- **Page format:** letter, landscape slide orientation

## Main purpose

Neutron spin echo spectroscopy uses neutron-spin precession as an individual clock for each neutron. This allows very small energy or velocity changes to be measured directly, while still using a relatively broad and intense incident neutron beam.

NSE is presented as a technique for accessing very small energy transfers, approximately:

```text
delta E = 10^-5 to 10^-2 meV
```

The presentation emphasizes the use of **cold neutrons**, with typical wavelengths and energies:

```text
lambda = 5 to 12 Angstrom
E = 0.5 to 3.3 meV
```

Unlike classical inelastic neutron-scattering methods, which require both preparation of a monochromatic incoming beam and analysis of the scattered beam, NSE encodes the energy change in the spin phase.

## Accessible phase space

The phase-space comparison in slide 2 places NSE in a low-energy-transfer region that complements backscattering and disk-chopper spectrometers. NSE covers small delta-E values over a small-angle scattering Q range, making it useful for slow dynamics in soft matter and related systems.

## Neutrons in magnetic fields

A neutron in a magnetic field experiences torque when the field is perpendicular to the neutron spin direction. The spin precesses at the Larmor frequency:

```text
omega_L = gamma B
```

Key constants from the presentation:

```text
neutron mass, m_n = 1.675 x 10^-27 kg
spin, S = 1/2 in units of h/(2 pi)
gyromagnetic ratio, gamma = 1.832 x 10^8 s^-1 T^-1
                     = 29.164 MHz T^-1
```

The precession rate is determined by the magnetic-field strength.

## Spin echo concept

The spin echo effect is based on reversing accumulated spin phase. If a spin rotates anticlockwise and then clockwise by the same amount, it returns to its original orientation. In NSE this is achieved either by reversing the direction of the applied magnetic field or by reversing the precession angle at the midpoint using a pi flipper.

For constant neutron velocity, the final orientation is independent of the neutron speed. If the neutron velocity changes at the sample, the spin does not return to the same orientation; the phase difference is a measure of the neutron energy or velocity change.

## Monochromatic beam case

For a monochromatic beam, elastic scattering rephases the spin after the second precession arm. Inelastic scattering causes an additional phase shift because the neutron speed changes at the sample.

The slide defines the magnetic field integral:

```text
J = integral B dl
```

and states the NCNR maximum field integral:

```text
J_max = 0.5 T m
```

For an 8 Angstrom neutron wavelength, the number of precession cycles is approximately:

```text
N(lambda = 8 Angstrom) ~ 3 x 10^5
```

This large number of cycles gives NSE high sensitivity to very small velocity or energy changes.

## Polychromatic beam case

For a wavelength distribution with mean wavelength lambda_0, the number of precession cycles depends on wavelength. The presentation describes how the measured quantity is the spin component along the analysis direction, proportional to:

```text
cos(delta phi(lambda))
```

The derivation separates contributions from:

- energy change,
- asymmetry between coil field integrals,
- second-order terms, which can be neglected for small asymmetries or quasielastic scattering.

This treatment explains why NSE can use a relatively broad incident wavelength spread while retaining high energy resolution.

## NSE spectrometer schematic

The instrument schematic identifies the beamline elements in order:

1. **Velocity selector** - selects neutrons with a chosen wavelength `lambda_0`.
2. **Polarizer** - polarizing supermirrors.
3. **pi/2 flipper** - starts Larmor precession.
4. **First main solenoid** - phase and correction coils.
5. **pi flipper** - provides phase inversion.
6. **Sample**.
7. **Second main solenoid** - phase and correction coils.
8. **pi/2 flipper** - stops Larmor precession.
9. **Polarization analyzer** - radial array of polarizing supermirrors.
10. **Area detector** - 20 cm x 20 cm.

The schematic shows the neutron spin precessing through two solenoid regions with the sample between them and the pi flipper at the midpoint.

## Spin flippers

The presentation distinguishes two spin-flipper operations:

- **pi/2 flipper:** starts or stops Larmor precession by rotating the spin by 90 degrees.
- **pi flipper:** reverses the spin phase by 180 degrees, providing phase inversion at the middle of the spectrometer.

## Detector intensity and the intermediate scattering function

The measured detector intensity encodes the intermediate scattering function:

```text
I(Q, t)
```

For a wavelength distribution `f(lambda)` with mean wavelength `lambda_0`, the measured polarization includes a wavelength average and a cosine transform of the dynamic structure factor `S(Q, omega)`.

The presentation defines the NSE time approximately as:

```text
t = N_0 m lambda^3 / (h lambda_0)
```

The slide notes that at small `N_0`, varying `Delta N_0` provides diagnostic information:

- the oscillation period gives `lambda_0`,
- the envelope gives the wavelength distribution `f(lambda)`.

## Measuring I(Q,t)

The measurement example uses a 10 % SDS in D2O sample at:

```text
Q = 0.13899 Angstrom^-1
t = 1 ns
```

The measurement compares flipper-on and flipper-off conditions:

```text
N_ON  = counts with flipper on
N_OFF = counts with flipper off
```

The slide states:

- the difference between flipper ON and flipper OFF data gives `I(Q,0)`,
- the echo is fit to a Gaussian-damped cosine,
- the instrumental signal before resolution correction is proportional to:

```text
2A / (N_ON - N_OFF)
```

where `A` is the fitted echo amplitude.

## Resolution correction

The time-domain resolution correction is described as a division:

```text
J(Q,t) = I(Q,t) R(Q,t)
I(Q,t) = J(Q,t) / R(Q,t)
```

The presentation explains that magnetic-field inhomogeneities can further reduce polarization. Because these effects are not correlated with `S(Q, omega)` or `f(lambda)`, they can be divided out by measuring the polarization from a purely elastic scatterer.

## Main applications

The presentation states that the main application of NSE is measurement of the **intermediate coherent scattering function**:

```text
I_coh(Q,t)
```

This corresponds to coherent density fluctuations associated with a SANS intensity pattern. Example application areas include:

- diffusion,
- internal dynamics,
- shape fluctuations.

## Example: diffusion of surfactant molecules

The first example considers AOT micelles in deuterated decane (`C10D22`). The diagram identifies:

- AOT surfactant molecules,
- hydrophobic tails,
- hydrophilic heads,
- inverse spherical micelles,
- approximately 25 AOT molecules per micelle,
- translational diffusion.

The intermediate scattering function for translational diffusion is shown as:

```text
I(Q,t) / I(Q,0) = exp[-D_eff Q^2 t]
```

where `D_eff` is an effective diffusion coefficient.

## Example: shape fluctuations in inverse microemulsion droplets

The second application is shape fluctuations in an inverse microemulsion droplet:

```text
AOT / D2O / C6D14
```

The slide separates contributions from:

- translational diffusion,
- shape fluctuations,
- deformation dynamics.

It writes the effective diffusion coefficient as a sum of translational and deformation terms:

```text
D_eff(Q) = D_tr + D_def(Q)
```

The goal is to extract the **bending modulus of elasticity**. Parameters identified in the final slide include:

- `lambda_2`: damping frequency or frequency of deformation,
- `<|a_2|^2>`: mean-square displacement of the second harmonic, or amplitude of deformation,
- `p_2`: size polydispersity, measurable by SANS or DLS,
- `eta`: bulk viscosity of deuterated n-hexane,
- `eta'`: bulk viscosity of deuterated water.

## Practical takeaways

NSE provides high energy resolution by measuring spin phase rather than directly monochromatizing and energy-analyzing every neutron. The instrument uses a velocity selector, polarizer, spin flippers, solenoids, sample, analyzer, and detector to encode and decode neutron energy changes. The data-reduction workflow extracts `I(Q,t)` from spin-echo measurements and corrects it using a resolution measurement from an elastic scatterer.

## Source-cleaning notes

The original PDF is a 2005 presentation with slides, diagrams, equations, and example plots. This Markdown version preserves the main slide sequence and scientific content. Direct email/contact details and visual presentation styling were intentionally omitted. Some equations in the PDF were embedded as low-fidelity extracted text; equations here are normalized only where the meaning is clear from the slide content.
