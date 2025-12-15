#!/usr/bin/env python3
"""
Validation script for the traffic dataset.

Compares:
  - Folders on disk (valid + invalid years)
  - Dates in dataset_summary.csv
Ensures that the scan captured all valid data and correctly excluded invalid folders.
"""

import os
import pandas as pd

from scripts.archive.utils import (
    list_candidate_folders,
    list_valid_folders,
    list_invalid_year_folders,
    extract_date
)

# ============================================================
# Configuration
# ============================================================

IMG_ROOT = "/home/student/files/traffic/img/full"
SND_ROOT = "/home/student/files/traffic/snd"
CSV_PATH = "../results/dataset_summary.csv"


# ============================================================
# Validation
# ============================================================

def main():
    print("\n===================================================")
    print(" VALIDATING TRAFFIC DATASET SCAN")
    print("===================================================\n")

    # -------------------------
    # Load CSV
    # -------------------------
    try:
        df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return

    print(f"Loaded CSV: {CSV_PATH}")
    print(f"Total rows in CSV: {len(df)}\n")

    # ===========================
    # LIST FOLDERS ON DISK
    # ===========================
    img_valid   = list_valid_folders(IMG_ROOT)
    snd_valid   = list_valid_folders(SND_ROOT)

    img_invalid = list_invalid_year_folders(IMG_ROOT)
    snd_invalid = list_invalid_year_folders(SND_ROOT)

    print(f"Disk IMAGE folders (valid years): {len(img_valid)}")
    print(f"Disk AUDIO folders (valid years): {len(snd_valid)}\n")

    print(f"Disk IMAGE folders (invalid years): {img_invalid}")
    print(f"Disk AUDIO folders (invalid years): {snd_invalid}\n")

    # Convert valid folder names → date strings
    img_dates = sorted(set(extract_date(f) for f in img_valid))
    snd_dates = sorted(set(extract_date(f) for f in snd_valid))

    # -------------------------
    # CSV: extract modality-specific dates
    # -------------------------
    csv_img_dates = sorted(
        df[df["modality"] == "image"]["date"].dt.strftime("%Y-%m-%d").unique()
    )
    csv_snd_dates = sorted(
        df[df["modality"] == "audio"]["date"].dt.strftime("%Y-%m-%d").unique()
    )

    # -------------------------
    # Missing = on-disk but not in CSV
    # -------------------------
    missing_img = sorted(set(img_dates) - set(csv_img_dates))
    missing_snd = sorted(set(snd_dates) - set(csv_snd_dates))

    # -------------------------
    # Unexpected = in CSV but not on disk
    # -------------------------
    unexpected_img = sorted(set(csv_img_dates) - set(img_dates))
    unexpected_snd = sorted(set(csv_snd_dates) - set(snd_dates))

    # OUTPUT RESULTS

    print("---------------------------------------------------")
    print(" IMAGE: Dates on disk but NOT in CSV")
    print("---------------------------------------------------")
    print(" None" if not missing_img else "\n".join(f" {d}" for d in missing_img))

    print("\n---------------------------------------------------")
    print(" AUDIO: Dates on disk but NOT in CSV")
    print("---------------------------------------------------")
    print(" None" if not missing_snd else "\n".join(f" {d}" for d in missing_snd))

    print("\n---------------------------------------------------")
    print(" CSV dates NOT on IMAGE disk")
    print("---------------------------------------------------")
    print(" None" if not unexpected_img else "\n".join(f" {d}" for d in unexpected_img))

    print("\n---------------------------------------------------")
    print(" CSV dates NOT on AUDIO disk")
    print("---------------------------------------------------")
    print(" None" if not unexpected_snd else "\n".join(f" {d}" for d in unexpected_snd))

    # SUMMARY
    
    print("\n===================================================")
    print(" SUMMARY")
    print("===================================================\n")

    img_ok = (not missing_img and not unexpected_img)
    snd_ok = (not missing_snd and not unexpected_snd)

    print(f"Image folders fully match CSV?  {'YES' if img_ok else 'NO'}")
    print(f"Audio folders fully match CSV?  {'YES' if snd_ok else 'NO'}")

    # Final classification
    if img_ok and snd_ok:
        print("\n✔ SCAN IS CORRECT — All valid folders accounted for.\n")
    else:
        print("\n✖ MISMATCH DETECTED — Review differences above.\n")


if __name__ == "__main__":
    main()
