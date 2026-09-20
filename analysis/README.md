# Analysis

This folder contains the public, aggregate analysis layer for the ISYS 814 final project.

The raw Qualtrics export, cleaned row-level response file, and workbook with the row-level `raw_data` sheet are intentionally local-only. They are ignored by Git because the survey included optional contact information and respondent-level context.

## Public Files

- `analysis_results.txt` - narrative summary of aggregate findings.
- `aggregate_metrics.csv` - public aggregate metrics used in the deck and README.
- `segment_counts.csv` - public segment counts and percentages.
- `analysis_methodology.md` - analysis logic, segmentation rules, and privacy boundary.
- `build_analysis_workbook.py` - rebuilds the private local workbook from the local Qualtrics export.
- `generate_public_summary.py` - regenerates the public aggregate CSV/TXT files from the ignored local cleaned CSV.

## Private Local Inputs

These files are used locally but are not tracked:

- `data/raw/`
- `data/processed/survey_clean.csv`
- `analysis/analysis_summary.xlsx`

## Rebuild

From the project root:

```bash
python3 analysis/build_analysis_workbook.py
python3 analysis/generate_public_summary.py
```

