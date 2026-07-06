---
doc_id: nse_dave_reduction
source_id: NSE-002
title: NSE Data Reduction in DAVE
instrument: NSE
workflow_stage: data_reduction
source_type: pdf_handout
access_level: public_or_uploaded
status: historical
owner: NCNR / DAVE NSE reduction workflow
last_reviewed: 2026-06-15
source_url_or_path: nse_dave_reduction.pdf
source_last_updated: 2005-09-26
citation_required: false
---

# NSE Data Reduction in DAVE

## Purpose

This handout describes how to reduce data from the NG-5 Neutron Spin Echo (NSE) instrument at the NIST Center for Neutron Research using the NSE reduction tools in DAVE, the Data Analysis and Visualization Environment.

The goal of an NSE experiment is to determine the normalized intermediate scattering function, `I(Q,t)`, the time-correlation function of scattering-length-density fluctuations at wave vector `Q`.

During the experiment, the directly measured quantity is not `I(Q,t)` itself, but the polarization of the scattered neutron beam as a function of phase current, at different Fourier times, for each pixel of the 2D detector.

## Detector and raw measurement model

The detector is a 32 x 32 pixel 2D detector, with nominal pixel size of 1 cm^2.

At each detector position and Fourier time, neutron counts `N` are recorded as a function of phase current `phi_c`. Each echo is fit to a Gaussian-damped cosine:

```text
N = N0 + A exp[-(phi_c - phi0)^2 / (2 sigma^2)] cos[(360/T)(phi_c - phi0)]
```

where:

- `A` is the echo amplitude and contains the information needed for `I(Q,t)`.
- `N0` is the average count level.
- `phi0` is the echo point.
- `T` is the cosine period.
- `sigma` is the width of the Gaussian envelope.

`T` and `sigma` are determined by the incoming beam characteristics, primarily mean wavelength and wavelength spread. `phi0` depends on the field path experienced by the neutrons.

## Polarization and correction equations

The non-spin-flip and spin-flip counts are measured at the end of each echo scan with the pi/2 flippers off and the pi flipper off/on. These are labeled `Nup` and `Ndown`.

The measured sample polarization at the echo point is:

```text
<Pz>_S = 2A / (Nup - Ndown)
```

Magnetic-field inhomogeneity can reduce polarization. Its effect is divided out using a purely elastic scatterer, giving the resolution polarization:

```text
<Pz>_E = 2 A_E / (Nup_E - Ndown_E)
```

`<Pz>_E` as a function of Fourier time is effectively the instrumental resolution.

A background measurement is also required so that dynamic scattering from the sample holder, solvent, or other non-sample contributions does not contaminate the final result. The background should be measured under conditions identical to the sample.

The final normalized `I(Q,t)` combines sample, background/cell, transmission, solvent volume fraction, and resolution corrections.

## Reduction overview

The reduction procedure has four main stages:

1. Fit every echo at each Fourier time and detector pixel.
2. Determine scattered-beam polarization from the fitted echo amplitudes.
3. Correct for resolution and background effects.
4. Group detector zones into a finite number of `Q` arcs to obtain `I(Q,t)` curves.

The first step is the most critical because fitting an oscillatory function can become trapped in local minima. A common failure mode is a fitted echo point offset by plus or minus 360 degrees, corresponding to one period of the cosine. The user must inspect the fits and ensure that the echo phase varies smoothly across the detector and as a function of Fourier time.

The phase map should be nearly identical for any sample measured under the same instrument conditions, because it is an instrumental quantity rather than a sample-scattering quantity. The usual workflow is to determine phase values from the reference/resolution sample and import them into sample and background fits.

## DAVE NSE reduction interface

Open DAVE and select **Reduce NSE Data** from the Data Reduction menu/tree.

The NSE Data Reduction window contains:

- Menu bar
- Tab menu interface: **DATA FILES**, **GENERAL**, **DATA SET**, **FITTING**
- Detector image
- Help text line
- Fourier-time selector / CD-type menu
- Main plot window

The detector image and plot window initially show dummy data, then update after `.echo` files are loaded.

## Loading data files

Use **File > Open .echo file(s)**.

The software displays loaded files under the **DATA FILES** tab, grouped by stated exchanged wave vector `Q`.

### Echo file contents

Raw NSE data are stored in ASCII files named like:

```text
mxxxx.echo
```

where `xxxx` is an automatically incremented 4-digit run number. A typical file is about 1.4 MB.

Each `.echo` file includes:

