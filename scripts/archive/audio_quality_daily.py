#!/usr/bin/env python3
"""
audio_quality_daily.py

FAST daily aggregation of audio quality metrics
from an existing per-audio CSV (audio_quality.csv).

Produces ONE ROW PER DATE.

Metrics per day:
- n_audio
- rms_dbfs_mean
- rms_dbfs_p10
- rms_dbfs_p90
- zcr_mean
- zcr_std
- duration_mean
- file_size_mean
"""

import pandas as pd
from pathlib import Path


# -----------------------------
# PATHS
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV  = PROJECT_ROOT / "results" / "audio_quality.csv"
OUTPUT_CSV = PROJECT_ROOT / "results" / "audio_quality_daily.csv"


# -----------------------------
# MAIN
# -----------------------------
def main():

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_CSV}")

    # Load CSV
    df = pd.read_csv(
        INPUT_CSV,
        parse_dates=["date"]
    )

    # Normalize to date-only (safety)
    df["date"] = df["date"].dt.normalize()

    # Sanity checks
    print("Raw rows:", df.shape[0])
    print("Unique dates (raw):", df["date"].nunique())

    # Daily aggregation
    daily = (
        df
        .groupby("date")
        .agg(
            n_audio=("relative_path", "count"),
            rms_dbfs_mean=("rms_dbfs", "mean"),
            rms_dbfs_p10=("rms_dbfs", lambda x: x.quantile(0.10)),
            rms_dbfs_p90=("rms_dbfs", lambda x: x.quantile(0.90)),
            zcr_mean=("zcr", "mean"),
            zcr_std=("zcr", "std"),
            duration_mean=("duration_sec", "mean"),
            file_size_mean=("file_size_bytes", "mean"),
        )
        .reset_index()
        .sort_values("date")
    )

    # Integrity check
    assert daily["n_audio"].sum() == df.shape[0], \
        "ERROR: Aggregation dropped rows"

    # Write output
    daily.to_csv(OUTPUT_CSV, index=False)

    print("Daily rows:", daily.shape[0])
    print("Wrote:", OUTPUT_CSV)


if __name__ == "__main__":
    main()
