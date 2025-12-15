#!/usr/bin/env python3
"""
image_vs_audio_quality_scatter.py

Cross-modal quality analysis:
IMAGE sharpness (blur) vs AUDIO loudness (RMS),
faceted by year.

Purpose:
- Assess whether image and audio quality degradations co-occur
- Compare behavior across years (system stability)
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path


# ======================================================
# PATHS
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

IMG_CSV = PROJECT_ROOT / "results" / "image_quality_daily.csv"
AUD_CSV = PROJECT_ROOT / "results" / "audio_quality_daily.csv"

OUTPUT_HTML = PROJECT_ROOT / "figures" / "image_vs_audio_quality_scatter_faceted.html"

VALID_YEARS = [2023, 2024, 2025]


# ======================================================
# MAIN
# ======================================================
def main():

    # ------------------------------
    # Load data
    # ------------------------------
    img = pd.read_csv(IMG_CSV)
    aud = pd.read_csv(AUD_CSV)

    # Robust date handling
    img["date"] = pd.to_datetime(img["date"], errors="coerce")
    aud["date"] = pd.to_datetime(aud["date"], errors="coerce")

    img = img.dropna(subset=["date"])
    aud = aud.dropna(subset=["date"])

    # Restrict to valid years
    img = img[img["date"].dt.year.isin(VALID_YEARS)]
    aud = aud[aud["date"].dt.year.isin(VALID_YEARS)]

    # Merge
    df = img.merge(aud, on="date", how="inner")
    df["year"] = df["date"].dt.year

    # Valid-day filtering
    df = df[
        (df["n_images"] > 0) &
        (df["n_audio"] > 0) &
        (df["rms_dbfs_mean"] > -120) &
        (df["zcr_mean"] > 0)
    ]

    print("Valid rows:", df.shape[0])
    print("Years:", sorted(df["year"].unique()))

    # ------------------------------
    # Global axis limits (shared)
    # ------------------------------
    x_min = df["blur_mean"].quantile(0.01)
    x_max = df["blur_mean"].quantile(0.99)

    y_min = df["rms_dbfs_mean"].quantile(0.01)
    y_max = df["rms_dbfs_mean"].quantile(0.99)

    # ------------------------------
    # Build faceted figure
    # ------------------------------
    fig = make_subplots(
        rows=1,
        cols=3,
        shared_xaxes=True,
        shared_yaxes=True,
        subplot_titles=[str(y) for y in VALID_YEARS],
    )

    for i, year in enumerate(VALID_YEARS, start=1):
        df_y = df[df["year"] == year]

        fig.add_trace(
            go.Scatter(
                x=df_y["blur_mean"],
                y=df_y["rms_dbfs_mean"],
                mode="markers",
                marker=dict(
                    size=5,
                    color=df_y["n_images"],
                    colorscale="Viridis",
                    cmin=df["n_images"].min(),
                    cmax=df["n_images"].max(),
                    showscale=(i == 3),  # show colorbar once
                    colorbar=dict(
                        title="Images per Day",
                        thickness=18,
                    ),
                    opacity=0.8,
                    line=dict(width=0.4, color="black"),
                ),
                customdata=list(
                    zip(
                        df_y["date"].dt.strftime("%Y-%m-%d"),
                        df_y["n_images"],
                        df_y["n_audio"],
                    )
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Blur: %{x:.0f}<br>"
                    "RMS: %{y:.1f} dBFS<br>"
                    "Images: %{customdata[1]}<br>"
                    "Audio files: %{customdata[2]}<extra></extra>"
                ),
                showlegend=False,
            ),
            row=1,
            col=i,
        )

    # ------------------------------
    # Layout
    # ------------------------------
    fig.update_layout(
        title=dict(
            text="Image vs Audio Quality by Year (Blur vs RMS)",
            x=0.5,
        ),
        width=2000,
        height=600,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(
        title_text="Image Sharpness (Laplacian Variance)",
        range=[x_min, x_max],
        zeroline=False,
    )

    fig.update_yaxes(
        title_text="Audio Loudness (RMS dBFS)",
        range=[y_min, y_max],
        zeroline=False,
    )

    # ------------------------------
    # Save + show
    # ------------------------------
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUTPUT_HTML)
    fig.show()

    print("Saved:", OUTPUT_HTML)


if __name__ == "__main__":
    main()