- Description of the performed scan
- For each Fourier time: coil-current settings and corresponding physical parameters such as Fourier time and `Q`
- For each phase point: phase current, counters, multimeter readings, and detector-pixel neutron counts

### Echo file location

The source handout states that echo files reside on the Linux echo computer in:

```text
/var/nse
```

and are mirrored to the central server **Charlotte** in the `NSE Data/Current` folder.

Because this document is historical, verify current file locations with the instrument team before relying on these paths.

## Selecting file type

Right-click a file in the **DATA FILES** tree and select **Select data set type**.

Available object types:

- `untyped`
- `resolution`
- `sample`
- `cell`

Icon center color indicates file type:

- Red: resolution
- Green: sample
- Blue: cell
- Black: no type

Icon edge color indicates reduction status:

- Red edge: not reduced
- Green edge: reduced

## Selecting detector binning

Use the **DATA SET** tab to group detector pixels and improve signal-to-noise ratio. Common binning choices are:

- `2 x 2`
- `4 x 4`

The NSE instrument has a relatively broad incoming wavelength spread and therefore limited `Q` resolution. However, the echo point varies across the detector. Choose the binning factor by balancing signal-to-noise, `Q` resolution, and the expected `Q` dependence of the sample dynamics.

Important: sample and reference/resolution objects must use the same binning factor if phases will be imported from the reference into the sample/background fits.

## DATA SET and GENERAL parameters

In **DATA SET**, enter:

- Sample transmission
- Volume fraction

These values are not used until final `I(Q,t)` calculation, and the program asks for them again before the final calculation.

In **GENERAL**, enter:

- Beam center X/Y position
- Number of `Q` arcs

The number of `Q` arcs determines how many `I(Q,t)` curves will be produced. Fewer arcs improve statistics but reduce angular/`Q` discrimination.

## Masking low-quality pixels

After data are loaded, the detector image can show the integrated counts per echo scan at each pixel.

Visual conventions described in the handout:

- Dark green: detector area physically masked by NSE supports
- Blue thick lines: borders between `Q` arcs
- Cyan rectangle: currently selected pixel
- Light green: user-masked pixels

Controls:

- Move through pixels with arrow keys when the mouse is in the detector image.
- Left-click a detector pixel to select it.
- Step through Fourier times with the CD menu or `Page Up` / `Page Down`.
- Press `m` to mask or unmask the selected pixel.
- Press `Enter`, or right-click except when showing phase, to open the detector-image popup menu.

Popup menu options include applying the current mask or selected-pixel mask to all Fourier times or only subsequent Fourier times.

## Masking low-quality phase points

Bad phase-current points may appear because of changes in the surrounding magnetic field or detector-count reset problems.

To mask or unmask a phase point:

- Inspect the main plot window showing intensity versus phase.
- Left-click the bad phase point in the plot.
- The program masks the point whose phase current is closest to the cursor.

Masking a phase point applies to each detector pixel at that Fourier time. Masked phase points are displayed in cyan, and their error bars are removed.

## Phase current as phase angle

The echo scan physically varies the current through the phase coil. Because phase current is proportional to neutron-spin precession angle, DAVE expresses it as phase angle.

A linear relationship exists between phase-current values and phase-angle values. The zero-angle phase point is only approximately predetermined and is chosen so that the true echo point for all detector pixels falls within the investigated window.

`Nup` and `Ndown` are collected at zero phase current, but DAVE displays them at high phase-angle values for visual clarity.

## Reducing a resolution object

Select a resolution file under **DATA FILES**, right-click, and choose:

```text
Fit Operations > Fit Echoes (Resolution)
```

This fits all echoes in the resolution file for all Fourier times and pixels. When complete, the file icon gets a green edge and the detector image/plot windows show fitting results.

The fit can also be started from the **FITTING** tab by clicking **Fit**.

### Recommended FITTING tab defaults for resolution files

For resolution files, the handout recommends:

- `Av`: vary
- `A`: vary
- `PH`: vary
- `T`: vary
- `W`: fix

`W`, the Gaussian-envelope width, was previously determined by the instrument scientist. It should normally remain fixed, unless a complete Gaussian envelope with many phase-current points was measured.

Available fitting methods:

- `arc` (default)
- `spiral`
- `expand`

## Inspecting fit results

After fitting, the detector image can display fitting parameters and quality metrics:

- `Av`
- `Ph`
- `T`
- `W`
- signal / beam polarization from Equation 2
- chi-squared of the fit

