#!/usr/bin/env python3
"""
Interactive normalized time series comparing:
- Sensor-reported sound level (dba_mean)
- Waveform-derived RMS amplitude (rms_dbfs_mean)

Both series are z-score normalized and plotted on a shared timeline.
"""

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

# ======================================================
# Paths
# ======================================================
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

INP = RESULTS / "audio_daily_joined.csv"
OUT_HTML = FIGS / "sensor_vs_waveform_timeseries_zscore.html"

# ======================================================
# Load data
# ======================================================
df = pd.read_csv(INP)

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["dba_mean"] = pd.to_numeric(df["dba_mean"], errors="coerce")
df["rms_dbfs_mean"] = pd.to_numeric(df["rms_dbfs_mean"], errors="coerce")
df["n_audio"] = pd.to_numeric(df["n_audio"], errors="coerce")

# ------------------------------------------------------
# Filter to days with meaningful audio coverage
# ------------------------------------------------------
MIN_AUDIO = 100

df_ts = df[
    (df["n_audio"] >= MIN_AUDIO) &
    df["dba_mean"].notna() &
    df["rms_dbfs_mean"].notna()
].copy()

df_ts = df_ts.sort_values("date")

# ======================================================
# Z-score normalization
# ======================================================
df_ts["dba_z"] = (
    (df_ts["dba_mean"] - df_ts["dba_mean"].mean())
    / df_ts["dba_mean"].std()
)

df_ts["rms_z"] = (
    (df_ts["rms_dbfs_mean"] - df_ts["rms_dbfs_mean"].mean())
    / df_ts["rms_dbfs_mean"].std()
)

# ======================================================
# Build figure
# ======================================================
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df_ts["date"],
        y=df_ts["dba_z"],
        mode="lines",
        name="Sensor sound level (z-score)",
        hovertemplate=(
            "Date: %{x}<br>"
            "Sensor dBA (mean): %{customdata[0]:.2f}<br>"
            "z-score: %{y:.2f}<extra></extra>"
        ),
        customdata=df_ts[["dba_mean"]],
    )
)

fig.add_trace(
    go.Scatter(
        x=df_ts["date"],
        y=df_ts["rms_z"],
        mode="lines",
        name="Waveform RMS amplitude (z-score)",
        hovertemplate=(
            "Date: %{x}<br>"
            "Waveform RMS (mean): %{customdata[0]:.2f} dBFS<br>"
            "z-score: %{y:.2f}<extra></extra>"
        ),
        customdata=df_ts[["rms_dbfs_mean"]],
    )
)

# ======================================================
# Mark capture-failure day (robust method)
# ======================================================
fail_days = df[df["flag_capture_failure_candidate"] == True]

if not fail_days.empty:
    fail_date = pd.to_datetime(fail_days.iloc[0]["date"])

    # Vertical line as scatter trace
    fig.add_trace(
        go.Scatter(
            x=[fail_date, fail_date],
            y=[df_ts[["dba_z", "rms_z"]].min().min(),
               df_ts[["dba_z", "rms_z"]].max().max()],
            mode="lines",
            line=dict(dash="dash", width=2),
            name="Capture failure",
            hoverinfo="skip",
        )
    )

    # Annotation
    fig.add_annotation(
        x=fail_date,
        y=df_ts[["dba_z", "rms_z"]].max().max(),
        text="Capture failure<br>2023-11-13",
        showarrow=True,
        arrowhead=2,
        ax=40,
        ay=-40,
    )

# ======================================================
# Layout
# ======================================================
fig.update_layout(
    title="Normalized Time Series: Sensor Sound vs Waveform Amplitude",
    xaxis_title="Date",
    yaxis_title="Z-score (standardized)",
    hovermode="x unified",
    legend_title_text="",
    template="plotly_white",
)

# ======================================================
# Save HTML
# ======================================================
fig.write_html(str(OUT_HTML), include_plotlyjs="cdn")
print(f"✔ Wrote interactive HTML: {OUT_HTML}")

fig.show()

