#!/usr/bin/env python3
"""
Import the latest Qualtrics export, clean survey_clean.csv to exactly 15
respondent rows, then rebuild analysis_summary.xlsx. Column letters for
formulas are derived from the current CSV header (no hard-coded AB/T/Z maps).
"""

from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT / "data" / "raw"
PROCESSED_DATA_DIR = ROOT / "data" / "processed"
ANALYSIS_DIR = ROOT / "analysis"
CSV_PATH = PROCESSED_DATA_DIR / "survey_clean.csv"
XLSX_PATH = ANALYSIS_DIR / "analysis_summary.xlsx"
DICTIONARY_PATH = PROCESSED_DATA_DIR / "survey_dictionary.csv"

KEY_I = "it_strategy_importance"
KEY_A = "contribute_achieving_competitive_advantage"

METRICS_FIELDS = [
    "it_strategy_importance",
    "contribute_achieving_competitive_advantage",
    "think_alignment_business_needs",
    "involved_setting_business_goals",
    "responsiveness_changing_business_needs",
    "effective_delivering_projects_timeliness",
]

EXPECTED_N = 15


def is_blank(val: str | None) -> bool:
    if val is None:
        return True
    return str(val).strip() == ""


def latest_qualtrics_zip() -> Path | None:
    zips = sorted(
        RAW_DATA_DIR.glob("ISYS*Strategic*Role*IT*Survey*.zip"),
        key=lambda p: p.stat().st_mtime,
    )
    return zips[-1] if zips else None


def normalize_label(value: str) -> str:
    value = str(value).replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", value).strip()


def parse_answer_mapping(mapping: str) -> dict[str, str]:
    if is_blank(mapping) or str(mapping).strip().lower() == "free text":
        return {}
    pairs: dict[str, str] = {}
    parts = re.split(r";\s*(?=\d+=)", str(mapping))
    for part in parts:
        if "=" not in part:
            continue
        code, label = part.split("=", 1)
        pairs[normalize_label(label)] = code.strip()
    return pairs


def load_dictionary() -> list[dict[str, str]]:
    with DICTIONARY_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def map_single_value(value: str, mapping: dict[str, str]) -> str:
    if is_blank(value):
        return ""
    value_s = str(value).strip()
    if value_s in mapping.values():
        return value_s
    return mapping.get(normalize_label(value_s), value_s)


def map_multi_value(value: str, mapping: dict[str, str]) -> str:
    if is_blank(value):
        return ""
    value_s = str(value).strip()
    if re.fullmatch(r"\d+(,\d+)*", value_s):
        return value_s

    norm = normalize_label(value_s)
    labels = sorted(mapping.keys(), key=len, reverse=True)
    codes: list[str] = []
    while norm:
        match = next((label for label in labels if norm.startswith(label)), None)
        if match is None:
            raise SystemExit(f"Could not map multi-select value: {value_s!r}")
        codes.append(mapping[match])
        norm = norm[len(match) :].lstrip()
        if norm.startswith(","):
            norm = norm[1:].lstrip()
    return ",".join(codes)


def import_latest_qualtrics_export() -> None:
    latest_zip = latest_qualtrics_zip()
    if latest_zip is None:
        return

    with zipfile.ZipFile(latest_zip) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise SystemExit(f"Expected one CSV in {latest_zip.name}, found {len(csv_names)}")
        with zf.open(csv_names[0]) as f:
            rows = list(csv.reader((line.decode("utf-8-sig") for line in f)))

    if len(rows) < 3:
        raise SystemExit(f"Qualtrics export {latest_zip.name} has no respondent rows")

    raw_header = rows[0]
    raw_idx = {name: i for i, name in enumerate(raw_header)}
    dictionary = load_dictionary()

    clean_header = [row["readable_name"] for row in dictionary]
    clean_rows: list[list[str]] = []
    for raw_row in rows[3:]:
        out: list[str] = []
        for field in dictionary:
            original = field["original_name"]
            if original not in raw_idx:
                raise SystemExit(f"Missing raw export column: {original!r}")
            raw_value = raw_row[raw_idx[original]] if raw_idx[original] < len(raw_row) else ""
            mapping = parse_answer_mapping(field["answer_mapping"])
            if field["field_type"] == "multi_select":
                out.append(map_multi_value(raw_value, mapping))
            elif mapping:
                out.append(map_single_value(raw_value, mapping))
            else:
                out.append("" if is_blank(raw_value) else str(raw_value).strip())
        clean_rows.append(out)

    header, body = clean_csv_rows([clean_header, *clean_rows])
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(body)


