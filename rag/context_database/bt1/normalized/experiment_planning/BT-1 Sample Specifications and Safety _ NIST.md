---
doc_id: bt-1_sample_specifications_and_safety
source_id: BT1-002
title: BT-1 Sample Specifications and Safety
instrument: BT1
workflow_stage: experiment_planning
source_type: web_page
access_level: public
status: current
owner: BT-1 instrument scientists
last_reviewed: 2026-08-16
source_url_or_path: https://www.nist.gov/ncnr/bt-1-sample-specifications-and-safety
source_last_updated: 2026-05-28
citation_required: false
---

# BT-1 Sample Specifications and Safety

The ideal specimen for use at BT-1 is a powder, contains <1% hydrogen (by atom), does not contain any elements with high absorption cross sections for neutrons, and is available in sufficient quantity to fill a 5-10 ml container. For a sample meeting this description, a dataset may be collected in 2-4 hours. Actual samples often differ from this ideal.

## Sample Considerations

Users should be aware of sample activation. A calculator for estimating attenuation and activation is available via the NCNR resources.

The ideal sample size for BT-1 is $10\text{ cm}^3$ (typically 5-15 g) of material, although significantly less is often sufficient.

### Vanadium Cells for BT-1
Vanadium sample cans are used and can be sealed using various thicknesses of either Indium or Lead wire.

| Size | I.D. (mm) | Length (mm) | Volume (c.c.) |
| :--- | :--- | :--- | :--- |
| A | 6.0 | 50.0 | 1.5 |
| B | 9.2 | 50.0 | 4.0 |
| C | 10.8 | 50.0 | 5.5 |
| D | 12.4 | 50.0 | 8.0 |
| E | 15.6 | 50.0 | 11.5 |

### Crystallite Considerations
Samples must have a sufficient number of crystallites (grains) so that the powder diffraction approximation is valid. For accurate measurements, crystallites must be randomly oriented. While the sample can be oscillated or spun to improve particle statistics and randomization, this is rarely needed. 

*   **Pellets:** Samples pressed into pellets can typically be used without grinding.
*   **Preferred Orientation:** Cast ingots or machined parts may exhibit significant preferred orientation. (BT-8 can be used for texture measurements).
*   **Small Crystallites:** Samples with crystallites $<1\text{ micron}$ exhibit significant diffraction peak broadening and may not benefit from high-resolution measurements.

### Container Considerations
Samples are typically sealed into vanadium containers; aluminum and steel are used for specific measurements. 

*   **Cryogenic Loading:** If the sample is cooled below 77 K, loading is typically performed in a He glove bag or glove box.
*   **Sealing:** Indium gaskets are standard, though other materials are used for high-temperature measurements.
*   **Irregular Samples:** Small ($<100\text{ ml}$) irregular ceramic samples can be used without modification.
*   **Geometry Constraints:** Due to the wide angular range of the detector bank, the diffractometer cannot be used in reflection mode for flat-plate samples or transmission mode with large thin samples.

### Sample Quantity
NIST provides vanadium containers with volumes of 1.5, 3.4, 5, 6, and 10 ml. The 10 ml volume is effectively the largest possible. Samples smaller than 1 ml can be accommodated, though signal-to-noise decreases as sample size decreases. Long data collection times for small samples must be justified based on scientific value and sample scarcity.

## Hydrogen
Hydrogen (unlike deuterium) increases background scattering and decreases instrumental sensitivity. 
*   **Recommendation:** Use deuterium-exchanged materials if hydrogen is present in amounts greater than a few percent of the total atoms.
*   **Hygroscopic Materials:** Keep dry or exchange water with deuterated water.
*   **Analysis:** Prompt-Gamma Neutron Activation Analysis (PGNAA), available at the NCNR, can quantify hydrogen levels.

## Neutron Activation
Most elements become radioactive via neutron capture when placed in a beam. While activation is often minimal or decays within hours/days, certain elements are more prone to significant activity.

**Elements with high tendency for significant activity:**
Li, Sc, Ga, As, Y, Sb, La, Pr, and most elements with atomic number $\ge \text{Sm (62)}$.

**Elements with lower levels of activation:**
Na, P, Cl, K, Co, Se, Br, Rb, Mo, Ru, Pd, Ag, Cd, In, Sn, Cs, Ce, and Nd.

### Safety and Removal
All samples irradiated at NIST must be cleared by Health Physics staff before removal from the NCNR. NRC regulations may restrict storage or shipping. If a sample is classified as radioactive and the receiving institution is not licensed, NIST may need to store it until activity decreases or, in rare cases, dispose of it.

## Elements to Avoid
Certain elements cause difficulties with neutron diffraction. Contact BT-1 instrument scientists if your sample contains:

*   **H:** Incoherent scattering raises backgrounds (use D where possible).
*   **B:** Highly absorbing (use $^{11}\text{B}$).
*   **V:** Extremely small scattering length; usually invisible to neutrons (combine with x-ray refinements).

### Extensive Safety Review Required
An extensive safety review is required if any of the following are present:

| Element/Material | Reason |
| :--- | :--- |
| **Cd, Sm, Eu, Ir** | Highly absorbing, gamma emitter |
| **Gd** | Extremely highly absorbing, severe gamma emitter, activates |
| **Radioactive Isotopes** | Requires prior review and approval per NRC license |
| **Transuranics** | Radioactivity hazard, may be highly absorbing and gamma emitting |

**Note:** Using isotopically purified materials (e.g., $^{11}\text{B}$, $^{112}\text{Cd}$, or $^{114}\text{Cd}$) can often avoid these absorption and activation problems.

For further information, contact the BT-1 instrument scientists at [contact details omitted].

<!-- Source: BT-1 Sample Specifications and Safety (https://www.nist.gov/ncnr/bt-1-sample-specifications-and-safety). Removed NIST site navigation, header/footer chrome, and "Was this page helpful?" widget. -->
