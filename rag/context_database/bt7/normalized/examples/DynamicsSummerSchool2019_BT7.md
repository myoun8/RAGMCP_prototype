---
doc_id: dynamicssummerschool2019_bt7
source_id: BT7-002
title: Magnetic Phase Transition and Spin Wave Excitations in the Colossal Magnetoresistive Manganites: An Experiment Using the BT7 Triple-Axis Spectrometer
instrument: BT7
workflow_stage: examples
source_type: presentation_pdf
access_level: public
status: current
owner: [contact details omitted]
last_reviewed: 2026-07-02
source_url_or_path: DynamicsSummerSchool2019_BT7.pdf
citation_required: true
---

# Magnetic Phase Transition and Spin Wave Excitations in the Colossal Magnetoresistive Manganites: An Experiment Using the BT7 Triple-Axis Spectrometer

**Objectives:** The summer school participants will use elastic scattering to measure the ferromagnetic order parameter and transition temperature, and inelastic neutron scattering measurements to study the spin wave excitations in the perovskite $\text{La}_{0.7}\text{Sr}_{0.3}\text{MnO}_3$. This system demonstrates the versatility and power of triple-axis spectrometry in studying the static and dynamic properties of condensed matter systems.

## I. Introduction to the System

The $\text{LaMnO}_3$ class of materials is based on a cubic perovskite system where the $\text{Mn}$ ion is surrounded by six oxygen ions with octahedral symmetry, with $\text{La}$ ions on a simple cubic lattice.

### Material Properties
*   **$\text{LaMnO}_3$:** An antiferromagnetic insulator ($T_N = 140\text{ K}$).
*   **Doped Manganites ($\text{La}_{1-x}A_x\text{MnO}_3$):** Substituting $2+$ cations (Ca, Sr, Ba) for $\text{La}^{3+}$. For $0.2 < x < 0.5$, the material becomes an isotropic, metallic ferromagnet at low temperatures.
*   **Colossal Magnetoresistance (CMR):** The magnetic ordering (Curie) temperature is accompanied by a metal-insulator transition. The electrical resistivity changes by several orders of magnitude upon the application of a magnetic field.
*   **$\text{La}_{0.7}\text{Sr}_{0.3}\text{MnO}_3$:** The specific material examined, where doped holes induce ferromagnetism and metallic conductivity.

### Physics of Conductivity and Magnetism
In the cubic crystal environment, $\text{Mn}^{3+}$ ions (with four $d$-electrons) experience crystal field splitting into three degenerate $t_{2g}$ orbitals and two degenerate $e_g$ orbitals. 
*   **Hund's Rule:** Three electrons occupy $t_{2g}$ orbitals, and the fourth occupies an $e_g$ level, all with parallel spins (localized magnetic moment $S=3/2$).
*   **Jahn-Teller Effect:** $\text{Mn}^{3+}$ is Jahn-Teller active; distortion of the oxygen octahedron breaks the $e_g$ degeneracy to lower the system's energy.
*   **Double Exchange:** Replacing $\text{La}^{3+}$ with $\text{Sr}^{2+}$ creates $\text{Mn}^{4+}$ ions (unoccupied $e_g$ orbital). $e_g$ electrons can hop between $\text{Mn}^{3+}$ and $\text{Mn}^{4+}$ sites via oxygen orbitals. This hopping is maximized when spins are aligned ferromagnetically, providing the physical basis for ferromagnetism in these manganites.

## II. The BT-7 Triple-Axis Spectrometer

The BT-7 is a flexible triple-axis spectrometer used to study both static and dynamic properties.

### Instrumental Configuration
*   **Monochromators:** Choice of copper [$\text{Cu}(220)$] or pyrolytic graphite [$\text{PG}(002)$] doubly-focusing monochromators.
*   **Energy Range:** Continuous incident neutron energy from $5$ to $500\text{ meV}$.
*   **Flux:** Reflecting area of $400\text{ cm}^2$, providing fluxes up to $10^8\text{ n/cm}^2/\text{s}$.
*   **Sample Stage:** Includes two coaxial rotary tables (sample rotation and magnetic field coil rotation), a computer-controlled goniometer, and an elevator.
*   **Polarization:** $\text{He}^3$ cells available for neutron polarization.
*   **Analyzer/Detection:** Interchangeable systems including:
    *   Multi-strip $\text{PG}(002)$ analyzer array (horizontally focused or flat).
    *   Linear position-sensitive detector (PSD) or Söller collimators.
    *   Diffraction detector for Bragg peak measurements.
    *   11 embedded detectors for continuous flux monitoring.

### General Specifications for BT-7
| Feature | Specification |
| :--- | :--- |
| **Filter** | PG filter in reactor beam (remotely insertable/tunable) |
| **Monochromators** | $\text{PG}(002)$ ($d=3.35416\text{ \AA}$) or $\text{Cu}(220)$ ($d=1.273\text{ \AA}$) |
| **Analyzer** | Flat PG or horizontally focused PG (13 blades, $2\text{ cm}$ wide each) |
| **Polarization** | Built-in guide fields, insertable spin rotators, $\text{He}^3$ polarizers |
| **Take-off angles** | $2\theta$ from $16^\circ$ to $75^\circ$ |
| **Incident Energy** | $5.0$ to $500\text{ meV}$ |
| **Scattering Angles** | $0$ to $120^\circ$ |
| **Collimation** | Söller slits: $10'$, $25'$, $50'$, $80'$, and open |
| **Additional** | Radial collimators available before/after analyzer; computer-controlled guide fields |

## III. Experiment and Analysis

