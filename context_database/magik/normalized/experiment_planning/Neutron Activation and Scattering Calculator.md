---
doc_id: neutron_activation_and_scattering_calculator
source_id: MAGIK-006
title: Neutron Activation and Scattering Calculator
instrument: MAGIK
workflow_stage: experiment_planning
source_type: web_page
access_level: public
status: current
owner: [contact details omitted]
last_reviewed: 2026-07-02
source_url_or_path: context_database\magik\originals\web_pages\Neutron Activation and Scattering Calculator.html
citation_required: false
---

# Neutron Activation and Scattering Calculator

This calculator uses neutron cross sections to compute activation of the sample given the mass in the sample and the time in the beam, and to perform absorption and scattering calculations for samples on slow neutron beamlines (energy below 325 meV, wavelength above 0.05 nm).

## Usage Overview

1. **Material Specification**: Enter the sample formula in the material panel.
2. **Activation Calculations**: Fill in the thermal flux, mass, and time on/off the beam, then press the calculate button in the neutron activation panel.
3. **Scattering Calculations**: Fill in the wavelength of the neutron and/or x-rays, the thickness, and the density (if not specified in the formula), then press the calculate button in the absorption and scattering panel.

## Chemical Formula Parser

The chemical formula parser allows the specification of materials and mixtures using the `periodictable` Python package.

### Basic Formulas
* **Simple Formula**: Basic elements and quantities (e.g., `CaCO3`).
* **Multi-part Formula**: Parts separated by `+` or spaces. Numbers before a part represent repeats; parentheses treat a group as a single unit. 
    * Examples: `CaCO3+6H20`, `CaCO3 6H2O`, and `CaCO3(H2O)6` all represent ikaite ($\text{CaCO}_3 \cdot 6\text{H}_2\text{O}$).

### Isotopes and Special Symbols
* **Nuclide Index**: Represented as `element[nuclide index]` (e.g., `O[18]` for $^{18}\text{O}$).
* **Special Symbols**: `D` and `T` can be used for $^2\text{H}$ and $^3\text{H}$.
* **Mixed Isotopes**: e.g., `DHO` for partially deuterated water.
* **Labile Hydrogen**: Use `H[1]` in formulas. These are substituted with H and D in proportion with the $\text{D}_2\text{O}$ fraction when computing contrast match points.
* **Complex Example**: `C3H4H[1]NO@1.29n` represents alanine with one labile hydrogen.

### Density Specifications
Mass density is required for scattering factors.
* **Formula Suffix**: Add `@value` to the end of the formula (e.g., `H2O@1` for $1\text{ g/cm}^3$).
* **Isotopic Density**: 
    * If using natural abundance density as a base to scale to isotope specific density, add `n` (e.g., `D2O@1n`).
    * If the isotopic density is known, use the value alone (e.g., `D2O@1.11`).
    * `D2O@1.11i` also indicates $1.11\text{ g/cm}^3$.

### Mixture Types
* **Mole Fractions**: Use non-integer quantities (e.g., `78.2H2O[16] + 21.8H2O[18] @1n`).
* **Mass Fractions**: Use `%wt` for the first part, followed by `//` for subsequent parts.
    * Example: `50%wt Co // Ti` (50% Cobalt, 50% Titanium).
    * Example: `33%wt Co // 33% Fe // Ti` (1:1:1 mixture by mass).
* **Volume Fractions**: Use `%vol`. Each component must specify density.
    * Example: `20%vol (10%wt NaCl@2.16 // H2O@1) // D2O@1n`.
* **Specific Amounts**: Mix by mass (kg, g, mg, ug, ng) or volume (L, mL, uL, nL) using `//`.
    * Example: `5g NaCl // 50mL H2O@1`.
    * Example: `50 mL (45 mL H2O@1 // 5 g NaCl)@1.0707 // 20 mL D2O@1n`.

### Advanced Material Specifications
* **Layer Thickness**: Specified as `thickness material // thickness material`. Thickness units: cm, mm, um, nm. 
    * Example: `1 cm Si // 5 nm Cr // 10 nm Au`.
* **Biomolecules (FASTA)**: Use `code:sequence` (aa: amino acid, dna: DNA, rna: RNA). Density is estimated automatically.

## Calculation Parameters

### Thermal Flux
* **Units**: $\text{n/cm}^2/\text{s}$
* **Scaling**: For most isotopes, scale the flux by $\lambda / 1.798\text{ \AA}$, where $\lambda$ is the average wavelength at the sample weighted by spectral intensity.
* **Notes**: 
    * Activation is calculated per isotope.
    * Data sources: IAEA handbook (1987), IUPAC 2021 atomic weights, and NUBASE2020 for half-lives.
    * For fluences $> 10^{16}\text{ n/cm}^2$, results may be erroneous due to precision limits; calculate at lower flux and proportion the result.

