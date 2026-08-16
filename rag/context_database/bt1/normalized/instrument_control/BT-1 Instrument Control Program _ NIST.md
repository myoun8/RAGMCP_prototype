---
doc_id: bt-1-instrument-control-program
source_id: BT1-001
title: BT-1 Instrument Control Program
instrument: BT1
workflow_stage: instrument_control
source_type: web_page
access_level: public
status: current
owner: NCNR BT-1 Team
last_reviewed: 2026-08-16
source_url_or_path: https://www.nist.gov/ncnr/bt-1-instrument-control-program
source_last_updated: 2023-05-01
citation_required: false
software: none
---

# BT-1 Instrument Control Program

**WARNING: DO NOT ENTER THE DETECTOR AREA WHEN THE BEAM IS ON**

## Rules for using BT-1

### Information Board and Log Book
*   **Whiteboard:** You MUST write the sample composition, your name(s), and telephone number(s) on the white board.
*   **Log Book:** Fill out all information requested in the BT-1 log book and on a BT-1 sample tag.
*   **Sample Tracking:** Add samples to the Sample Tracking App and print a barcode. Contact an instrument scientist if unable to do so.

### Shutter and Collimation Operation
*   **Collimation:** Press the desired collimation usa-button and wait while the drum rotates to the desired point. **Do not enter the sample area during this process.**
*   **Closing Beam:** Press the green 'close' usa-button to close the beam.
*   **Shutter Key:** Always remove and take the shutter key when working in the beam path.

### Monochromator and Positioning
*   **Settings:** Only trained persons may change the monochromator settings.
*   **Beam Dimensions:** The beam is 5/8" wide and focused to a 2" height at the sample position.
*   **Positioning Check:** To check sample positioning using the neutron-sensitive camera, consult an instrument scientist.

### Scanning Parameters
*   **Recommended Settings:** 
    *   Default scan range: 3-13 degrees 2theta (1.3-11.3 for Ge311).
    *   Step size: 0.05.
    *   *Note: These settings ensure each data point is counted in two different detectors.*
*   **Sample Checking:** For quick quality checks, run a scan with 60' collimation, range 5-10 degrees, 0.1 degree steps, and a 10 sec count.

### Sample Changer and Unloading
*   **Automatic Sample Changer:** Do not attempt to mount the 6-position automatic sample changer without instruction/approval from qualified personnel. Use the ICP command `next` to advance to the next sample position.
*   **Unloading:** 
    *   Survey the sample before removing it from the instrument area.
    *   Store all V sample cans in the BT-1 cabinet when not in use.
    *   Log samples to be removed via the NCNR Samples Tracking App or contact a user with access.
    *   **Never open cans in C100.**
    *   **Radiation Safety:** Health Physics must clear irradiated powder samples before removal from cans. Consult your instrument contact regarding Hot lab access.

## Sample Handling Procedures

### Prior to Experiments
*   **Activation Evaluation:** Users are strongly recommended to evaluate potential activation using the provided tool or by contacting Health Physics.
*   **Containers:** See a BT-1 scientist or [contact details omitted] for vanadium sample containers.
*   **Identification:** Fill out a BT-1 Sample Tag when loading the container. Attach the tag to the sample or the exterior of the sample environment (cryostat, furnace, etc.).
*   **Tracking:** Add samples to the NCNR Sample Tracking App and record the location throughout the stay at NCNR.

### During Experiments
*   **Logging:** All samples must be recorded in the log book along with the instrument monitor (`mrat`) reading. Proprietary measurements may use an approximate empirical chemical formula.
*   **Communication:** Update the whiteboard with the experiment details, emergency contact name/phone, and the names/institutions of all experimenters. Hang BT-1 sample tags on the whiteboard or equipment.

### After Experiments
*   **Survey:** A survey must be performed before the sample is removed from the instrument.
*   **Clearance:** All irradiated powder samples must be checked by Health Physics before removal from containers.
*   **Special Precautions:** If non-ambient conditions or special precautions are needed for unloading, use a **pink sample tag** or other obvious indicator.
*   **Shipping:** The local contact assists with unloading, Health Physics clearance, and shipping. If leaving samples at NIST, the user must complete a BT-1 Sample Shipping Form and provide a Material Safety Data Sheet (MSDS) or certify the sample is non-hazardous.
*   **Storage:** Store sample containers in the unlocked cabinet adjacent to BT-1. Special storage needs must be discussed with a scientist and noted in the Sample Tracking App.

