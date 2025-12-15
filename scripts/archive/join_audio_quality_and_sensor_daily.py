#!/usr/bin/env python3
"""
Join waveform-derived audio quality daily metrics with sensor-derived audio daily metrics.

Inputs:
  results/audio_quality_daily.csv   (primary)
  results/audio_sensor_daily.csv    (secondary)

Output:
  results/audio_daily_joined.csv
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

AUDIO_QUALITY_DAILY = RESULTS / "audio_quality_daily.csv"
AUDIO_SENSOR_DAILY  = RESULTS / "audio_sensor_daily.csv"
OUT                 = RESULTS / "audio_daily_joined.csv"

print("Loading audio_quality_daily.csv...")
aq = pd.read_csv(AUDIO_QUALITY_DAILY)

print("Loading audio_sensor_daily.csv...")
asens = pd.read_csv(AUDIO_SENSOR_DAILY)

# -------------------------
# Parse and normalize dates
# -------------------------
aq["date"] = pd.to_datetime(aq["date"], errors="coerce").dt.date
asens["date"] = pd.to_datetime(asens["date"], errors="coerce").dt.date

bad_aq = aq["date"].isna().sum()
bad_as = asens["date"].isna().sum()
assert bad_aq == 0, f"Invalid dates in audio_quality_daily.csv: {bad_aq}"
assert bad_as == 0, f"Invalid dates in audio_sensor_daily.csv: {bad_as}"

# -------------------------
# Coerce numeric columns (sensor side can have blanks)
# -------------------------
for col in ["snd_lvl_mean", "dba_mean", "dba_p90", "n_events"]:
    if col in asens.columns:
        asens[col] = pd.to_numeric(asens[col], errors="coerce")

# -------------------------
# LEFT JOIN: quality is primary
# -------------------------
print("Joining (LEFT) quality → sensor on date...")
joined = aq.merge(asens, on="date", how="left")

# Useful flags for analysis/reporting
joined["sensor_missing"] = joined["n_events"].isna()
joined["sensor_present"] = ~joined["sensor_missing"]

# Example: if you want a simple “capture failure” heuristic:
# high sensor dBA but near-zero recordings
joined["flag_capture_failure_candidate"] = (
    (joined.get("dba_mean").notna())
    & (joined["n_audio"] <= 2)
    & (joined.get("dba_mean") >= 75)
)

# -------------------------
# Write output
# -------------------------
OUT.parent.mkdir(parents=True, exist_ok=True)
joined.to_csv(OUT, index=False)

print("✔ Wrote:", OUT)
print("Rows written (days):", len(joined))
print("Days with sensor data:", int(joined["sensor_present"].sum()))
print("Days missing sensor data:", int(joined["sensor_missing"].sum()))
print("Capture-failure candidates:", int(joined["flag_capture_failure_candidate"].sum()))

