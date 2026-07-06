---
doc_id: nice_faq
source_id: COMMON-008
title: NICE FAQ
instrument: COMMON
workflow_stage: troubleshooting
source_type: faq
software: NICE
access_level: public
status: current
owner: NCNR computing group
last_reviewed: 2026-06-12
source_url_or_path: https://www.nist.gov/ncnr/nice-help/faq
source_last_updated: 2023-06-09
citation_required: false
---

# NICE FAQ

Notation: commands typed at the console are shown in **bold** following the `>>>` prompt. Bracket pairs `<` and `>` signify the type of input needed. Three dots `...` mean multiple inputs are possible. Pressing **[Tab]** lists available commands, devices, and nodes; typing part of a command, device, or node narrows the list.

## What are the most basic commands I need to know?

- **read** — Reads the value(s) of the device(s) provided. Performed immediately and posted to the console.
  - `>>> read <device name> ...`
  - Example: `>>> read sampleAngleMotor`
- **move** — Changes the value(s) of the device(s) provided. The move command is queued.
  - `>>> move <device name> <value> ...`
  - Example: `>>> move sampleAngleMotor 10`
- **ct** — Performs an individual count and writes the result to the console. The ct command is queued.
  - `>>> ct <keyword argument> ...`
  - Example: `>>> ct -t 10`

## What is the difference between display and read?

- **display**ing a node shows node values based on the last state read from hardware.
- **read**ing a node queries hardware directly for the latest value. If a node's value is based on other nodes' values, those other nodes are also read, recursively.

## Where can I find help about using a command or device?

In the menu, under **Help → Find/Help Commands and Devices**. Type part or all of the name of the device or command into the help window.

## What is the difference between soft, hard, and raw positions?

- **rawPosition** is the raw value as read from the hardware.
- **hardPosition** is the position in a convenient unit: hardPosition = rawPosition × conversion factor.
- **softPosition** is further adjusted by a zero offset and to orient in a convenient direction: softPosition = parity × (hardPosition − zero).

## How can I set a motor's position?

- **setMotorPosition** conveniently redefines a motor's softPosition by adjusting the zero.
  - `>>> setMotorPosition <motor name> <softPosition value>`
  - Example: `>>> setMotorPosition sampleAngleMotor 10`

## How can I set a motor's position without moving it?

Moving the **resetRawPosition** node for a motor changes the hardware readout of the motor itself (rawPosition).

- `>>> move <motor name>.resetRawPosition <rawPosition value>`
- Example: `>>> move sampleAngleMotor.resetRawPosition 10`

## How do I restore lost motor positions (e.g., after a power outage)?

Use the **restoreMotorPositions** command.

## What does sleep do?

Use `>>> sleep <# of seconds>` to make the system wait a specified duration.

## How do I change limits?

- For motors, the `softUpperLimit` and `softLowerLimit` nodes define the limits.
- For devices such as temperature controllers, the `upperLimit` and `lowerLimit` nodes define the limits.
- For controllers with multiple control channels, each channel has separate limits (`upperLimit_1`, `lowerLimit_1`).
- `>>> move <motor name>.<limitNode> <positional value>`
- Examples: `>>> move sampleAngleMotor.softLowerLimit 10` ; `>>> move temp.upperLimit_1 150`

## How do I change units?

- `>>> setNodeProperties <device name>.<node name> --units <unit type>`
- Example: `>>> setNodeProperties sampleAngleMotor.softPosition --units rad`

Note: after units are changed, the latest units are not reflected in all GUI panels until the client is restarted. The command line and Device Panel always respect the latest unit. The dimension of a node CANNOT be changed (e.g., a node in degrees cannot be changed to cm).

## How do I lock (fix) a motor or other device? What is a lock?

- A lock prevents a node from being moved directly or indirectly via a move command, trajectory, sequence, etc.
- Everyone can lock/unlock any node: `>>> setNodeProperties <node> --userLocked true`
- Only admins can admin-lock/admin-unlock a node: `>>> setNodeProperties <node> --adminLocked true`
- See: Locking Nodes (https://www.nist.gov/ncnr/nice-help/nodes/locking-nodes).

## How do I know if the system is busy (motors moving, counting, etc.)?

Check the top-right status bar of any window. Go to *Window > Device Control* for a real-time display of exactly which devices are busy.

## How do I add/remove sample environment equipment?

Go to *Window > Configure Devices* to add and remove available device configurations.

## How do I stop ONLY the current command running in the queue?

Right-click the desired command in the queue and select *Cancel*.

## How do I find my files? How do I copy them from a previous experiment into the current experiment?

1. Go to *Experiment > View Experiment Manifest…* to see all files organized by experiment (a search bar allows filtering).
2. Selecting an experiment shows subfolders, including sequences and trajectories. Right-click and choose *Copy* on the files of interest.
3. The current experiment is always at the top of the list. You can also open a separate file browser via *Open Experiment Folder*.
4. Select the destination folder (do not open it; right-click on it) and select *Paste files into /...*

## What is the difference between a script, a sequence, and a trajectory?

- **Sequence** — a text file of NICE commands executed in order. No loops or if/then statements, but nesting other sequences is possible and any NICE command can be called. Easiest to build by selecting part of the queue, *Copy*, then *Paste* into a text file. A syntax-highlighting editor is built into NICE. See Sequences (https://www.nist.gov/ncnr/nice-help/sequences).
- **Trajectory** — the recipe for a "scan," where data points are recorded to a data file. Supports loops over a range (start, step, stop) or a list of positions; loops can be nested (e.g., scanning a range of Q-values for a list of temperatures). See the Trajectory Guide (https://www.nist.gov/ncnr/nice-help/trajectory-guide).
- **Script** — an embedded Python program, allowing decisions based on measurement results. More difficult than the other two and reserved for special cases (e.g., align a sample while cooling, then proceed once a setpoint temperature is reached). See Scripts (https://www.nist.gov/ncnr/nice-help/scripts).

## How does temperature control in NICE work (hold time vs. timeout vs. tolerance band)?

See Temperature Controllers under Sample Environment Equipment (https://www.nist.gov/ncnr/sample-environment/equipment).

## What are the features of the counter (event vs. non-event mode, handshaking on/off)?

See Counters in the NICE Help (https://www.nist.gov/ncnr/nice-help/devices/counter).

## How/where/when to save configs, maps, trays, and sequence files? Common file naming schemes?

See File Output under Sequences and File Output under the Trajectory Guide. For files used by VSANS, see File Output under VSANS.

<!-- Source: FAQ | NIST (https://www.nist.gov/ncnr/nice-help/faq). Created December 4, 2018; updated June 9, 2023. No deprecation banner present -> status current. Navigation, sharing widgets, and inline screenshots (busy.png, cancel.png) removed during normalization; command syntax and Q&A content preserved. -->