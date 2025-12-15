#!/usr/bin/env python3
"""
parse_traffic_sound_json.py

Parse newline-delimited traffic JSON logs and extract
sensor-reported audio metrics for analysis.

Outputs DAILY aggregates suitable for joining with
audio_quality_daily.csv.

Metrics extracted:
- snd_lvl (sensor sound level)
- dba_mean (mean of dBA window)
- dba_p90  (90th percentile of dBA window)
- n_events (number of sound events logged)

Source:
~/files/traffic/logs/traffic.txt*
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path


# ======================================================
# PATHS
# ======================================================
LOG_DIR = Path.home() / "files" / "traffic" / "logs"
OUTPUT_CSV = Path.home() / "ia626_project" / "results" / "audio_sensor_daily.csv"


# ======================================================
# MAIN
# ======================================================
def main():

    rows = []

    log_files = sorted(LOG_DIR.glob("traffic.txt*"))
    print("Found log files:", len(log_files))

    for log_fp in log_files:
        print("Parsing:", log_fp.name)

        with open(log_fp, "r") as f:
            for line in f:
                try:
                    rec = json.loads(line)

                    snd = rec.get("snd")
                    if not snd:
                        continue

                    dto = rec.get("dto")
                    if not dto:
                        continue

                    # Extract dBA window
                    dba_vals = snd.get("res", {}).get("dba")
                    if not dba_vals:
                        continue

                    rows.append({
                        "date": dto[:10],  # YYYY-MM-DD
                        "snd_lvl": snd.get("snd_lvl"),
                        "dba_mean": float(np.mean(dba_vals)),
                        "dba_p90": float(np.percentile(dba_vals, 90)),
                    })

                except Exception:
                    # Skip malformed lines silently
                    continue

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("No sound records extracted from logs")

    # --------------------------------------------------
    # Aggregate DAILY
    # --------------------------------------------------
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    daily = (
        df.groupby("date")
          .agg(
              snd_lvl_mean=("snd_lvl", "mean"),
              dba_mean=("dba_mean", "mean"),
              dba_p90=("dba_p90", "mean"),
              n_events=("dba_mean", "size"),
          )
          .reset_index()
    )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUTPUT_CSV, index=False)

    print("Wrote:", OUTPUT_CSV)
    print("Days:", daily.shape[0])


if __name__ == "__main__":
    main()
