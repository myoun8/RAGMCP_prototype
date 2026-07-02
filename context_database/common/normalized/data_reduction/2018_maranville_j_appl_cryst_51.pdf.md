---
doc_id: 2018_maranville_j_appl_cryst_51
source_id: COMMON-014
title: 'reductus: a stateless Python data reduction service with a browser front end'
instrument: COMMON
workflow_stage: data_reduction
source_type: paper
access_level: public
status: current
owner: [contact details omitted]
last_reviewed: 2026-07-02
source_url_or_path: 2018_maranville_j_appl_cryst_51.pdf.pdf
citation_required: true
software: Reductus
---

# reductus: a stateless Python data reduction service with a browser front end

The online data reduction service **reductus** transforms measurements in experimental science from laboratory coordinates into physically meaningful quantities with accurate estimation of uncertainties from instrumental settings and properties. 

The system is designed as a stateless Python back end with a JavaScript browser front end, utilizing a visual data flow diagram to allow users to construct arbitrary pipelines from known data transforms. It is specifically implemented for the three neutron reflectometry instruments at the NIST Center for Neutron Research (NCNR), though it is designed to be extensible for other techniques such as off-specular reflectometry, small-angle neutron scattering (SANS), and triple-axis spectrometry.

## 1. Motivation
In scientific user facilities, visiting researchers often require flexible data reduction capabilities without the overhead of installing specialized software on various platforms. A web-based application provides:
* **Universal Accessibility:** Accessible via any standards-compliant browser.
* **Centralized Maintenance:** Updates to calculation code are applied instantly to all users.
* **Local Installation Option:** Users can run the service locally to process private data or develop new reduction applications.

### 1.1 Data Reduction for Reflectometry
Neutron reflectometry characterizes surfaces, thin films, and multilayers by analyzing the intensity of a reflected signal relative to the incident beam (reflectivity).

**Standard Reduction Process (Monochromatic Beam, No Polarization):**
1. **Specular Reflection:** Record the number of neutrons reflected at various incident angles.
2. **Direct Beam Measurement:** Measure incident intensity with the same collimation (slits) but without the sample.
3. **Background Measurement:** Measure spurious detection events by offsetting the detector from the specular position (e.g., $bg+$ and $bg-$).
4. **Calculation:**
   $$\text{Reflectivity} = \frac{\text{Reflected Intensity} - \text{Background Intensity}}{\text{Direct Beam Intensity}}$$
5. **Coordinate Conversion:** Convert incident angles and wavelengths to reciprocal space $Q_z$.
6. **Uncertainty:** Error bars are generated based on Poisson distribution; angular and energy resolutions are calculated from collimation and optics.

## 2. Web Interface
The user interface is a JavaScript application comprising four key components:
* **Data source file browser:** For selecting input files.
* **Plotting panel:** For visualizing intermediate and final results.
* **Parameters panel:** For configuring individual computation modules.
* **Interactive data flow diagram:** A visual representation of the reduction chain.

### 2.1 Data Flow Diagram
Users navigate the reduction chain by interacting with the diagram. Clicking a module opens its parameters, and clicking output terminals displays the calculated results in the plotting panel. The client sends a JSON representation of the diagram to the server via HTTP POST.

### 2.2 Parameters Panel
The panel is rendered based on the instrument definition. It supports various input types:
* **Simple types:** `int`, `float`, `bool`.
* **Index type:** Allows clicking data points on a plot to add them to a list.
* **Scale type:** Enables dragging a data set on the plot to set a scaling factor.

### 2.3 Persistence and Sharing
The server is stateless. State is managed via:
* **In-browser stashing:** Results are stored in local persistent memory.
* **Filesystem save/load:** Users can download/upload the data flow diagram as a JSON file.
* **Data Export:** Reduced data is exported as a tab-delimited text file with the data flow diagram included in the header as a comment, ensuring **data provenance**.

## 3. Computational Framework

### 3.1 Data Types and Operations
Data sets flowing between modules have associated types; matching types are required for connection. The Python back end utilizes:
* **NumPy and SciPy:** For numerical processing.
* **Uncertainties library:** For propagation of uncertainties.
* **Custom utilities:** For unit conversion, rebinning, interpolation, and weighted least-squares solving.

### 3.2 Bundles of Inputs
To handle multiple files efficiently, `reductus` uses "bundles":
* **Single input:** The module operates on each input file independently.
* **Multiple input:** All inputs are passed as a single list (e.g., for joining multiple data sets).

### 3.3 Module Definition
Modules are defined by their action function and associated documentation (written in reStructuredText). Documentation is converted to HTML via Sphinx and equations are rendered using MathJax.

## 4. Back End Architecture

### 4.1 System Components
The architecture consists of:
1. **Web Server:** Serves static resources (HTML/JS/CSS) and acts as a proxy to the calculation engines via WSGI.
2. **Computation Engine:** Handles requests as Remote Procedure Calls (RPC).
3. **Data Store:** An HTTP-accessible repository (e.g., NCNR data store at `https://dx.doi.org/10.18434/T4201B`).
4. **Cache:** A Redis key-value store used for results and source files.

### 4.2 Computation Process
* **DAG Execution:** The data flow diagram is treated as a Directed Acyclic Graph (DAG). Nodes are computed in topological order.
* **Caching Strategy:** Every calculation step is identified by a unique hash of its input values and the code version. If any input or the code changes, the hash changes, triggering a recalculation of that node and all subsequent dependent nodes.
* **Reproducibility:** The Git commit hash of the server source is stored with the template to allow exact reproduction of results using a specific software version.

### 4.3 Server Configurations
| Configuration | Description | Use Case |
| :--- | :--- | :--- |
| **Single-computer** | Web server, engine, and cache on one machine (Flask). | Private data, local file access, custom modules. |
| **Container-based** | Docker/Docker Compose with three coordinated containers. | Development and testing. |
| **Scalable Production** | Apache/nginx $\rightarrow$ uWSGI $\rightarrow$ Pool of Python engines $\rightarrow$ Shared Redis. | Public-facing facility services. |

## 5. Conclusions
The `reductus` system provides a flexible, stateless approach to data reduction. By making the data flow graph visible, it allows experts to build complex pipelines while allowing novice users to perform routine reductions. It has successfully replaced legacy reduction software for NCNR's neutron reflectometry instruments.

<!-- Source: reductus: a stateless Python data reduction service with a browser front end (J. Appl. Cryst. 2018). Removed author email, repetitive page headers/footers, and publication metadata. -->
