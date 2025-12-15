#!/usr/bin/env python3
"""
image_quality_daily.py

FAST daily aggregation of image quality metrics
from an existing per-image CSV (image_quality.csv).

Produces ONE ROW PER DATE.

Metrics per day:
- n_images
- blur_mean
- blur_p10
- brightness_mean
- contrast_mean
- file_size_mean
"""

import pandas as pd
from pathlib import Path


# -----------------------------
# PATHS
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "results" / "image_quality.csv"
OUTPUT_CSV = PROJECT_ROOT / "results" / "image_quality_daily.csv"


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

    # Sanity checks
    print("Raw rows:", df.shape[0])
    print("Unique dates (raw):", df["date"].nunique())

    # Daily aggregation
    daily = (
        df
        .groupby("date")
        .agg(
            n_images=("file_name", "count"),
            blur_mean=("blur_laplacian_var", "mean"),
            blur_p10=("blur_laplacian_var", lambda x: x.quantile(0.10)),
            brightness_mean=("brightness_mean", "mean"),
            contrast_mean=("contrast_std", "mean"),
            file_size_mean=("file_size_bytes", "mean"),
        )
        .reset_index()
        .sort_values("date")
    )

    # Integrity check
    assert daily["n_images"].sum() == df.shape[0], \
        "ERROR: Aggregation dropped rows"

    # Write output
    daily.to_csv(OUTPUT_CSV, index=False)

    print("Daily rows:", daily.shape[0])
    print("Wrote:", OUTPUT_CSV)


if __name__ == "__main__":
    main()
