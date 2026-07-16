---
doc_id: magik_experiment
source_id: MAGIK-002
title: MAGIK Experiment: Composition Depth Profile in Hydrated Polymer Electrolyte Films
instrument: MAGIK
workflow_stage: examples
source_type: web_page
access_level: public
status: deprecated
owner: NCNR
last_reviewed: 2026-07-02
source_url_or_path: https://www.nist.gov/ncnr/2018-summer-school-fundamentals-neutron-scattering/course-materials/experiment-handouts/magik
source_last_updated: 2026-05-27
citation_required: false
software: Refl1D
---

# MAGIK Experiment: Composition Depth Profile in Hydrated Polymer Electrolyte Films

> DEPRECATION NOTICE: This page is no longer being updated and the information may be out of date.

## Abstract
Neutron Reflectometry with isotopic substitution will be used to determine the water volume fraction and polymer SLD, independent of any assumptions, in thin films of Nafion. The objective of these measurements is to provide hands-on experience in neutron reflectometry data collection, reduction, fitting and subsequent analysis. In doing so, the student will gain insights into the capability of neutron reflectometry to determine the composition depth profile of a variety of thin film samples and the design of reflectometry experiments.

## 1 Objectives
The objectives of this experiment are to:
* Determine the depth profile of scattering length density (SLD) in a thin film of Nafion deposited on the native oxide, $\text{SiO}_2$ on a Si substrate in the presence of water vapor at relative humidity, $\text{RH}=92\%$ in both $\text{H}_2\text{O}$ and $\text{D}_2\text{O}$, and at $\text{RH}=0\%$ after drying.
* Use the concept of contrast variation to determine the depth profiles both of the water volume fraction and of the solid polymer SLD.
* Learn how to perform a neutron reflectometry experiment, including planning, sample preparation, data collection, reduction, fitting, analysis, and interpretation.
* Gain experience that will allow one to determine how to apply neutron reflectometry to one’s own research interests.

## 2 Introduction
Nafion is a widely used polymer electrolyte membrane material consisting of a hydrophobic fluorocarbon backbone with a flexible perfluorinated vinyl ether side chain terminated by a sulfonic acid group. In the presence of water, these components phase segregate into water-rich and water-poor domains.

### Morphological Characteristics
* **Bulk Nafion:** Domains typically consist of cylinders of water in a fluorocarbon matrix.
* **Interface Effects:** Hydrophilic surfaces such as $\text{SiO}_2$ induce a lamellar phase (water-rich layer at the interface followed by a Nafion-rich layer, repeating for roughly 5 layers).
* **Metallic Surfaces:** Less hydrophilic surfaces like Au and Pt typically exhibit only a single water-rich layer at the interface.

### Hydration Regimes
Research has identified three regimes based on film thickness:
1. **Lamellar Regime:** Sample is truncated at thicknesses including only lamellae (moderate water uptake).
2. **Thin Film Regime:** A non-lamellar layer (thickness up to the radius of gyration, $R_g$) occurs on top of the lamellar region; water uptake increases linearly with thickness.
3. **Thick Film Regime:** The top layer exceeds $R_g$ and exhibits bulk-like water uptake, while lamellae maintain higher uptake.

## 3 Experimental

### 3.1 Sample Preparation
Si substrates (5mm thick, 76.2mm diameter) are cleaned and rinsed with DI water to be highly hydrophilic. Nafion thin films are spin-coated from a commercial dispersion diluted with HPLC grade ethanol. Samples are vacuum annealed at 60 °C for one hour to ensure adhesion and thermal history consistency.

### 3.2 Sample Environment
Measurements are performed using a specially designed controlled-humidity sample environment.
* **Gas Path:** Dry Ar carrier gas passes through a dew point generator (DPG) and a heated line to prevent condensation.
* **Sample Housing:** A temperature-controlled Al cylinder positioned on the goniometer stage.
* **Temperature Control:** Managed via resistive cartridge heaters and a coolant loop (ethylene glycol/water mixture). Stability is maintained within $\pm 0.02\text{ °C}$ of the set point.
* **RH Determination:** Determined by comparing the specified dew point with sample temperature and via an in-line Rotronics RH probe. Overall RH uncertainty is 1.5%.

