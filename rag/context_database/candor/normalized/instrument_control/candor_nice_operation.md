---
doc_id: nice_console
source_id: CANDOR-005
title: The NICE Console
instrument: COMMON
workflow_stage: instrument_control
source_type: reference
software: NICE
access_level: public
status: deprecated
owner: NCNR computing group
last_reviewed: 2026-06-12
source_url_or_path: https://www.nist.gov/ncnr/nice-help/nice-console
source_last_updated: 2026-05-27
deprecation_notice: true
related_source_ids: COMMON-001
citation_required: false
---

# The NICE Console

> DEPRECATION NOTICE: The source page carries the banner "This page is no longer being updated and the information may be out of date." Treat as deprecated/legacy and verify against current NICE documentation.
>

CANDOR, like other NCNR instruments, is operated through the NICE console; the console features described below apply to CANDOR operation even though this page itself is general NICE documentation rather than CANDOR-specific.

## The Console Panel

Most features of NICE can be accessed quickly via the console. To get to the console (or any other window), go to the *Window* menu (at the top of any NICE window) and choose *console*.

## Auto-complete

While typing commands you can press **Tab** to auto-complete. You can tab-complete all NICE commands and almost all command arguments. Use this feature.

## Help

You can obtain help for any/all commands via the menu **Help → Find/Help Commands and Devices**.

Open this window, type **notify**, and press Enter to auto-complete. You'll see documentation about the **notify** command, which allows you to send emails to yourself.

- **notify** takes 2 required positional arguments: an email and a message, in order.
  - Example: `notify <email> "experiment reached state x"`

Other commands take other types of arguments.

## Related NICE Help pages

- NICE Help (book home): https://www.nist.gov/ncnr/nice-help
- Common Commands (child; see COMMON-010): https://www.nist.gov/ncnr/nice-help/nice-console/common-commands
- Sequences: https://www.nist.gov/ncnr/nice-help/sequences
- Scripts: https://www.nist.gov/ncnr/nice-help/scripts

<!-- Source: The NICE Console | NIST (https://www.nist.gov/ncnr/nice-help/nice-console). Created February 6, 2019; updated May 27, 2026. Page carries an explicit deprecation banner -> status deprecated. Captured under a CANDOR-005 filename but content is general NICE/COMMON, not CANDOR-specific. Navigation, sharing widgets, and inline UI screenshots (1.png, auto-complete.png, help_1.png) removed during normalization. An example email address in the notify illustration was replaced with a placeholder <email>. -->