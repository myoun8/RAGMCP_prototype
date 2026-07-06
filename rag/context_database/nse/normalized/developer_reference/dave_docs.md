---
doc_id: dave_docs
source_id: NSE-005
title: DAVE Documentation
instrument: NCNR / neutron scattering
workflow_stage: data_reduction_analysis_documentation
source_type: web_page
access_level: public
status: legacy
owner: NCNR DAVE development team
last_reviewed: 2026-06-15
source_url_or_path: https://www.ncnr.nist.gov/dave/documentation.html
source_last_updated: 2011-02-18
citation_required: true
---

# DAVE Documentation

DAVE is the NCNR Data Analysis and Visualization Environment for reduction, visualization, and analysis of low-energy neutron spectroscopic data. This page collects DAVE/IDL course notes, internal PDF manuals, PAN extension guidance, citation guidance, and public-domain/disclaimer information.

## DAVE site navigation

- [DAVE Home](https://www.ncnr.nist.gov/dave/index.html)
- [Features](https://www.ncnr.nist.gov/dave/features.html)
- [Changelogs](https://www.ncnr.nist.gov/dave/new_features.html)
- [Screenshots](https://www.ncnr.nist.gov/dave/screenshots.html)
- [Downloads](https://www.ncnr.nist.gov/dave/download.html)
- [Citations](https://www.ncnr.nist.gov/dave/dave_citations_alt.html)
- [DAVE/IDL documentation](https://www.ncnr.nist.gov/dave/documentation.html)

## Course notes

### Application Development in IDL I
- Instructor/date: Robert M. Dimeo, February 28-March 2, 2005
- [Application Development in IDL I](https://www.ncnr.nist.gov/dave/documentation/intro_to_idl1.pdf)
- [Application Development in IDL I Programs](https://www.ncnr.nist.gov/dave/documentation/intro_to_idl1_programs.zip)

### Application Development in IDL II
- Instructor/date: Robert M. Dimeo, February 3-5, 2003
- [Application Development in IDL II](https://www.ncnr.nist.gov/dave/documentation/intro_to_idl2.pdf)
- [Application Development in IDL II Programs](https://www.ncnr.nist.gov/dave/documentation/intro_to_idl2_programs.zip)

### DAVE 2 course notes
- Instructor/date: Richard Tumanjong Azuah, March 4-6, 2008
- [DAVE 2: Introduction to programing using the iTool framework](https://www.ncnr.nist.gov/dave/documentation/dave2_rev1.pdf)
- [simpleclasses.zip](https://www.ncnr.nist.gov/dave/documentation/simpleclasses.zip)
- [inheritedclasses.zip](https://www.ncnr.nist.gov/dave/documentation/inheritedclasses.zip)
- Remaining code referenced in the notes is part of the DAVE project.

## DAVE PDF internal documentation

- Diatomic Calculation: [diatomiccalc.pdf](https://www.ncnr.nist.gov/dave/documentation/diatomiccalc.pdf)
- HFBS Data Reduction user manual: [hfbsreduction.pdf](https://www.ncnr.nist.gov/dave/documentation/hfbsreduction.pdf)
- Methyl Calculations: [methylcalc.pdf](https://www.ncnr.nist.gov/dave/documentation/methylcalc.pdf)
- Peak Analysis (PAN) user manual: [pandoc.pdf](https://www.ncnr.nist.gov/dave/documentation/pandoc_DAVE.pdf)
- PAN user macros manual: [pan_user_macros.pdf](https://www.ncnr.nist.gov/dave/documentation/pan_user_macros.pdf)
- Spurion Calculator: [spurcalc.pdf](https://www.ncnr.nist.gov/dave/documentation/spurcalc.pdf)
- FCS data reduction user manual: [fcs_manual.pdf](https://www.ncnr.nist.gov/dave/documentation/fcs_manual.pdf)
- NSE data reduction user manual: [nse_manual.pdf](https://www.ncnr.nist.gov/dave/documentation/nse_reduction_manual.pdf)
- ASCII file reader user manual: [ascii_help.pdf](https://www.ncnr.nist.gov/dave/documentation/ascii_help.pdf)
- Mslice user manual: [dcs_mslice.pdf](https://www.ncnr.nist.gov/dave/documentation/dcs_mslice.pdf)
- Gaussian98 user manual: [gaussian1.pdf](https://www.ncnr.nist.gov/dave/documentation/gaussian1.pdf)
- RAINS user manual: [rains_models.pdf](https://www.ncnr.nist.gov/dave/documentation/rains_models.pdf)

## Templates and PAN extension guidance

- [Template and brief instructions](https://www.ncnr.nist.gov/dave/documentation/dave_template.html) for including a GUI into DAVE version 1.x.
- To include additional functions in PAN, define the function in IDL as described in [PAN_userfunction.pdf](https://www.ncnr.nist.gov/dave/documentation/PAN_userfunction.pdf) or use the [function template](http://www.ncnr.nist.gov/staff/dimeo/panweb/pan_functions.html) as a guide. IDL source code can be forwarded to the DAVE team for possible inclusion in a future build.
- Documentation for the stand-alone version of PAN, requiring an IDL license, is available on the [PAN documentation page](http://www.ncnr.nist.gov/staff/dimeo/panweb/pan.html). Much of it is also relevant to the DAVE version of PAN.

## Required citation / acknowledgement

If DAVE is used to reduce, analyze, or visualize data, the source page asks users to acknowledge its use by including this reference:

- [DAVE: A comprehensive software suite for the reduction, visualization, and analysis of low energy neutron spectroscopic data](https://dx.doi.org/10.6028/jres.114.025), R.T. Azuah, L.R. Kneller, Y. Qiu, P.L.W. Tregenna-Piggott, C.M. Brown, J.R.D. Copley, and R.M. Dimeo, *J. Res. Natl. Inst. Stan. Technol.* **114**, 341 (2009).

## Disclaimer

The DAVE software was developed at the National Institute of Standards and Technology at the NIST Center for Neutron Research by federal employees in the course of official duties. Under 17 U.S.C. § 105, the software is not subject to copyright protection and is in the public domain. DAVE is an experimental neutron scattering data reduction, visualization, and analysis system. NIST assumes no responsibility for its use and makes no express or implied guarantees about quality, reliability, or other characteristics. Mention of trade names or commercial products does not imply endorsement. Acknowledgment is appreciated when the software is used.

## Acknowledgments

- Work based on activities supported by the National Science Foundation under Agreement No. DMR-0944772, previously DMR-0454672 for 2005-2010.
- DAVE development team named on the source page: Richard Azuah, John Copley, Rob Dimeo, Sungil Park, Seung-Hun Lee, Alan Munter, Larry Kneller, Yiming Qiu, Inma Peral, Craig Brown, Paul Kienzle, and Philip Tregenna.
- Additional open-source utilities by David Fanning, Ronn Kling, Mark Piper, Michael D. Galloy, and Craig Markwardt were incorporated into some DAVE programs.

## Source status

- Source page last modified: 18-February-2011 by website owner NCNR, attention Richard Azuah.
- Page content is legacy-style HTML. Banners, legacy table layout, analytics scripts, styling, tracking, and Cloudflare code were removed; substantive documentation links, citation language, disclaimer, and acknowledgments were preserved.
