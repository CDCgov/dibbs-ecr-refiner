# Schematron Validation in DIBBs eCR Refiner

This directory contains the Schematron files and supporting XSLT assets required for validating XML documents (eICR and RR) used in this project.

## Overview

- **Schematron** (`.sch`): XML-based rule language for expressing validation rules.
- **XSLT** (`.xsl`): Schematron files are compiled to XSLT using the [SchXslt](https://schxslt.github.io/schxslt/) library.
- **Python (saxonche)**: We use [saxonche](https://pypi.org/project/saxonche/) (Python bindings for Saxon-HE) to run the transformation and validation, since XSLT 2.0+ is required and not supported by lxml.

## Why This Setup?

- **Python and XSLT:**
    - The standard Python XML libraries (`lxml`, `xml.etree`) support only XSLT 1.0, but modern Schematron compilation (and especially the `SchXslt` toolchain used here) requires XSLT 2.0+.
    - As a result, we use [Saxon-HE](https://www.saxonica.com/products/PD12/SaxonC-HE.pdf) via its Python bindings (`saxonche`). Saxon-HE is an open-source XSLT 2.0/3.0 processor.
- **Schematron Compilation:**
    - [SchXslt](https://schxslt.github.io/schxslt/) is a modern, open-source Schematron-to-XSLT compiler. It is used to convert `.sch` files into XSLT stylesheets suitable for Saxon-HE.
    - Note: There are no pure-Python Schematron processors that support XSLT 2.0+; hence this hybrid approach.
- **Why not lxml?**
    - `lxml` only supports XSLT 1.0, which is insufficient for Schematron features used in these profiles (e.g., abstract patterns, advanced XPath).

## Directory Structure

```
.
├── convert-sch-to-xslt.py       # Python script to compile .sch -> .xsl
├── eicr/
│   ├── CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.sch
│   ├── CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xsl
│   └── voc.xml
├── rr/
│   ├── CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.sch
│   ├── CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.xsl
│   └── CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml
└── schxslt/                     # SchXslt XSLT assets
    ├── compile/
    ├── compile-for-svrl.xsl
    ├── expand.xsl
    ├── include.xsl
    ├── pipeline-for-svrl.xsl
    ├── pipeline.xsl
    ├── svrl.xsl
    ├── util/
    └── version.xsl
```

## How to Compile Schematron `.sch` to XSLT `.xsl`

For **eICR** and **RR** Schematrons, we provide a Python script `convert-sch-to-xslt.py` that uses Saxon-HE (via `saxonche`) and the SchXslt `pipeline-for-svrl.xsl` to produce `.xsl` files for validation.

### Step-by-Step Instructions

1. **Install Requirements**

   - Install [saxonche](https://pypi.org/project/saxonche/):
     ```bash
     pip install saxonche
     ```
   - Ensure all SchXslt assets are present in the `schxslt/` directory (already included in this repo).

2. **Run the Compilation Script**

   From the directory containing `convert-sch-to-xslt.py`, run:
   ```bash
   python convert-sch-to-xslt.py
   ```

   This will:
   - Compile `eicr/CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.sch` to `eicr/CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xsl`
   - Compile `rr/CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.sch` to `rr/CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.xsl`

   The script uses `schxslt/pipeline-for-svrl.xsl` as the compilation stylesheet.

3. **Result**

   You should see `.xsl` files appear alongside their source `.sch` files in the `eicr/` and `rr/` subdirectories.

## How Validation Works (Python Workflow)

1. **Preparation**: Ensure Saxon-HE and SchXslt assets are available.
2. **Compilation**: Compile any new or updated `.sch` files as above.
3. **Validation**:
    - Use the compiled `.xsl` with Saxon-HE (via Python) to validate XML documents.
    - The validation produces an [SVRL](https://schematron.com/document/3427.html) (Schematron Validation Report Language) output file that details all assertions and results.
4. **Result Handling**: Parse and interpret the SVRL for pass/fail and diagnostics.

## SVRL Output

The XSLT files produced are intended for use in validation runs that output an [SVRL (Schematron Validation Report Language)](https://schematron.com/document/3427.html) report, which captures the assertions and results from the Schematron rules.

## References

- [SchXslt Documentation](https://schxslt.github.io/schxslt/)
- [saxonche (Saxon-HE Python)](https://pypi.org/project/saxonche/)
- [SVRL Format](https://schematron.com/document/3427.html)
- [HL7 eICR Implementation Guide 1.1](https://github.com/HL7/CDA-phcaserpt-1.1.1)
- [HL7 eICR Implementation Guide 3.1](https://github.com/HL7/CDA-phcaserpt-1.3.0)
- [HL7 RR Implementation Guide 1.1](https://github.com/HL7/CDA-phcr-rr-1.1.0)

> [!NOTE]
> For all of the HL7 GitHub repos the `.sch` files were pulled from these three repos above in the repos' `validation/` directory.

## FAQ

**Q: Why not use lxml for everything?**
A: lxml only supports XSLT 1.0, but modern Schematron (and SchXslt) requires XSLT 2.0/3.0. Saxon-HE fills this gap.

**Q: Can I recompile the .sch files?**
A: Yes, use the provided `convert-sch-to-xslt.py` script.

**Q: Is this approach comparable to HL7/AIMS validation?**
A: Yes, the goal is for SVRL output to be 1:1 comparable to AIMS reference results.

## Contributing

If you update or add new Schematron profiles, please document their source and intended use in this README. If you update the validation workflow, update this documentation accordingly.