Use **Image Options** or the detector-image popup menu to change the displayed quantity. The main plot window shows the measured echo points and the fitted curve as a thick red line.

### Error-bar image

Use **Image Options > Display Image Error bars** or right-click the detector image to open a color-coded image of the absolute fitting error for the currently displayed parameter.

If the detector image is showing raw counts, the error is the square root of the counts.

Special attention should be paid to the fitted echo phase. It should vary smoothly across the detector and as a function of Fourier time.

Recommended inspection setup:

- Detector image: **Phase**
- Main plot: **Fit Phase v. Fourier Time**
- Optional: toggle auxiliary plot to view echo and phase-vs-time simultaneously

The auxiliary plot is display-only; it cannot be used to mask phase points or refit data.

## Refitting pixels

If one or more fits are unsatisfactory, DAVE provides several refit methods.

### Refit from the FITTING tab

Use **Fit Pixel** to refit the currently highlighted detector pixel using the parameter values shown in the **FITTING** tab.

You can edit starting values manually, press `Enter`, and preview the resulting fitting function in the plot window.

### Refit from the detector-image phase map

When the detector image displays **Phase**, sliders appear for selecting starting phase and period values.

Right-click a detector pixel to refit using the slider-selected phase and period as starting parameters.

### Refit from Fit Phase vs Fourier Time

In the **Fit Phase v. Fourier Time** plot, phase values should form a smooth curve. For discontinuities:

1. Place the mouse at the Fourier time to refit.
2. Set the vertical cursor position to the expected phase value on a smooth curve.
3. Left-click to refit.

The pixel is refit using the clicked phase value as the starting phase. The starting period is either `T = 360` or the click-refit slider value.

### Refit with Smooth T

The **smooth t** button refits all pixels at the current Fourier time. The routine starts from the center of the detector and moves outward, keeping phases within 180 degrees of neighboring values.

This is similar to the `expand` fitting method. A bad fit near the center can propagate outward and affect more distant pixels.

### Refit with +/-360 buttons

If all phases at a Fourier time appear offset by one period, use:

```text
+360 refit
-360 refit
```

to shift all phases by a period and redo the fits.

Inspect each Fourier time carefully. Good reference-sample fits are essential for correct sample reduction.

If a pixel has poor statistics, it may be better to mask it than to accept a meaningless fit. The handout notes that low reference signal, for example below about 20 near detector edges or high Fourier times, can produce large error bars in the corresponding sample `I(Q,t)` point.

## Reducing sample or cell objects

After completing the resolution-file fit, select a sample or cell object with the same `Q` value.

Before fitting:

- Inspect for low-count pixels.
- Inspect for phase-point glitches.
- Mask poor pixels or phase points as needed.

Then select:

```text
Fit Operations > Import Phases (Sample, Cell)
```

or click **IMPORT PHASES** in the **FITTING** tab.

The resolution object must have the same binning as the sample/cell object.

During import, choose the file whose phases and periods should be imported and decide whether to fix or vary those parameters. Because phase and period are instrumental, the recommended choice is generally to fix both.

### Constant phase-offset option

The **fit phase offset (constant phase)** option lets the program account for a constant phase offset in the data.

When selected, DAVE:

1. Keeps phase free for a 4 x 4 pixel area in the detector center at each Fourier time.
2. Compares those fitted phases with the reference scan.
3. Adds the resulting offset to reference echo phases.
4. Applies this offset as fixed for all other pixels.

The offset is constant across the detector surface but varies with Fourier time.

The handout does not recommend this option for cell objects because their counting statistics may be poor.

## Calculating I(Q,t)

After sample, resolution, and cell/background objects have been fit, enter the beam center values in **GENERAL**.

To calculate `I(Q,t)`:

1. Select the sample object.
2. Right-click and choose **Calculate I(Q,t)**, or use **Calculations > Calculate I(Q,t)** from the menu bar.
3. Select the sample, resolution, and cell/background objects.
4. Enter the number of `Q` arcs.
5. Enter sample transmission, sample volume fraction, and cell transmission.
6. Click **OK**.

Example interpretation: if the sample is 96% solvent, the sample volume fraction entered for the non-solvent component is `0.04`.

## I(Q,t) display window

The result opens in an `I(Q,t)` display window for preliminary inspection.

Capabilities include:

