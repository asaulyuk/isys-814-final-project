# ISYS 814 Final Project: Strategic Role of IT

This repository contains Team C's ISYS 814 final project on how organizations convert IT capability into strategic and competitive advantage. The public repo focuses on the aggregate analysis, supporting code, benchmark research, charts, and final presentation materials.

## Project Summary

The central research question is:

> If organizations continue investing in IT, why does that investment not always become competitive advantage?

The analysis uses a 15-response exploratory survey dataset and classifies organizations into three IT-strategy segments:

- Strategic IT: high IT strategy importance and high competitive impact
- Constrained IT: IT is seen as important but does not produce matching competitive impact
- Support IT: lower strategic importance and lower competitive impact

## Key Findings

- IT strategy importance mean: **3.53 / 5**
- IT competitive impact mean: **2.67 / 4**
- IT-business alignment mean: **3.80 / 5**
- IT strategy involvement mean: **2.60 / 4**
- Strategy-impact gap: **+0.87**
- Segment counts: **1 Strategic IT**, **8 Constrained IT**, **6 Support IT**

Overall, the project argues that IT capability becomes strategic advantage only when it is connected to governance, business involvement, execution discipline, and clear value realization.

## Repository Layout

```text
analysis/              Analysis code, aggregate tables, methodology, and public summary
assets/                Chart images and PowerPoint theme assets
benchmark research/    Supporting benchmark research notes
data/processed/        Public codebook and data dictionary
presentations/         Final deck and presentation outline
scripts/               Deck/theme helper scripts
```

Raw Qualtrics exports, cleaned row-level survey responses, analysis workbooks with row-level data, detailed written reports, and respondent interview notes are intentionally excluded from Git because they may contain respondent-level or identifying context.

## Important Files

- `analysis/analysis_results.txt` - public aggregate analysis summary
- `analysis/aggregate_metrics.csv` - aggregate metric table
- `analysis/segment_counts.csv` - aggregate segment table
- `analysis/build_analysis_workbook.py` - rebuilds the local analysis workbook when private raw exports are present
- `analysis/generate_public_summary.py` - regenerates public aggregate tables from the local private cleaned CSV
- `presentations/ISYS814_FinalProject_TeamC_v1.pptx` - final presentation deck
- `data/processed/codebook.csv` - question-to-field mapping
- `data/processed/survey_dictionary.csv` - field definitions and answer coding

## Rebuilding The Analysis

From the project root:

```bash
python3 analysis/build_analysis_workbook.py
```

The script looks for a local Qualtrics export under `data/raw/`, cleans the survey rows, writes `data/processed/survey_clean.csv`, and rebuilds `analysis/analysis_summary.xlsx`. Those generated row-level files are local-only and intentionally ignored by Git.

To regenerate the public aggregate tables after rebuilding the local workbook:

```bash
python3 analysis/generate_public_summary.py
```

## Data Privacy Note

This GitHub version keeps the project materials presentation-ready while avoiding publication of respondent-level data. Public materials include aggregate findings, charts, codebook/dictionary files, scripts, and presentation artifacts. Raw survey exports, cleaned respondent rows, detailed written reports, and interview notes are kept local only.
