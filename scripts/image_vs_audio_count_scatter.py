#!/usr/bin/env python3
"""
image_vs_audio_count_scatter.py

Scatter plot comparing daily IMAGE vs AUDIO file counts.

Purpose:
- Detect modality imbalance
- Identify pipeline failures
- Complement calendar heatmaps

Encoding:
- X-axis: image count
- Y-axis: audio count (with small visual jitter at zero)
- Color: image − audio difference
- Hover: date + true counts

Notes:
- All data retained
- Axis limits truncated at 99th percentile to reduce whitespace
- Small vertical jitter applied ONLY to zero-audio days (visual only)
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# ======================================================
# PATHS
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "results" / "daily_zero_filled.csv"
OUTPUT_HTML = PROJECT_ROOT / "figures" / "image_vs_audio_count_scatter.html"

VALID_YEARS = [2023, 2024, 2025]


# ======================================================
# MAIN
# ======================================================
def main():

    # ------------------------------
    # Load + clean
    # ------------------------------
    df = pd.read_csv(INPUT_CSV)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df["year"] = df["date"].dt.year
    df = df[df["year"].isin(VALID_YEARS)]

    # --------------------------------
    # Resolve image/audio count columns
    # --------------------------------
    IMAGE_COL_CANDIDATES = ["image_files", "image_count", "image"]
    AUDIO_COL_CANDIDATES = ["audio_files", "audio_count", "audio"]

    def resolve_column(candidates, df_cols, label):
        for c in candidates:
            if c in df_cols:
                return c
        raise ValueError(
            f"Could not find {label} column. "
            f"Tried: {candidates}. "
            f"Available columns: {list(df_cols)}"
        )

    image_col = resolve_column(IMAGE_COL_CANDIDATES, df.columns, "image")
    audio_col = resolve_column(AUDIO_COL_CANDIDATES, df.columns, "audio")

    print(f"Using columns → image: {image_col}, audio: {audio_col}")

    # ------------------------------
    # Difference metric
    # ------------------------------
    df["diff"] = df[image_col] - df[audio_col]

    print("Rows:", df.shape[0])
    print("Years:", sorted(df["year"].unique()))

    # --------------------------------
    # Axis limits (reduce whitespace)
    # --------------------------------
    x_max = df[image_col].quantile(0.99)
    y_max = df[audio_col].quantile(0.99)

    # --------------------------------
    # Small vertical jitter for zero-audio days (visual only)
    # --------------------------------
    df["_audio_plot"] = df[audio_col].astype(float)

    zero_mask = df[audio_col] == 0
    n_zero = zero_mask.sum()

    if n_zero > 0:
        jitter = 0.02 * y_max * (
            pd.Series(range(n_zero)) / max(1, n_zero)
        )
        df.loc[zero_mask, "_audio_plot"] += jitter.values

    # --------------------------------
    # Build hover customdata (date, true audio)
    # --------------------------------
    customdata = list(
        zip(
            df["date"].dt.strftime("%Y-%m-%d"),
            df[audio_col]
        )
    )

    # ------------------------------
    # Scatter plot
    # ------------------------------
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df[image_col],
            y=df["_audio_plot"],   # jittered values for plotting only
            mode="markers",
            marker=dict(
                size=5,
                color=df["diff"],
                colorscale="RdBu",
                colorbar=dict(
                    title="Image − Audio",
                    thickness=18,
                ),
                showscale=True,
                line=dict(width=0.5, color="black"),
                opacity=0.85,
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Images: %{x}<br>"
                "Audio: %{customdata[1]}<br>"
                "Diff: %{marker.color}<extra></extra>"
            ),
        )
    )

    # ------------------------------
    # Layout
    # ------------------------------
    fig.update_layout(
        title=dict(
            text="Daily Image vs Audio File Counts",
            x=0.5,
        ),
        xaxis=dict(
            title="Image Files per Day",
            range=[0, x_max],
            zeroline=False,
        ),
        yaxis=dict(
            title="Audio Files per Day",
            range=[0, y_max],
            zeroline=False,
        ),
        width=1000,
        height=800,
        plot_bgcolor="white",
        paper_bgcolor="white",
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