- Resize window
- Zoom by dragging the right mouse button over the plot
- Zoom by entering min/max values
- Unzoom by right-clicking the plot
- Move legend using arrow keys and `Page Up`, `Page Down`, `Home`, `End`
- Step through individual `I(Q,t)` curves with **Step through curves**
- Preliminary exponential or stretched-exponential fits

## Export formats

The `I(Q,t)` display window supports several export formats:

1. **DAVE binary**
   - Can be loaded by other DAVE programs for visualization and analysis, especially PAN.

2. **ASCII Files**
   - One file per `I(Q,t)` curve.
   - Filename pattern:
     ```text
     IQT_q.qqqq.dat
     ```
   - Four columns: `Q`, Fourier time, `I(Q,t)`, error bar.
   - This is the format used by the IGOR NSE reduction program.

3. **Single ASCII file**
   - Two header lines indicating arc `Q` values.
   - `nQ + 1` fixed-width, space-separated columns, where `nQ` is the number of `Q` arcs.
   - Column sequence: Fourier time, `I(Q1,t)`, error bar, `I(Q2,t)`, error bar, etc.
   - Fit results are saved separately with an `_info` extension.

4. **Separate 3-column ASCII files**
   - One file per `I(Q,t)` function.
   - Filename pattern:
     ```text
     IQT_q.qqqq.txt
     ```
   - Eight description lines and four fixed-width, space-separated columns: `Q`, Fourier time, `I(Q,t)`, error bar.

## Saving and restoring sessions

At any time, use:

```text
File > Save session
```

This creates a binary `.sav` file. It can be loaded with:

```text
File > Restore session
```

Restoring a session overwrites the current session.

You can also save only the selected object through the **File** menu or **DATA FILES** popup menu. Restoring an object adds it to the current session. If a saved session is restored as an object, only the first file is loaded and added.

## Additional operations

### Remove a Fourier time

To remove unwanted Fourier-time data:

1. Right-click the object.
2. Choose **Remove Fourier times**.
3. Select the Fourier time in the popup window.
4. Click **Remove T**.

A new object is created with the selected Fourier time removed.

### Merge objects

To merge runs of the same sample measured at different Fourier times:

1. Right-click the object.
2. Choose **Merge**.
3. Select the run/object to merge from the dropdown.
4. Confirm.

A new object is created containing Fourier-time data from both runs.

### AutomaskSomething

The **AutomaskSomething** feature can automatically mask unsatisfactory pixels using selected criteria.

Possible criteria include:

- Minimum total scattering intensity
- Minimum average intensity fit parameter
- Minimum signal, for resolution data only
- Maximum error bar associated with a fitted parameter

Workflow:

1. Select **AutomaskSomething** from the menu bar.
2. Choose the quantity to filter on.
3. Choose greater-than or less-than filtering.
4. Enter the threshold.
5. Apply mask.

The available quantities include total echo counts, fitting variables, and corresponding error bars.

## Key quality-control rules

- Confirm that resolution fits are good before reducing samples.
- Check that fitted phases vary smoothly across the detector and with Fourier time.
- Treat +/-360 degree phase jumps as suspicious and refit where needed.
- Mask low-statistics pixels rather than accepting meaningless fits.
- Use identical binning for resolution, sample, and cell objects when importing phases.
- Verify beam center and `Q` arc definitions before calculating final `I(Q,t)` curves.
- Use background/cell and resolution corrections for final normalized results.

## Figure and visual notes

- Page 3 shows an example spin echo with `Nup` and `Ndown` points at the end of the scan; regular measurements collect only points near the echo minimum.
- Page 5 shows detector `Q` arcs and masked regions. The detector is divided into seven arcs, with 2 x 2 super-pixel binning shown in the grid.
- Page 6 labels the DAVE NSE Data Reduction interface: menu bar, tabs, detector image, help line, Fourier-time selector, and plot window.
- Pages 9-10 show examples of masking low-count pixels and bad phase points.
- Pages 13-14 show several refit workflows, including phase-map refit, Fit Phase vs Fourier Time refit, and Smooth T refit.
- Page 17 shows the `I(Q,t)` display window used for preliminary inspection and export.
- Pages 19-20 show removing Fourier times, merging runs, and the AutomaskSomething filtering interface.

## Source-cleaning note

This Markdown file was generated from the uploaded PDF handout `nse_dave_reduction.pdf`. The PDF text, equations, GUI workflow, figure meanings, reduction sequence, export formats, and troubleshooting guidance were preserved. Direct live-location assumptions and legacy server paths were kept only where they are part of the source, with a historical-use caution. Visual figure content was summarized rather than reproduced.
