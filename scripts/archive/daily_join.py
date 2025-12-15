#!/usr/bin/env python3
"""
daily_join.py

Merge all daily-level datasets into a unified analytics table:

    - daily_counts.csv
    - image_quality_daily.csv
    - logs_daily.csv

Adds:
    - cleaned date fields
    - correlation matrix export
    - automated anomaly flags
    - summary printed to console

Output:
    results/daily_master.csv
    results/daily_master_correlations.csv
"""

import argparse
import pandas as pd
from pathlib import Path


def load_csv(path):
    """Load CSV and normalize 'date' column."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)
    if "date" not in df.columns:
        raise ValueError(f"'date' column not found in {path}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    return df


def add_anomaly_flags(df):
    """
    Add heuristic anomaly indicators:
        - low file counts
        - low image score
        - low log event volume
        - sudden structural changes
    """

    df["count_anomaly"] = df["total_files"].lt(df["total_files"].median() * 0.3)

    if "img_quality_mean" in df:
        df["quality_anomaly"] = df["img_quality_mean"].lt(
            df["img_quality_mean"].median() * 0.4
        )

    if "log_n_events" in df:
        df["log_anomaly"] = df["log_n_events"].lt(
            df["log_n_events"].median() * 0.3
        )

    # Combined flag
    df["any_anomaly"] = (
        df.get("count_anomaly", False)
        | df.get("quality_anomaly", False)
        | df.get("log_anomaly", False)
    )

    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", default="results/daily_counts.csv")
    parser.add_argument("--quality", default="results/image_quality_daily.csv")
    parser.add_argument("--logs", default="results/logs_daily.csv")
    parser.add_argument("--output", default="results/daily_master.csv")
    parser.add_argument("--correlations", default="results/daily_master_correlations.csv")
    args = parser.parse_args()

    print("Loading datasets...")

    df_counts = load_csv(args.counts)
    df_quality = load_csv(args.quality)
    df_logs = load_csv(args.logs)

    # Ensure expected names
    if "total_files" not in df_counts.columns:
        raise ValueError("daily_counts.csv must include total_files column")

    # Merge all datasets
    print("Merging daily datasets...")

    df = (
        df_counts
        .merge(df_quality, on="date", how="outer")
        .merge(df_logs, on="date", how="outer")
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Add anomaly detection
    print("Adding anomaly flags...")
    df = add_anomaly_flags(df)

    # Compute correlations
    print("Computing correlations...")
    numeric_cols = df.select_dtypes(include=["number"]).columns
    corr = df[numeric_cols].corr()

    # Write outputs
    output_path = Path(args.output)
    corr_path = Path(args.correlations)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    corr.to_csv(corr_path)

    print()
    print("✓ daily_master.csv written to:", output_path)
    print("✓ correlations written to:", corr_path)
    print()
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print()
    print("Preview:")
    print(df.head(10))


if __name__ == "__main__":
    main()