**Measurement Sequence:**
1. Equilibrated at $\text{RH}=92\%$ in $\text{H}_2\text{O}$ vapor at 30°C.
2. Dried at 60°C under dry flowing Ar, then cooled to 30°C ($\text{RH}=0\%$).
3. Equilibrated in $\text{D}_2\text{O}$ at $\text{RH}=92\%$.

### 3.3 Neutron Reflectometry Data Acquisition
Samples are aligned using the following process:
1. **Transmission Mode:** The sample is centered in the beam (minimum transmitted intensity) and the angle is scanned to find the peak intensity (parallel to the beam).
2. **Reflection Mode:** Alignment is refined by setting the sample angle slightly below the critical angle of the Si substrate and positioning the detector at twice this angle.

Data is collected in a series of scans with limited Q range. Once equilibrium hydration is reached (no statistically significant changes in NR), scans are combined for better statistics. Background scans and slit scans are also performed.

### 3.4 Data Reduction and Fitting
Absolute specular reflectivity is determined by subtracting averaged background scans from specular scans and normalizing by the incident intensity. Data is fit using the **Refl1d** fitting software.

### 3.5 Data Analysis
If the sample is considered a mixture of "water" and "non-water" phases, the SLD is given by:

$$SLD_{fit,k}(z) = V_{Water}(z) \times SLD_{known,k} + [1 - V_{Water}(z)] \times SLD_{Non-Water}(z)$$

Where $k$ represents the isotope ($\text{H}_2\text{O}$ or $\text{D}_2\text{O}$).

**Water Volume Fraction Calculation:**
Assuming equal uptake for both isotopes:
$$V_{Water}(z) = \frac{SLD_{fit,H_2O}(z) - SLD_{fit,D_2O}(z)}{SLD_{known,H_2O} - SLD_{known,D_2O}}$$

**Non-Water Phase SLD Calculation:**
$$SLD_{non-water}(z) = \frac{SLD_{fit,H_2O}(z) + SLD_{fit,D_2O}(z)}{2 \times \frac{1}{V_{Water}(z)}} - \frac{SLD_{known,D_2O} - SLD_{known,H_2O}}{2 \times V_{Water}(z)(1 - V_{Water}(z))}$$

Alternatively, $SLD_{non-water}(z)$ can be calculated directly from measured and known quantities:
$$SLD_{non-water}(z) = \frac{SLD_{fit,H_2O}(z)}{SLD_{known,D_2O} - SLD_{fit,D_2O}(z)} \frac{SLD_{known,H_2O}}{[SLD_{known,D_2O} - SLD_{known,H_2O}] - [SLD_{fit,D_2O}(z) - SLD_{fit,H_2O}(z)]}$$

## References
1. Gierke, T.D., et al. (1981). J. Polym. Sci. Part B, 19(11): 1687-1704.
2. Rubatat, L., et al. (2004). Macromolecules, 37(20): 7772-7783.
3. Cui, S.T., et al. (2007). J. Phys. Chem. B, 111(9): 2208-2218.
4. Kim, M.H., et al. (2006). Macromolecules, 39(14): 4775-4787.
5. Kubo, W., et al. (2010). J. Phys. Chem. C, 114(5): 2370-2374.
6. Schmidt-Rohr, K. and Q. Chen (2008). Nat. Mater., 7(1): 75-83.
7. Dura, J.A., et al. (2009). Macromolecules, 42(13): 4769-4774.
8. Murthi, V.S., et al. (2008). ECS Transactions, 16: 1471-1485.
9. Kim, S., et al. (2013). Macromolecules, 46(14): 5630-5637.
10. DeCaluwe, S.C., et al. (2014). Soft Matter, 10, 5763.
11. DeCaluwe, S.C., et al. (2018). Nano Energy, 46, 91-100.
12. Dura, J., et al. (2006). Rev. Sci. Instr, 77, 074301.
13. Owejan, J.E., et al. (2012). Chem. Mater, 24, 11: 2133–2140.
14. Kienzle, P.A., et al. Refl1D: Interactive depth profile modeler. https://refl1d.readthedocs.io/en/stable/

## Contacts
[contact details omitted]

<!-- Source: MAGIK experiment | NIST. Removed site navigation, social media buttons, footer, and personal contact details. Converted LaTeX-style formulas to Markdown math. -->
