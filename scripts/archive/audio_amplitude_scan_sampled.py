#!/usr/bin/env python3
"""
audio_amplitude_scan_sampled.py

Sampled extraction of linear-domain audio metrics from raw traffic audio files.

Metrics (per file):
- RMS amplitude (linear)
- Peak amplitude
- Crest factor

Sampling strategy:
- Randomly sample up to MAX_FILES_PER_DAY per YYYY-MM-DD folder
- Enforce a global MAX_TOTAL_FILES cap

Folder structure assumed:
~/files/traffic/snd/YYYY-MM-DD[_h|_l]/*.wav | *.mp3
"""

import random
import numpy as np
import pandas as pd
import librosa
from pathlib import Path


# ======================================================
# CONFIG
# ======================================================
AUDIO_ROOT = Path.home() / "files" / "traffic" / "snd"
OUTPUT_CSV = Path.home() / "ia626_project" / "results" / "audio_amplitude_filelevel_sampled.csv"

MAX_FILES_PER_DAY = 25      # 20–50 is reasonable
MAX_TOTAL_FILES   = 50_000  # hard safety cap
RANDOM_SEED = 42


# ======================================================
# MAIN
# ======================================================
def main():

    random.seed(RANDOM_SEED)
    rows = []

    # --------------------------------------------------
    # Iterate day folders
    # --------------------------------------------------
    day_dirs = sorted([d for d in AUDIO_ROOT.iterdir() if d.is_dir()])
    print("Found day folders:", len(day_dirs))

    for day_dir in day_dirs:

        # 🔑 FIX: strip suffix (_h / _l)
        date_str = day_dir.name.split("_")[0]

        files = list(day_dir.glob("*.wav")) + list(day_dir.glob("*.mp3"))
        if not files:
            continue

        # Sample per day
        if len(files) > MAX_FILES_PER_DAY:
            files = random.sample(files, MAX_FILES_PER_DAY)

        for fp in files:
            try:
                y, sr = librosa.load(
                    fp,
                    sr=None,
                    mono=True,
                    res_type="kaiser_fast"
                )

                if y.size == 0:
                    continue

                rms  = np.sqrt(np.mean(y ** 2))
                peak = np.max(np.abs(y))

                rows.append({
                    "file": fp.name,
                    "date": date_str,
                    "rms_amplitude": rms,
                    "peak_amplitude": peak,
                    "crest_factor": peak / rms if rms > 0 else np.nan,
                })

            except Exception as e:
                print(f"Failed: {fp} → {e}")

            # Global safety cap
            if len(rows) >= MAX_TOTAL_FILES:
                print("Reached MAX_TOTAL_FILES cap")
                break

        if len(rows) >= MAX_TOTAL_FILES:
            break

    # --------------------------------------------------
    # Finalize dataframe
    # --------------------------------------------------
    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("Sampling produced no rows — check AUDIO_ROOT")

    # Robust date parsing
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["date"])

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    print("Sampled rows:", df.shape[0])
    print("Wrote:", OUTPUT_CSV)


if __name__ == "__main__":
    main()

