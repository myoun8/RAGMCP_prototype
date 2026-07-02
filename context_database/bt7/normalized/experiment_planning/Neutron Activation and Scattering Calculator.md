---
doc_id: neutron_activation_and_scattering_calculator
source_id: BT7-010
title: Neutron Activation and Scattering Calculator
instrument: BT7
workflow_stage: experiment_planning
source_type: web_page
access_level: public
status: current
owner: NCNR
last_reviewed: 2026-07-02
source_url_or_path: context_database\bt7\originals\web_pages\Neutron Activation and Scattering Calculator.html
citation_required: false
---

# Neutron Activation and Scattering Calculator

This calculator uses neutron cross sections to compute the activation of a sample given its mass and the time spent in the beam. It also performs absorption and scattering calculations for samples on slow neutron beamlines (energy below 325 meV, wavelength above 0.05 nm).

## Usage Instructions

### Activation Calculations
1. Enter the sample formula in the **Material** panel.
2. Fill in the **Thermal flux**, **Mass**, and the **Exposure** and **Decay** times.
3. Press the calculate button in the **Neutron Activation** panel.

### Scattering Calculations
1. Fill in the **Wavelength** of the neutrons and/or X-rays.
2. Provide the **Thickness** and **Density** (if not specified in the formula).
3. Press the calculate button in the **Absorption and Scattering** panel.

## Material Formula Specification

The calculator uses the `periodictable` Python package for formula parsing.

### Basic Formulas
*   **Simple Formula:** Elements and their quantities (e.g., `CaCO3`).
*   **Multi-part Formula:** Parts separated by `+` or space. Use parentheses for units. 
    *   Example: `CaCO3+6H20`, `CaCO3 6H2O`, and `CaCO3(H2O)6` all represent ikaite ($\text{CaCO}_3 \cdot 6\text{H}_2\text{O}$).
*   **Isotopes:** Represented as `element[nuclide index]`.
    *   `D` and `T` are shortcuts for $^2\text{H}$ and $^3\text{H}$.
    *   `DHO` represents partially deuterated water.
    *   `H[1]` represents labile hydrogen (substituted with H and D based on $\text{D}_2\text{O}$ fraction for contrast match point calculations).
    *   `O[18]` represents $^{18}\text{O}$.
    *   Example: `C3H4H[1]NO@1.29n` represents alanine with one labile hydrogen.

### Density Specification
Density is required for scattering factors.
*   **Formula-based:** Add `@value` to the end of the formula (e.g., `H2O@1` for $1\text{ g/cm}^3$).
*   **Isotopic Density:** 
    *   `@value n`: Scales the natural abundance density to the isotope-specific density (e.g., `D2O@1n`).
    *   `@value`: Uses the specific value provided (e.g., `D2O@1.11`).
*   **Cell Volume:** Enter a number followed by `A3` for $\text{\AA}^3$ (e.g., `4NaCl` with `179.4 A3`).
*   **Lattice Parameters:** Format as `a:n b:n c:n alpha:n beta:n gamma:n` (a, b, c in $\text{\AA}$; angles in degrees). 
    *   Example: `4NaCl` cubic lattice with `a:5.6402`.

### Mixtures and Complex Samples
*   **Mole Fractions:** Use non-integer quantities (e.g., `78.2H2O[16] + 21.8H2O[18] @1n`).
*   **Mass Fractions:** Use `%wt` for the first part, separated by `//`.
    *   Example: `50%wt Co // Ti` (50% Cobalt, 50% Titanium by mass).
*   **Volume Fractions:** Use `%vol`. Each component must specify density.
    *   Example: `20%vol (10%wt NaCl@2.16 // H2O@1) // D2O@1n`.
*   **Specific Quantities:** Mix masses (kg, g, mg, ug, ng) or volumes (L, mL, uL, nL) separated by `//`.
    *   Example: `5g NaCl // 50mL H2O@1`.
*   **Layer Thickness:** Specified as `thickness material // thickness material`. Thickness units: cm, mm, um, nm.
    *   Example: `1 cm Si // 5 nm Cr // 10 nm Au`.
