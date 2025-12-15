#!/usr/bin/env python3
"""
Traffic dataset scanner — uses shared utils.py logic.

Produces two CSV files:
  1. dataset_summary.csv        → valid date folders only
  2. dataset_invalid_dates.csv  → invalid or out-of-range date folders
"""

import pandas as pd
from scripts.archive.utils import (
    scan_modality_root
)


# ============================================================
# Main scan function
# ============================================================

def scan_dataset(
    img_root,
    snd_root,
    output_csv="../results/dataset_summary.csv",
    invalid_csv="../results/dataset_invalid_dates.csv"
):
    """
    Scans image + audio datasets.
    Returns:
        df_valid, df_invalid
    """

    print("\n==============================================")
    print(" SCANNING TRAFFIC DATASET")
    print("==============================================\n")

    # ------------------------------
    # Scan image and audio roots
    # ------------------------------
    img_valid, img_invalid = scan_modality_root(img_root, "image")
    snd_valid, snd_invalid = scan_modality_root(snd_root, "audio")

    # Merge
    valid_all = img_valid + snd_valid
    invalid_all = img_invalid + snd_invalid

    # ------------------------------
    # Save VALID entries
    # ------------------------------
    df_valid = pd.DataFrame(valid_all)

    if not df_valid.empty:
        df_valid["date"] = pd.to_datetime(df_valid["date"], errors="coerce")
        df_valid = df_valid.dropna(subset=["date"])
        df_valid = df_valid.sort_values("date")

    df_valid.to_csv(output_csv, index=False)

    # ------------------------------
    # Save INVALID entries
    # ------------------------------
    df_invalid = pd.DataFrame(invalid_all)
    df_invalid.to_csv(invalid_csv, index=False)

    # ------------------------------
    # Console summary
    # ------------------------------
    print(f"Valid rows saved:   {output_csv}  (rows={len(df_valid)})")
    print(f"Invalid rows saved: {invalid_csv} (rows={len(df_invalid)})\n")

    print("Completed dataset scan.\n")
    return df_valid, df_invalid


# ============================================================
# Run as script
# ============================================================

if __name__ == "__main__":
    IMG_ROOT = "/home/student/files/traffic/img/full"
    SND_ROOT = "/home/student/files/traffic/snd"

    scan_dataset(IMG_ROOT, SND_ROOT)