## Controlling the Instrument

### Invoking the Program
The instrument control program `IICPP` is invoked from the command line by typing `icp`. 

*   **Hardware Control:** Hardware commands can only be executed from the **first session** of ICP.
*   **Monitoring:** Additional sessions may be opened to check sequences or timing.
*   **Preparation:** Buffers (I-buffers for scanning motor angles) and sequences can be edited using the `prepare` command from the ICP running directory.

### Execution Workflow
1.  **Temperature/Magnet:** Set `tdev` or `hdev` to the required controller following on-screen instructions.
2.  **Monochromator:** Verify monochromator settings; save monitor rate if needed (`mrat/s -20`).
3.  **Buffers:** Use `prepare` to edit buffers and sequences. Sequences can also be loaded from a file (one command per line).

#### Common Control Commands
| Command | Action |
| :--- | :--- |
| `prs` | Print the run sequence |
| `howlong/rs` | Estimate sequence duration based on saved monitor rate |
| `howlong i2-5` | Estimate duration for buffers 2 through 5 |
| `howlong/f [filename]` | Estimate duration for a specific sequence file |
| `ri#` | Run i-buffer number # |
| `rs` | Run sequence |
| `rsf [filename]` | Run sequence defined in filename |
| `ctrl-z` | Pause collection (after prefactor counts); press again to resume |
| `ctrl-c` | **Emergency Abort** |

#### Additional Utility Commands
*   `st=#` : Set temperature to value #
*   `sm=#` : Set magnetic field to #
*   `pt` : Print temperature
*   `phf` : Print field
*   `PRIVATE` : Toggle writing data file information to the MANIFEST for backup (used for proprietary data)

## Notes on using PREPARE

Use the simplest mode possible to avoid known strange behaviors.

### Parameter Definitions
*   **Comments:** The first 5 characters are the file name (with an iterative ### number).
*   **A3:** Sample table (usually does not require setting).
*   **A4:** Detector bank start (`beg`), step (`inc`), and end in 2-theta, across `NPTS` number of points.
*   **T0:** Target data collection temperature. Usually Kelvin, except for the high-temperature furnace (Celsius). Ignored if 0, if 'T-' flag is set, or if no controller is assigned.
*   **Inc-T:** Temperature increment added at each data point (usually 0.0 at BT-1).
*   **WAIT:** Maximum delay (minutes) if temperature is outside `T0 +/- ERR`. Run resumes once within range.
*   **ERR:** Maximum allowable temperature error before introducing a delay.
*   **Hld0:** Delay (minutes) used before starting the scan after the set-point temperature is reached (for equilibration).
*   **Hld:** Delay before each point (should always be 0).
*   **Field:** Menu for setting magnetic field conditions.
*   **Monit / Prefac / M-Typ:** 
    *   `M-Typ = Time`: `Monit` is in seconds. Total time = `Monit * Prefac`.
    *   `M-Typ = Neut`: `Monit` is a number of monitor counts. Total counts = `Monit * Prefac`.
    *   If `Prefac >= 4`, measurements are checked for statistical consistency.
*   **AUTOMON:** Menu to estimate `Monit` value based on desired finish time or total run period.

**Important:** Always select `UPDATE` before switching buffers to save changes.

### Buffer Operations (`BufOps`)
*   `COPY n1[-n2],m`: Copies buffers from n1 to n2 into buffer m, m+1, etc. (e.g., `copy 1,2` copies buffer 1 to 2).

## Hardware Setup Notes

### Temperature Devices (`tdev`)
1.  Input the temperature device plugged into the computer (e.g., 25-pin 'temp' cable to Lakeshore).
2.  Most Lakeshore controllers are option '10'.
3.  Choose sample and control channels.
4.  Verify communications and read temperature using `pt`.
5.  **Check that the heater is enabled** on the Lakeshore controller.

### 7-T Magnet (`hdev`)
*   **Configuration:** 
    *   Option: "Superconducting Magnet with no persistence switch"
    *   Controller: "Oxford controller"
    *   Value: 0.0778 A/G
    *   Limit: 90 A

<!-- Source: BT-1 Instrument Control Program (https://www.nist.gov/ncnr/bt-1-instrument-control-program). Removed navigation menus, NIST website headers/footers, and redundant metadata. -->