*   **Biomolecules (FASTA):** Use `code:sequence` (`aa` for amino acids, `dna` for DNA, `rna` for RNA).
    *   Example: `aa:RELEEL...`

## Calculation Parameters

### Neutron Activation
*   **Thermal Flux (n/cm²/s):** Provide the pre-sample beam configuration flux. Scale by $\lambda/1.798\text{ \AA}$ for most isotopes.
*   **Cadmium Ratio:** Used for rabbit system shielding to reduce thermal flux. Use `0` for beamline experiments.
*   **Thermal/Fast Ratio:** Used for rabbit tubes to determine fast neutron flux. $\text{Fast Flux} = (\text{Thermal Flux}) / (\text{Thermal/Fast Ratio})$. Use `0` for beamline experiments.
*   **Material Mass:** (g, kg, mg, ug). Assumes a thin plate sample with no self-shielding.
*   **Exposure:** Duration of exposure. Units: `h` (hours), `m` (minutes), `s` (seconds), `d` (days), `w` (weeks), `y` (years).
*   **Decay:** Time since removal from beam. Supports relative durations (e.g., `2m`, `2.5w`) or absolute timestamps (`yyyy-mm-dd hh:mm:ss`).

### Absorption and Scattering
*   **Thickness (cm):** Used for transmission and incoherent scattering.
*   **Source Neutrons:** Specified as wavelength ($\text{\AA}$), energy (meV), or velocity (m/s).
    *   Reference values: $1.798\text{ \AA} = 25.3\text{ meV} = 2200\text{ m/s}$.
    *   Rare-earth resonance data from Lynn and Seeger (1992) is used for $\lambda < 1\text{ \AA}$.
*   **Source X-rays:** Specified as wavelength ($\text{\AA}$), energy (keV), or element name for $\text{K}_\alpha$ line.

## Technical Notes & Limitations

*   **Precision:** For fluences $> 10^{16}\text{ n/cm}^2$, numerical precision may lead to errors. Perform calculations at lower flux and proportion the results.
*   **Reaction Notation:**
    *   `b`: Production via beta decay of an activated parent.
    *   `m, m1, m2`: Metastable states.
    *   `+`: Radioactive daughter production already included in listing.
    *   `*`: Radioactive daughter production NOT calculated (approx. secular equilibrium).
    *   `s`: Radioactive daughter in secular equilibrium.
    *   `t`: Transient equilibrium via beta decay.
*   **Cross-Section Sources:**
    *   Activation: IAEA Handbook (1987).
    *   Scattering: IUPAC 2021 (CIAAW).
    *   Half-lives: NUBASE2020.
    *   X-ray: Henke (1993).

## Reference Implementation Details (URL Parameters)
The calculator behavior can be modified via URL queries:
*   `?abundance=IUPAC`: Uses IUPAC 2021 instead of IAEA 1987.
*   `?cutoff=0`: Displays all activation levels (default is $0.0005\text{ \mu Ci}$).
*   `?decay=0.1`: Sets the decay cutoff to $0.1\text{ \mu Ci}$.

## References
*   CIAAW. Isotopic compositions of the elements 2021. [www.ciaaw.org](http://www.ciaaw.org)
*   Deslattes, R.D., et al. (2003). Rev. Mod. Phys. 75, 35-99.
*   Henke, B.L., et al. (1993). Atomic Data and Nuclear Data Tables Vol. 54 (no.2), 181-342.
*   IAEA (1987). Handbook on Nuclear Activation Data. TR 273.
*   Kienzle, P. A. (2008). Extensible periodic table. [https://periodictable.readthedocs.io](https://periodictable.readthedocs.io)
*   Lynn, J.E. and Seeger, P.A. (1990). Atomic Data and Nuclear Data Tables 44, 191-207.
*   Rauch, H. and Waschkowski, W. (2003). ILL Neutron Data Booklet (2nd ed).
*   Sears, V. F. (2006). International Tables for Crystallography Volume C.
*   Shleien, B., et al. (1998). Handbook of health physics and radiological health.
*   Kondev, F.G., et al. (2021). Chin. Phys. C45, 030001.

<!-- Source: Neutron Activation and Scattering Calculator. Removed website navigation, JS/CSS references, and UI labels ("Initializing calculator...", etc.). -->
