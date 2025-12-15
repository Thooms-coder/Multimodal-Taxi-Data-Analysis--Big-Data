#!/usr/bin/env python3
"""
Check that each valid date has both image and audio folders.

This ensures that the dataset is balanced at the folder level
(independent of file counts).
"""

import os
import pandas as pd
from scripts.archive.utils import (
    list_valid_folders,
    extract_date
)

# ============================================
# CONFIG
# ============================================

IMG_ROOT = "/home/student/files/traffic/img/full"
SND_ROOT = "/home/student/files/traffic/snd"

OUTPUT_CSV = "../results/folder_pairing_summary.csv"


# ============================================
# MAIN LOGIC
# ============================================

def main():
    print("\n===================================================")
    print(" FOLDER PAIRING ANALYSIS")
    print("===================================================\n")

    # ------------------------------------------------
    # List valid-year folders only
    # ------------------------------------------------
    img_valid_folders = list_valid_folders(IMG_ROOT)
    snd_valid_folders = list_valid_folders(SND_ROOT)

    img_dates = sorted(set(extract_date(f) for f in img_valid_folders))
    snd_dates = sorted(set(extract_date(f) for f in snd_valid_folders))

    img_set = set(img_dates)
    snd_set = set(snd_dates)

    # ------------------------------------------------
    # Identify pairing relations
    # ------------------------------------------------
    paired_dates     = sorted(img_set & snd_set)
    img_only_dates   = sorted(img_set - snd_set)
    snd_only_dates   = sorted(snd_set - img_set)
    no_data_dates    = []     # Should never happen because disk only shows existing folders

    # ------------------------------------------------
    # Print summary
    # ------------------------------------------------
    print(f"Valid IMAGE dates found: {len(img_dates)}")
    print(f"Valid AUDIO dates found: {len(snd_dates)}")
    print(f"Dates with BOTH image & audio: {len(paired_dates)}\n")

    print("---------------------------------------------------")
    print(" DATES WITH IMAGE ONLY")
    print("---------------------------------------------------")
    print(" None" if not img_only_dates else "\n".join(" " + d for d in img_only_dates))

    print("\n---------------------------------------------------")
    print(" DATES WITH AUDIO ONLY")
    print("---------------------------------------------------")
    print(" None" if not snd_only_dates else "\n".join(" " + d for d in snd_only_dates))

    # ------------------------------------------------
    # Saving summary to CSV
    # ------------------------------------------------
    df = pd.DataFrame({
        "date": sorted(img_set | snd_set),
        "has_image": [d in img_set for d in sorted(img_set | snd_set)],
        "has_audio": [d in snd_set for d in sorted(img_set | snd_set)],
    })

    df["pair_status"] = df.apply(
        lambda r: "paired" if r.has_image and r.has_audio
                  else "image_only" if r.has_image
                  else "audio_only" if r.has_audio
                  else "missing_both",
        axis=1
    )

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved pairing summary to {OUTPUT_CSV}")

    # ------------------------------------------------
    # Final high-level status
    # ------------------------------------------------
    print("\n===================================================")
    print(" SUMMARY")
    print("===================================================\n")

    if img_only_dates or snd_only_dates:
        print("✖ Pairing incomplete — folders missing for some dates.\n")
    else:
        print("✔ All dates have both IMAGE and AUDIO folders.\n")


if __name__ == "__main__":
    main()
