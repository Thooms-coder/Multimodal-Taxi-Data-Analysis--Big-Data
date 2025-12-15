#!/usr/bin/env python3
"""
audio_amplitude_vs_dbfs.py

Validate linear amplitude ↔ dBFS relationship
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AMP_CSV  = PROJECT_ROOT / "results" / "audio_amplitude_daily.csv"
DBFS_CSV = PROJECT_ROOT / "results" / "audio_quality_daily.csv"
OUTPUT   = PROJECT_ROOT / "figures" / "amplitude_vs_dbfs.html"

VALID_YEARS = [2023, 2024, 2025]


def main():

    amp  = pd.read_csv(AMP_CSV, parse_dates=["date"])
    dbfs = pd.read_csv(DBFS_CSV, parse_dates=["date"])

    df = amp.merge(dbfs, on="date", how="inner")
    df = df[df["date"].dt.year.isin(VALID_YEARS)]

    df["log_rms_amp"] = np.log10(df["rms_amp_mean"])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["log_rms_amp"],
            y=df["rms_dbfs_mean"],
            mode="markers",
            marker=dict(
                size=6,
                color=df["crest_mean"],
                colorscale="Viridis",
                colorbar=dict(title="Crest Factor"),
                line=dict(width=0.3, color="black"),
            ),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "log10(RMS amp): %{x:.3f}<br>"
                "RMS dBFS: %{y:.1f}<br>"
                "Crest: %{marker.color:.2f}<extra></extra>"
            ),
            customdata=df["date"].dt.strftime("%Y-%m-%d"),
        )
    )

    fig.update_layout(
        title="Linear Amplitude vs RMS dBFS (Daily)",
        xaxis_title="log10(RMS Amplitude)",
        yaxis_title="RMS Loudness (dBFS)",
        width=1000,
        height=800,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUTPUT)
    fig.show()

    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
