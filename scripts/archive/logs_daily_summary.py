#!/usr/bin/env python3
"""
logs_daily_summary.py

Aggregate parsed traffic log events into daily metrics.

Usage:
    python3 scripts/logs_daily_summary.py \
        --input results/log_events_sample.csv \
        --output results/logs_daily.csv
"""

import argparse
import pandas as pd
from pathlib import Path


# ------------------------------------------------------
# Argument Parser
# ------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize log_events CSV into daily metrics."
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input CSV path (log_events.csv or log_events_sample.csv)."
    )

    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output CSV path for daily summary."
    )

    return parser.parse_args()


# ------------------------------------------------------
# Ensure parent directory exists
# ------------------------------------------------------
def ensure_parent_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------
# Main Logic
# ------------------------------------------------------
def main():
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Loading {input_path} ...")
    df = pd.read_csv(input_path)

    # Verify required column
    if "date" not in df.columns:
        raise ValueError("Input CSV must contain a 'date' column.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Numeric columns – convert safely
    numeric_cols = [
        "probs",
        "intersection_0", "intersection_1",
        "cross_0_0", "cross_0_1", "cross_1_0", "cross_1_1",
        "box_x1", "box_y1", "box_x2", "box_y2",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Group & Aggregate
    daily = (
        df.groupby("date")
          .agg(
              log_n_events=("probs", "count"),
              log_probs_mean=("probs", "mean"),
              inter0_mean=("intersection_0", "mean"),
              inter1_mean=("intersection_1", "mean"),
              cross00_mean=("cross_0_0", "mean"),
              cross01_mean=("cross_0_1", "mean"),
              cross10_mean=("cross_1_0", "mean"),
              cross11_mean=("cross_1_1", "mean"),
              box_x1_mean=("box_x1", "mean"),
              box_y1_mean=("box_y1", "mean"),
              box_x2_mean=("box_x2", "mean"),
              box_y2_mean=("box_y2", "mean"),
          )
          .reset_index()
    )

    # Save output
    ensure_parent_dir(output_path)
    daily.to_csv(output_path, index=False)

    print(f"\nWrote daily summary → {output_path}")
    print(f"Rows: {len(daily)}")
    print(f"Columns: {list(daily.columns)}\n")


if __name__ == "__main__":
    main()
