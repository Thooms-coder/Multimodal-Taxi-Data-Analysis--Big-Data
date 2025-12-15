#!/usr/bin/env python3
"""
audio_quality.py

Extract basic, defensible audio quality metrics from traffic audio (.mp3).

Per audio file:
- date
- relative_path
- duration_sec
- rms_dbfs
- zcr
- sample_rate
- file_size_bytes

Design:
- multiprocessing
- constant memory per worker
- calendar-restricted (optional, recommended)
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from multiprocessing import Pool, cpu_count

import numpy as np
import pandas as pd
import librosa
from tqdm import tqdm


# -----------------------------
# CONFIG
# -----------------------------
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac"}
DEFAULT_AUDIO_ROOT = Path("/home/student/files/traffic/snd")
DEFAULT_OUTPUT = Path("../results/audio_quality.csv")
DEFAULT_CALENDAR = Path("../results/daily_zero_filled.csv")


# -----------------------------
# LOGGING
# -----------------------------
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# -----------------------------
# DATE INFERENCE
# -----------------------------
def infer_date_from_path(audio_root: Path, path: Path) -> str:
    """
    Infer YYYY-MM-DD from top-level folder name (first 10 chars).
    """
    rel = path.relative_to(audio_root)
    top = rel.parts[0]
    return top[:10]


# -----------------------------
# AUDIO METRICS
# -----------------------------
def extract_audio_metrics(path: Path):
    y, sr = librosa.load(path, sr=None, mono=True)

    duration = float(librosa.get_duration(y=y, sr=sr))

    rms = np.mean(librosa.feature.rms(y=y))
    rms_dbfs = float(20 * np.log10(max(rms, 1e-12)))

    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))

    return duration, rms_dbfs, zcr, int(sr), path.stat().st_size


# -----------------------------
# WORKER
# -----------------------------
def worker(args):
    path_str, audio_root_str = args
    path = Path(path_str)
    audio_root = Path(audio_root_str)

    try:
        date = infer_date_from_path(audio_root, path)
        duration, rms_dbfs, zcr, sr, size = extract_audio_metrics(path)

        return {
            "date": date,
            "relative_path": str(path.relative_to(audio_root)),
            "duration_sec": duration,
            "rms_dbfs": rms_dbfs,
            "zcr": zcr,
            "sample_rate": sr,
            "file_size_bytes": size,
        }

    except Exception as e:
        return {"error": str(e), "path": str(path)}


# -----------------------------
# MAIN
# -----------------------------
def main():
    setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-root", default=DEFAULT_AUDIO_ROOT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--calendar", default=DEFAULT_CALENDAR)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    audio_root = Path(args.audio_root).resolve()
    output = Path(args.output).resolve()

    # Load calendar dates (recommended)
    calendar_dates = None
    if args.calendar:
        cal = pd.read_csv(args.calendar, parse_dates=["date"])
        calendar_dates = set(cal["date"].dt.strftime("%Y-%m-%d"))

        logging.info("Restricting extraction to %d calendar days", len(calendar_dates))

    # Collect audio files
    all_files = [
        p for p in audio_root.rglob("*")
        if p.suffix.lower() in AUDIO_EXTENSIONS
        and (calendar_dates is None or infer_date_from_path(audio_root, p) in calendar_dates)
    ]

    logging.info("Found %d audio files to process", len(all_files))

    workers = args.workers or cpu_count()
    logging.info("Using %d workers", workers)

    rows = []
    errors = 0

    with Pool(workers) as pool:
        for res in tqdm(
            pool.imap_unordered(worker, [(str(p), str(audio_root)) for p in all_files]),
            total=len(all_files),
            desc="Extracting audio features",
        ):
            if "error" in res:
                errors += 1
            else:
                rows.append(res)

    df = pd.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    logging.info("Wrote %s (%d rows)", output, len(df))
    logging.info("Errors: %d", errors)


if __name__ == "__main__":
    main()