### Simple Ferromagnetic Spin-Waves
Based on the Heisenberg Hamiltonian, the interaction energy between two neighboring spins is:
$$E = -2J S_i \cdot S_j$$
where $J$ is the exchange constant. For $J > 0$, the ground state is ferromagnetic.

Spin-wave excitations are collective precessions of spins. The dispersion relation for nearest-neighbor exchange is:
$$E_{SW} = 8JS \left( 1 - \cos(qa) \right) = 8JS \sin^2\left(\frac{qa}{2}\right)$$
For small $q$ (long wavelength), this approximates to:
$$E_{SW} = 2JSa^2q^2$$
Magnetic anisotropy is represented by a gap parameter $\Delta$. In "soft" ferromagnets, $\Delta$ is small.

### Temperature Dependent Properties
The ordered magnetic moment (magnetization) vanishes at the Curie temperature $T_C$ following a power law:
$$M(T) \propto \left( 1 - \frac{T}{T_C} \right)^\beta$$
with $\beta \approx 0.3$.

The integrated intensity for a magnetic Bragg reflection is:
$$I(\tau) \propto \left( \hat{\tau} \cdot \hat{M} \right)^2 \frac{1}{V} \sum_j \langle S_j \rangle^2 f(\tau)^2 W_j$$
where $f(\tau)$ is the magnetic form factor.

In the small $q$ regime, the spin-wave dispersion is:
$$E_{spinwaves}(q, T) = \Delta(T) + D(T)q^2 + \dots$$
where $D$ is the spin-wave stiffness parameter. As $T \to T_C$, $D(T)$ follows a power law $\propto (1 - T/T_C)^{\beta\nu'}$.

### Experimental Planning and Setup
**Sample:** $\approx 4\text{g}$ single crystal of $\text{La}_{0.7}\text{Sr}_{0.3}\text{MnO}_3$ in an aluminum container.
**Environment:** $\text{He}$ closed-cycle refrigerator/furnace ($30\text{--}600\text{ K}$).
**Crystallography:** Space group $cR3$; lattice parameters $a=b=5.5084\text{ \AA}, c=13.3717\text{ \AA}, \gamma = 120^\circ$ (Hexagonal) or $a=b=c=3.8835\text{ \AA}, \alpha=\beta=\gamma=90.344^\circ$ (Rhombohedral).

**Procedure:**
1.  **Bragg Peak Measurement:** Measure integrated intensity of $(1\ 0\ 0)$ peak from $250\text{--}400\text{ K}$ via transverse ($\theta$) and longitudinal ($\theta:2\theta$) scans to extract $T_C$.
2.  **Spin Wave Spectrum:** Scan incident energy at several $Q$ points up to $E \approx 10\text{ meV}$ to determine $D(T)$.
3.  **Quasielastic Intensity:** Measure intensity near $(1\ 0\ 0)$ through $T_C$ to study spin dynamics.

### Data Analysis
*   **Constant-Q Scans:** Typically show a central (quasi)elastic peak and two inelastic spin-wave peaks (energy loss and gain).
*   **Fitting:** Peaks are fit with Gaussian (small intrinsic linewidth) or Lorentzian (large intrinsic linewidth) functions.
*   **Quasielastic Peaks:** Intensity above $T_C$ arises from paramagnetic spin fluctuations; below $T_C$, it is mostly from spin waves.

### Polarized Neutron Scattering
To unambiguously discriminate magnetic scattering from nuclear scattering:
*   **Nuclear Scattering:** Always non-spin-flip (NSF).
*   **Magnetic Scattering:** Can reverse (flip) the neutron spin (SF).
Polarization analysis confirms if the signal is due to spin waves (SF) or spin diffusion/nuclear scattering (NSF).

## IV. Summary
Neutron scattering provides a comprehensive determination of magnetic properties:
*   **Elastic Scattering:** Determines order parameter, magnetic structure, and spin direction.
*   **Inelastic Scattering:** Determines fundamental exchange interactions, spin-wave stiffness, and lifetimes.
*   **Polarization Analysis:** Distinguishes between magnetic and nuclear origins of scattering.

## V. References
[1] N. Nagaosa, and Y. Tokura, Science 288, 462 (2000); E. Dagotto, Science 309, 257 (2005).
[2] A. Urushibara et al., Phys. Rev. B51, 14103 (1995).
[3] J. W. Lynn et al., Journal of Research of NIST 117, 61-79 (2012).
[4] L. Vasiliu-Doloc et al., Phys. Rev. B58, 14913 (1998).
[5] L. Vasiliu-Doloc et al., J. Appl. Phys. 83, 7342 (1998).
[6] J. W. Lynn, J. Appl. Phys. 75, 6806 (1994).
[7] C. P. Adams et al., Phys. Rev. B70, 134414 (2004).
[8] C. P. Adams et al., Phys. Rev. Lett. 85, 3954 (2000).
[9] J. W. Lynn et al., J. Appl. Phys. 89, 6846 (2001).
[10] J. W. Lynn et al., Phys. Rev. B 76, 014437 (2007).
[11] Y. Chen et al., Phys. Rev. B 78, 212301 (2008).
[12] F. Ye et al., Phys. Rev. Lett. 96, 047204 (2006); S. Petit et al., Phys. Rev. Lett. 102, 207201 (2009); J. S. Helton et al., Phys. Rev. B 99, 024407 (2019).

<!-- Source: Magnetic Phase Transition and Spin Wave Excitations in the Colossal Magnetoresistive Manganites: An Experiment Using the BT7 Triple-Axis Spectrometer. Removed page numbers, repetitions of "Question" boxes embedded in text, and references to separate experiment handouts. -->
