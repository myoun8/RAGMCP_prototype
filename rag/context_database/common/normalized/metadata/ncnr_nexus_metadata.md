---
doc_id: ncnr_nexus_metadata
source_id: COMMON-004
title: NeXus Physical File Format (Mapping NeXus into HDF5)
instrument: COMMON
workflow_stage: data_access
source_type: reference
access_level: public
status: current
owner: NIAC (NeXus International Advisory Committee)
last_reviewed: 2026-06-12
source_url_or_path: https://manual.nexusformat.org/fileformat.html
source_version: nexus v2026.01
external_source: true
related_source_ids: COMMON-003
citation_required: false
---

# NeXus Physical File Format

This section describes how NeXus structures are mapped to features of the underlying physical file format. It is a guide for people who wish to create NeXus files without using the NeXus API.

> Note: This is a section of the external NeXus User Manual maintained by NIAC, not an NCNR document. NCNR's NICE instruments write NeXus HDF5 (and NeXus-ZIP) files, so this reference describes the structure of the data files users receive.

## Choice of HDF as Underlying File Format

At its beginnings, the founders of NeXus identified the Hierarchical Data Format (HDF) as a capable and efficient multi-platform data storage format. HDF was designed for large data sets and already had a substantial user community. It was developed and maintained initially by the National Center for Supercomputing Applications (NCSA) at the University of Illinois at Urbana-Champaign, and later spun off into its own group, The HDF Group (https://www.hdfgroup.org/). Rather than developing its own unique physical file format, the NeXus group chose to build NeXus on top of HDF.

HDF (now HDF5) is provided with software to read and write data (the application-programmer interface, or API) on a large number of computing systems in common use for neutron and X-ray science. HDF is a binary data file format that supports compression and structured data.

## Mapping NeXus into HDF

NeXus data structures map directly to HDF structures:

- NeXus *groups* are HDF5 *groups*.
- NeXus *fields* (data sets) are HDF5 *datasets*.
- Attributes map directly to HDF group or dataset attributes.
- The NeXus class is stored as an attribute on the HDF5 group, named `NX_class`, with a value equal to the NeXus class name.
- A NeXus `link` maps directly to the HDF hard-link mechanism.

(For legacy NeXus data files using HDF4, groups are HDF4 *vgroups* and fields are HDF4 *SDS* (scientific data sets). HDF4 does not support group attributes; it supports a group class set with `Vsetclass()` and read with `VGetclass()`.)

## Inspecting NeXus structure with h5dump

The `h5dump` command-line utility (provided with the HDF5 support libraries) is a convenient way to view how NeXus is implemented in HDF5.

NAPI calls that create the basic components:

- group: `NXmakegroup(fileID, "entry", "NXentry");`
- field: `NXmakedata(fileID, "two_theta", NX_FLOAT32, 1, &n); NXopendata(fileID, "two_theta"); NXputdata(fileID, tth);`
- attribute: `NXputattr(fileID, "units", "degrees", 7, NX_CHAR);`
- link: `NXmakelink(fileid, &itemid);` or `NXmakenamedlink(fileid, "linked_name", &itemid);`

### h5dump of a NeXus NXentry group

```text
GROUP "entry" {
  ATTRIBUTE "NX_class" {
     DATATYPE  H5T_STRING {
           STRSIZE 7;
           STRPAD H5T_STR_NULLPAD;
           CSET H5T_CSET_ASCII;
           CTYPE H5T_C_S1;
        }
     DATASPACE  SCALAR
     DATA {
     (0): "NXentry"
     }
  }
  # ... group contents
}
```

### h5dump of a NeXus field (HDF5 dataset)

```text
DATASET "two_theta" {
   DATATYPE  H5T_IEEE_F64LE
   DATASPACE  SIMPLE { ( 31 ) / ( 31 ) }
   DATA {
   (0): 17.9261, 17.9259, ...
   }
   ATTRIBUTE "units" {
      DATATYPE  H5T_STRING { STRSIZE 7; ... }
      DATASPACE  SCALAR
      DATA { (0): "degrees" }
   }
   # ... other attributes
}
```

### h5dump of a NeXus attribute

```text
ATTRIBUTE "axes" {
   DATATYPE  H5T_STRING { STRSIZE 9; ... }
   DATASPACE  SCALAR
   DATA { (0): "two_theta" }
}
```

### h5dump of a NeXus link

A NeXus link has two parts in HDF5 files. The dataset is created in some group, and a `target` attribute is added to indicate the HDF5 path to the dataset:

```text
ATTRIBUTE "target" {
   DATATYPE  H5T_STRING { STRSIZE 21; ... }
   DATASPACE  SCALAR
   DATA { (0): "/entry/data/two_theta" }
}
```

Then a hard link is created that refers to the original dataset:

```text
DATASET "two_theta" {
   HARDLINK "/entry/data/two_theta"
}
```

## Related references

- Examples of writing and reading NeXus data files: https://manual.nexusformat.org/examples/index.html
- Rules for storing data items in NeXus files (prev section): https://manual.nexusformat.org/datarules.html
- Constructing NeXus files and application definitions (next section): https://manual.nexusformat.org/applying-nexus.html

<!-- Source: NeXus User Manual v2026.01, section 1.2.3.3 "Physical File format" (https://manual.nexusformat.org/fileformat.html). © 1996-2026 NIAC. External (non-NCNR) reference. Sphinx nav/sidebar removed during normalization; code listings preserved. -->