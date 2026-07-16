---
doc_id: candor_reflectometry_software
source_id: CANDOR-002
title: Reflectometry Software — Data Reduction and Analysis
instrument: CANDOR
workflow_stage: data_reduction
source_type: web_page
access_level: public
status: current
owner: NCNR reflectometry software team
last_reviewed: 2026-06-15
source_url_or_path: https://www.nist.gov/ncnr/neutron-instruments/data-reduction-analysis/reflectometry-software
source_last_updated: 2025-03-24
citation_required: false
---

# Reflectometry Software

This NIST NCNR page collects software and web tools for neutron and X-ray reflectometry data fitting, uncertainty analysis, raw-data reduction, scattering length density calculations, and quick reflectivity simulations. CANDOR users should use the Reductus-based reduction workflow described below as the standard path for reducing raw CANDOR reflectometry data to R vs. Q curves.

## Refl1D

Refl1D is used for fitting and uncertainty analysis of neutron and X-ray reflectivity data.

### Windows installation

Use the application installer from the most recent Refl1D release:

- Download the `...Windows-x86_64-installer.exe` file from the latest release at https://github.com/reflectometry/refl1d/releases
- If the browser flags the installer as unknown software, follow the prompts to keep it.
- Run the installer.
- Optional shortcuts may be added for:
  - Launching the Refl1D webview GUI from the Start Menu
  - Launching a Refl1D PowerShell session for installing additional libraries or using the command line
  - Launching the Refl1D webview GUI from the Desktop
- To upgrade, uninstall the old version from Windows “Add or remove programs,” then repeat the installation steps with the newer version.
- Multiple Refl1D versions can be run simultaneously without issue.

### macOS installation

Use the DMG bundle appropriate for the computer architecture:

- Download `...Darwin-arm64.dmg` for newer Apple Silicon / M-series Macs.
- Download `...Darwin-x86_64.dmg` for older Intel Macs.
- Open the `.dmg` file and drag the Refl1D app to the `/Applications` folder shortcut.
- Launch the Refl1D webview with `refl1d.app` in `/Applications/refl1d-<version>`.
- Launch a Refl1D shell with `refl1d_shell.app` to add additional Python packages, for example `pip install molgroups`.

### Python Package Index installation

Refl1D can also be installed from PyPI.

Requirements and commands:

```bash
pip install refl1d[webview]
```

- Install Python 3.9 or greater, such as from Python.org or Anaconda.
- Open a terminal window or Anaconda Prompt.
- Run the install command above.
- Running `refl1d` from the command line starts the command-line client.
- Running `refl1d --edit` starts an interactive fitting session.
- Running `pip install --upgrade refl1d` updates Refl1D to the latest version.

### Refl1D related resources

- Refl1D releases: https://github.com/reflectometry/refl1d/releases
- Refl1D manual: http://refl1d.readthedocs.org/
- Bumps fitting package: http://bumps.readthedocs.org/
- PeriodicTable package: http://periodictable.readthedocs.org/

### Suggested citation / acknowledgement

The page suggests acknowledging Refl1D by citing the NIST reflectometry software page. Example wording from the page:

> The Refl1D program was used for elements of the data analysis [1].

Reference:

[1] P.A. Kienzle, B.B. Maranville, K.V. O'Donovan, J.F. Ankner, N.F. Berk, C.F. Majkrzak; https://www.nist.gov/ncnr/reflectometry-software, 2017–

## Reductus

Reductus is a web application for reducing NCNR raw instrument data to reflectivity data.

Reductus is driven by the `reflred` Python libraries and supports common operations needed to convert raw X-ray and neutron reflectivity data into a reflectivity curve in physical units, `R` vs. `Q`. Supported operations include corrections such as background subtraction and scaling.

Key workflow notes:

- Data files are accessed directly by URL from the NCNR online data repository.
- Reduction templates, or recipes, can be modified with a graphical editor.
- Templates can be downloaded and reused or shared by email.
- Reduced data can be downloaded as columnar text files.
- No login or password is required.
- Reductus replaces the older Reflpak application.

Key links:

- Reductus application: https://reductus.nist.gov/
- `reflred` Python libraries: https://github.com/reflectometry/reduction
- NCNR online data repository: https://dx.doi.org/10.18434/T4201B
- Reflpak application: https://www.nist.gov/services-resources/software/reflpak

Suggested Reductus citation:

- Journal of Applied Crystallography, Volume 51, Part 5, pages 1500–1506: https://doi.org/10.1107/S1600576718011974

## PeriodicTable / SLD calculator

The online SLD and activation calculator uses the same PeriodicTable package as Refl1D and SasView to compute scattering length density and neutron activation.

Key link:

- Online SLD / activation calculator: https://www.ncnr.nist.gov/resources/activation/

## Web reflectivity calculators

The page links to browser-based reflectivity calculators for quick data exploration.

Available calculators:

- Magnetic reflectivity calculator: https://pages.nist.gov/reflectometry-calculators/magnetic-reflectivity-calculator.html
- Non-magnetic / unpolarized reflectivity calculator: https://pages.nist.gov/reflectometry-calculators/reflectivity-calculator.html

The calculators allow user-generated SLD profiles to be exported to a heavily commented Python Refl1D model file, providing a starting point for modeling data in Refl1D.

Related publication:

- Interactive web-based calculator for neutron and X-ray reflectivity: https://www.nist.gov/publications/interactive-web-based-calculator-neutron-and-x-ray-reflectivity

## Disclaimer / use conditions

The software was developed at NIST Center for Neutron Research by federal employees in the course of their official duties. The page states that, under 17 U.S.C. § 105, the software is not subject to copyright protection and is in the public domain.

NIST does not assume responsibility for use of the software and makes no guarantees, expressed or implied, about its quality, reliability, or other characteristics. Trade names or commercial products do not imply NIST endorsement or that the named product is necessarily the best product for the stated purpose. The page requests acknowledgement if the software is used.

## Acknowledgments

Portions of the work are based on activities supported by the National Science Foundation under Agreement No. DMR-0412074.

## References listed on the source page

- C.F. Majkrzak, K.V. O'Donovan, N.F. Berk (2006). “Polarized neutron reflectometry.” In *Neutron Scattering from Magnetic Materials*, T. Chatterji, editor. Elsevier.
- C.F. Majkrzak (1996). “Neutron scattering studies of magnetic thin films and multilayers.” *Physica B* 221, 342–356.
- J.F. Ankner, C.F. Majkrzak (1992). “Subsurface profile refinement for neutron specular reflectivity.” In *S.P.I.E. Conference Proceedings*, Vol. 1738. C.F. Majkrzak and J.L. Wood, editors. S.P.I.E., Bellingham, WA.

## Contacts

The source page lists contacts for Refl1D / NCNR reflectometry software. Refer to the live source page for current names, email addresses, and phone numbers.

<!-- Source: Reflectometry Software | NIST (https://www.nist.gov/ncnr/neutron-instruments/data-reduction-analysis/reflectometry-software). Created April 14, 2017; updated March 24, 2025. No deprecation banner -> status current. Navigation, U.S. government banner, NIST site header/footer, share widgets, scripts, styles, analytics, social links, topic tags, and direct personal contact details removed; software descriptions, installation guidance, citations, disclaimers, acknowledgments, references, and key software/resource links preserved. -->
