#!/usr/bin/env python3
"""
Generate public aggregate analysis files from the local cleaned survey CSV.

The input CSV is intentionally ignored by Git because it contains row-level
survey responses. This script only writes aggregate outputs that are suitable
for the public repository.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = ROOT / "data" / "processed" / "survey_clean.csv"
ANALYSIS_DIR = ROOT / "analysis"

METRICS = [
    ("IT strategy importance", "it_strategy_importance", 5),
    ("IT competitive impact", "contribute_achieving_competitive_advantage", 4),
    ("IT-business alignment", "think_alignment_business_needs", 5),
    ("IT strategy involvement", "involved_setting_business_goals", 4),
    ("IT responsiveness", "responsiveness_changing_business_needs", 5),
    ("IT delivery effectiveness", "effective_delivering_projects_timeliness", 5),
]


def load_rows() -> list[dict[str, str]]:
    if not INPUT_CSV.exists():
        raise SystemExit(f"Missing local input: {INPUT_CSV}")
    with INPUT_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def numeric_values(rows: list[dict[str, str]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = (row.get(field) or "").strip()
        if raw:
            values.append(float(raw))
    return values


def segment(row: dict[str, str]) -> str:
    importance = float(row["it_strategy_importance"])
    impact = float(row["contribute_achieving_competitive_advantage"])
    if importance >= 4 and impact >= 4:
        return "Strategic IT"
    if importance <= 3 and impact <= 3:
        return "Support IT"
    return "Constrained IT"


def write_metrics(rows: list[dict[str, str]]) -> dict[str, float]:
    means: dict[str, float] = {}
    raw_means: dict[str, float] = {}
    output = ANALYSIS_DIR / "aggregate_metrics.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value", "scale", "n", "notes"])
        for label, field, scale in METRICS:
            values = numeric_values(rows, field)
            raw_value = mean(values)
            value = round(raw_value, 2)
            raw_means[label] = raw_value
            means[label] = value
            writer.writerow([label, f"{value:.2f}", scale, len(values), "Mean survey rating"])

        strategy_gap = round(
            raw_means["IT strategy importance"] - raw_means["IT competitive impact"], 2
        )
        alignment_gap = round(
            raw_means["IT-business alignment"] - raw_means["IT responsiveness"], 2
        )
        writer.writerow(
            [
                "Strategy-impact gap",
                f"{strategy_gap:.2f}",
                "",
                len(rows),
                "IT strategy importance minus IT competitive impact",
            ]
        )
        writer.writerow(
            [
                "Alignment-responsiveness gap",
                f"{alignment_gap:.2f}",
                "",
                len(rows),
                "IT-business alignment minus IT responsiveness",
            ]
        )
    means["Strategy-impact gap"] = strategy_gap
    means["Alignment-responsiveness gap"] = alignment_gap
    return means


def write_segments(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = {"Strategic IT": 0, "Constrained IT": 0, "Support IT": 0}
    for row in rows:
        counts[segment(row)] += 1

    rules = {
        "Strategic IT": "High IT strategy importance and high competitive impact",
        "Constrained IT": "Strategic importance does not consistently translate into competitive impact",
        "Support IT": "Lower IT strategy importance and lower competitive impact",
    }
    output = ANALYSIS_DIR / "segment_counts.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["segment", "count", "percentage", "rule"])
        for label in ["Strategic IT", "Constrained IT", "Support IT"]:
            percentage = round(counts[label] / len(rows) * 100)
            writer.writerow([label, counts[label], percentage, rules[label]])
    return counts


def write_summary(rows: list[dict[str, str]], means: dict[str, float], counts: dict[str, int]) -> None:
    output = ANALYSIS_DIR / "analysis_results.txt"
    output.write_text(
        "\n".join(
            [
                "ISYS 814 TEAM C - PUBLIC ANALYSIS SUMMARY",
                "==================================================",
                "",
                "This file contains aggregate results only. Row-level survey responses,",
                "raw Qualtrics exports, and the local analysis workbook are intentionally",
                "excluded from the public repository.",
                "",
                f"Sample size: {len(rows)} valid survey responses",
                "",
                "CORE METRICS",
                "--------------------------------------------------",
                f"- IT strategy importance: {means['IT strategy importance']:.2f} / 5",
                f"- IT competitive impact: {means['IT competitive impact']:.2f} / 4",
                f"- IT-business alignment: {means['IT-business alignment']:.2f} / 5",
                f"- IT strategy involvement: {means['IT strategy involvement']:.2f} / 4",
                f"- IT responsiveness: {means['IT responsiveness']:.2f} / 5",
                f"- IT delivery effectiveness: {means['IT delivery effectiveness']:.2f} / 5",
                "",
                "GAP METRICS",
                "--------------------------------------------------",
                f"- Strategy-impact gap: +{means['Strategy-impact gap']:.2f}",
                f"- Alignment-responsiveness gap: +{means['Alignment-responsiveness gap']:.2f}",
                "",
                "SEGMENTATION",
                "--------------------------------------------------",
                "Rules:",
                "- Strategic IT: high IT strategy importance and high competitive impact",
                "- Support IT: lower IT strategy importance and lower competitive impact",
                "- Constrained IT: all other valid cases",
                "",
                "Counts:",
                f"- Strategic IT: {counts['Strategic IT']} (7%)",
                f"- Constrained IT: {counts['Constrained IT']} (53%)",
                f"- Support IT: {counts['Support IT']} (40%)",
                f"- Total assigned: {len(rows)}",
                "",
                "INTERPRETIVE SNAPSHOT",
                "--------------------------------------------------",
                "- IT is perceived as strategically important, but competitive impact is lower.",
                "- The strategy-impact gap is the headline quantitative finding.",
                "- Alignment is slightly higher than responsiveness, but the operational gap is small in this exploratory sample.",
                "- Most cases fall into Constrained IT, suggesting that strategic intent does not consistently become differentiated impact.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    rows = load_rows()
    means = write_metrics(rows)
    counts = write_segments(rows)
    write_summary(rows, means, counts)
    print(f"Wrote public aggregate files from {len(rows)} local rows.")


if __name__ == "__main__":
    main()