def row_all_blank(row: list[str]) -> bool:
    return all(is_blank(c) for c in row)


def keep_row(header: list[str], row: list[str]) -> bool:
    if row_all_blank(row):
        return False
    pad = row + [""] * max(0, len(header) - len(row))
    row = pad[: len(header)]
    idx_i = header.index(KEY_I)
    idx_a = header.index(KEY_A)
    if is_blank(row[idx_i]) or is_blank(row[idx_a]):
        return False
    return True


def clean_csv_rows(rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    if not rows:
        raise ValueError("Empty CSV")
    header = rows[0]
    body = [r for r in rows[1:] if keep_row(header, r)]
    return header, body


def header_col_letters(header: list[str]) -> dict[str, str]:
    """1-based Excel column index -> letter for each required field."""
    letters: dict[str, str] = {}
    for name in METRICS_FIELDS:
        if name not in header:
            raise SystemExit(f"Missing required column in CSV header: {name!r}")
        idx_1based = header.index(name) + 1
        letters[name] = get_column_letter(idx_1based)
    return letters


def segment_col_letter(header: list[str]) -> str:
    return get_column_letter(len(header) + 1)


def col_range(letter: str, data_start: int, data_end: int) -> str:
    # Quoted sheet name avoids reference parsing issues in some Excel builds.
    return f"'raw_data'!${letter}${data_start}:${letter}${data_end}"


def pad_row(header: list[str], row: list[str]) -> list[str]:
    return (row + [""] * max(0, len(header) - len(row)))[: len(header)]


def validate_numeric_body(header: list[str], body: list[list[str]]) -> None:
    """Ensure every data row has parsable floats in all metric columns."""
    idxs = [header.index(n) for n in METRICS_FIELDS]
    for ri, row in enumerate(body, start=2):
        pad = pad_row(header, row)
        for j in idxs:
            v = pad[j]
            if is_blank(v):
                raise SystemExit(f"Row {ri}: blank in required numeric column {header[j]!r}")
            try:
                float(str(v).strip())
            except ValueError:
                raise SystemExit(f"Row {ri}: non-numeric in {header[j]!r}: {v!r}")


def main() -> None:
    import_latest_qualtrics_export()

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    header, body = clean_csv_rows(rows)
    n = len(body)
    if n != EXPECTED_N:
        raise SystemExit(f"After cleaning, expected {EXPECTED_N} rows, got {n}.")

    validate_numeric_body(header, body)

    letters = header_col_letters(header)
    seg_letter = segment_col_letter(header)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(body)

    data_start = 2
    data_end = data_start + n - 1

    wb = Workbook()
    wb.remove(wb.active)

    let_i = letters[KEY_I]
    let_a = letters[KEY_A]

    # --- raw_data ---
    ws_raw = wb.create_sheet("raw_data", 0)
    ws_raw.append(header)
    metric_set = set(METRICS_FIELDS)
    for r_i, row in enumerate(body, start=data_start):
        pad = pad_row(header, row)
        for col_i, h in enumerate(header, start=1):
            v = pad[col_i - 1]
            cell = ws_raw.cell(row=r_i, column=col_i)
            if h in metric_set:
                cell.value = float(str(v).strip())
                cell.number_format = "0.########"
            else:
                cell.value = None if is_blank(v) else v

    seg_col_idx = len(header) + 1
    ws_raw.cell(row=1, column=seg_col_idx, value="segment_assignment")
    for excel_row in range(data_start, data_end + 1):
        c_i, c_a = f"${let_i}{excel_row}", f"${let_a}{excel_row}"
        fmla = (
            f'=IF(OR(ISBLANK({c_i}),ISBLANK({c_a})),"",'
            f'IF(AND({c_i}>=4,{c_a}>=4),"Strategic IT",'
            f'IF(AND({c_i}<=3,{c_a}<=3),"Support IT","Constrained IT")))'
        )
        ws_raw.cell(row=excel_row, column=seg_col_idx, value=fmla)

    # --- metrics ---
    ws_m = wb.create_sheet("metrics", 1)
    ws_m["A1"], ws_m["B1"], ws_m["C1"] = "variable", "mean", "notes"
    rng_note = f"raw_data rows {data_start}:{data_end}"
    for i, name in enumerate(METRICS_FIELDS, start=2):
        ws_m.cell(row=i, column=1, value=name)
        L = letters[name]
        ws_m.cell(row=i, column=2, value=f"=AVERAGE({col_range(L, data_start, data_end)})")
        ws_m.cell(row=i, column=3, value=rng_note)

    # --- gaps ---
    ws_g = wb.create_sheet("gaps", 2)
    ws_g["A1"], ws_g["B1"], ws_g["C1"] = "gap", "value", "formula (reference)"
    f_impact = (
        f"=AVERAGE({col_range(let_i, data_start, data_end)})"
        f"-AVERAGE({col_range(let_a, data_start, data_end)})"
    )
    lz = letters["think_alignment_business_needs"]
    lm = letters["responsiveness_changing_business_needs"]
    f_align = (
        f"=AVERAGE({col_range(lz, data_start, data_end)})"
        f"-AVERAGE({col_range(lm, data_start, data_end)})"
    )
    ws_g["A2"] = "strategy_impact (importance - competitive_advantage)"
    ws_g["B2"], ws_g["C2"] = f_impact, f_impact
    ws_g["A3"] = "alignment_responsiveness (alignment - responsiveness)"
    ws_g["B3"], ws_g["C3"] = f_align, f_align
    # Quick sanity checks if gaps show #DIV/0!: counts must match EXPECTED_N.
    ws_g["A5"] = "debug_count_it_strategy_importance"
    ws_g["B5"] = f"=COUNT({col_range(let_i, data_start, data_end)})"
    ws_g["A6"] = "debug_count_contribute_achieving_competitive_advantage"
    ws_g["B6"] = f"=COUNT({col_range(let_a, data_start, data_end)})"
    ws_g["A7"] = "debug_count_alignment"
    ws_g["B7"] = f"=COUNT({col_range(lz, data_start, data_end)})"
    ws_g["A8"] = "debug_count_responsiveness"
    ws_g["B8"] = f"=COUNT({col_range(lm, data_start, data_end)})"

    # --- segments ---
    ws_s = wb.create_sheet("segments", 3)
    ws_s["A1"], ws_s["B1"], ws_s["C1"] = "segment", "count", "formula (reference)"
    seg_range = f"'raw_data'!${seg_letter}${data_start}:${seg_letter}${data_end}"
    for i, label in enumerate(["Strategic IT", "Support IT", "Constrained IT"], start=2):
        fmla = f'=COUNTIF({seg_range},"{label}")'
        ws_s.cell(row=i, column=1, value=label)
        ws_s.cell(row=i, column=2, value=fmla)
        ws_s.cell(row=i, column=3, value=fmla)
    ws_s["A5"] = "total_assigned"
    ws_s["B5"] = "=SUM(B2:B4)"
    ws_s["C5"] = f"must equal {EXPECTED_N}"

    # --- traceability ---
    ws_t = wb.create_sheet("traceability", 4)
    lines = [
        "Traceability (ISYS 814 Team C)",
        "",
        "Source data:",
        f"  - {CSV_PATH.name} cleaned to {EXPECTED_N} rows; pasted to raw_data.",
        f"  - Formula column letters are derived from the CSV header (not hard-coded).",
        f"  - segment_assignment is column {seg_letter} (immediately after last CSV column).",
        "",
        f"Ranges: 'raw_data'!Col${data_start}:Col${data_end} only (quoted sheet name in formulas).",
        "Likert metric columns are written as numeric cells (not text) so AVERAGE/COUNT work.",
        f"gaps sheet rows 5-8: COUNT debug for each gap column (expect {EXPECTED_N} each).",
        "Segment rules: Strategic (I>=4,A>=4), Support (I<=3,A<=3), else Constrained; no Unclassified.",
    ]
    for r, line in enumerate(lines, start=1):
        ws_t.cell(row=r, column=1, value=line)

    wb.save(XLSX_PATH)

    # --- STEP 6: debug print ---
    print("Column mapping (0-based header index, 1-based Excel col, letter, sample row 1):")
    for name in METRICS_FIELDS:
        idx0 = header.index(name)
        excel_col = idx0 + 1
        let = letters[name]
        sample = body[0][idx0] if idx0 < len(body[0]) else ""
        print(f"  {name}: idx0={idx0} excel_col={excel_col} letter={let!r} sample={sample!r}")
    seg_excel_col = len(header) + 1
    print(
        f"  segment_assignment: excel_col={seg_excel_col} letter={seg_letter!r} (appended; not in CSV)"
    )
    print()
    print("strategy_impact formula:")
    print(f"  {f_impact}")
    print("alignment_responsiveness formula:")
    print(f"  {f_align}")
    print()
    print(f"Rows after cleaning: {n}; saved {XLSX_PATH}")


if __name__ == "__main__":
    main()