### Cadmium Ratio and Thermal/Fast Ratio
* **Cadmium Ratio**: Used for rabbit systems to reduce thermal flux. Use `0` for beamline experiments.
* **Thermal/Fast Ratio**: Used for rabbit tubes to determine fast neutron flux: $\text{Fast Flux} = \text{Thermal Flux} / \text{Thermal/Fast Ratio}$. Use `0` for beamline experiments.

### Material Mass and Exposure
* **Mass Units**: g, kg, mg, ug.
* **Exposure Units**: h, m, s, d, w, y. (1 year = 365 days).
* **Assumptions**: Thin plate sample, full flux exposure, no self-shielding.

### Decay
The decay field specifies time since removal from the beam.
* **Relative Time**: `2 m` (2 minutes ago), `2.5w` (2.5 weeks ago).
* **Absolute Time**: `yyyy-mm-dd hh:mm:ss` (US/Eastern unless `Z` for UTC or offset is provided).
* **Date Only**: `2010-03` is interpreted as the end of the month (`2010-03-31 23:59:59`) for conservative estimates.

### Mass Density (Detailed)
* **Units**: $\text{g/cm}^3$ or $\text{\AA}^3$.
* **Cell Volume**: Enter number followed by `A3` (e.g., `179.4 A3`).
* **Lattice Parameters**: Format `a:n b:n c:n alpha:n beta:n gamma:n`. Defaults: $b=a, c=a, \alpha=\beta=\gamma=90^\circ$.

### Thickness and Source Energy
* **Thickness**: Units in cm. Used for transmission and absorption.
* **Source Neutrons**: Wavelength ($\text{\AA}$), energy (meV), or velocity (m/s).
    * Cross sections tabulated at $1.798\text{ \AA} = 25.3\text{ meV} = 2200\text{ m/s}$.
    * Includes energy-dependent coherent and absorption cross sections for common rare-earth isotopes (Lynn and Seeger 1992).
* **Source X-rays**: Wavelength ($\text{\AA}$), energy (keV), or element name for $\text{K}_\alpha$ line.

## Activation Calculation Notes

### Reaction Notation
* **`Reaction = b`**: Beta produced daughter of an activated parent.
* **`m, m1, m2`**: Metastable states.
* **`+`**: Radioactive daughter production already included in daughter listing.
* **`*`**: Radioactive daughter production NOT calculated; approx. secular equilibrium.
* **`s`**: Radioactive daughter in secular equilibrium.
* **`t`**: Transient equilibrium via beta decay.

### General Limitations
* Numerical precision for very large half-lives may result in negative values ($\exp(x)$ limited to $|x| < 709$).
* No correction for neutron burn up.

## URL Parameter Controls

| Parameter | URL Suffix | Description |
| :--- | :--- | :--- |
| Isotope Abundance | `?abundance=IUPAC` | Use IUPAC 2021 instead of IAEA 1987. |
| Activation Cutoff | `?cutoff=0` | Display all activation levels (default $0.0005\text{ \mu Ci}$). |
| Decay Cutoff | `?decay=0.1` | Set time for activation to decay to specified value (e.g., $0.1\text{ \mu Ci}$). |

## References

* **CIAAW**: Isotopic compositions of the elements 2021. [www.ciaaw.org](http://www.ciaaw.org)
* **Deslattes et al. (2003)**: Rev. Mod. Phys. 75, 35-99. (X-ray emission lines).
* **Henke et al. (1993)**: Atomic Data and Nuclear Data Tables Vol. 54. (X-ray cross sections).
* **IAEA (1987)**: Handbook on Nuclear Activation Data, TR 273.
* **Kienzle, P. A. (2008)**: Extensible periodic table. [https://periodictable.readthedocs.io](https://periodictable.readthedocs.io)
* **Lynn & Seeger (1990)**: Atomic Data and Nuclear Data Tables 44, 191-207. (Rare earth scattering).
* **Rauch & Waschkowski (2003)**: ILL Neutron Data Booklet. (Neutron cross sections).
* **Sears, V. F. (2006)**: International Tables for Crystallography Volume C. (Scattering calculations).
* **Shleien et al. (1998)**: Handbook of health physics and radiological health. (Activation data).
* **Kondev et al. (2021)**: Chin. Phys. C45, 030001. (NUBASE2020 half-life data).

<!-- Source: Neutron Activation and Scattering Calculator. Removed navigation menus, CSS/JS links, site headers, footers, and the "Initializing calculator..." status message. -->
