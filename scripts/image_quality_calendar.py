#!/usr/bin/env python3
"""
image_quality_calendar.py

Interactive calendar heatmap for DAILY IMAGE QUALITY.

Modes:
- Blur (Laplacian variance)
- Brightness (mean grayscale)
- Contrast (grayscale std dev)

Features:
- Year selector
- Metric selector
- Annotated calendar cells
- Blank cells for missing / invalid days
"""

import numpy as np
import pandas as pd
import calendar
import plotly.graph_objects as go
from pathlib import Path


# ======================================================
# PATHS
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV    = PROJECT_ROOT / "results" / "image_quality_daily.csv"
OUTPUT_HTML  = PROJECT_ROOT / "figures" / "image_quality_calendar.html"


# ======================================================
# METRIC CONFIG
# ======================================================
METRICS = ["blur", "brightness", "contrast"]

METRIC_CONFIG = {
    "blur": {
        "column": "blur_mean",
        "label": "Blur (Laplacian Variance)",
        "cmin": 0,
        "cmax": 15000,
        "colorscale": "Greys_r",
        "fmt": "{:.0f}",
        "ticks": [0, 3000, 6000, 9000, 12000, 15000],
    },
    "brightness": {
        "column": "brightness_mean",
        "label": "Brightness (Mean Intensity)",
        "cmin": 0,
        "cmax": 120,
        "colorscale": "ylorbr",
        "fmt": "{:.0f}",
        "ticks": [0, 24, 48, 72, 96, 120],
    },
    "contrast": {
        "column": "contrast_mean",
        "label": "Contrast (Std Dev)",
        "cmin": 0,
        "cmax": 80,
        "colorscale": "Purples",
        "fmt": "{:.1f}",
        "ticks": [0, 16, 32, 48, 64, 80],
    },
}


# ======================================================
# BUILD MONTH × DAY MATRIX
# ======================================================
def build_matrix(df_year, metric, year):

    mat   = np.full((12, 31), np.nan)
    text  = np.full((12, 31), "", dtype=object)
    hover = np.full((12, 31), "", dtype=object)

    cfg = METRIC_CONFIG[metric]

    # Mark invalid calendar days
    for m in range(12):
        dim = calendar.monthrange(year, m + 1)[1]
        for d in range(dim, 31):
            mat[m, d] = np.nan

    # Fill data
    for _, row in df_year.iterrows():
        m = row["date"].month - 1
        d = row["date"].day - 1
        val = row[cfg["column"]]

        if pd.isna(val):
            continue

        mat[m, d]  = val
        text[m, d] = cfg["fmt"].format(val)

        hover[m, d] = (
            f"<b>{row['date'].date()}</b><br>"
            f"{cfg['label']}: {cfg['fmt'].format(val)}<br>"
            f"n_images: {int(row['n_images'])}"
        )

    months = [calendar.month_abbr[m] for m in range(1, 13)]
    days   = [str(d) for d in range(1, 32)]

    return mat, text, hover, months, days


# ======================================================
# MAIN
# ======================================================
def main():

    df = pd.read_csv(INPUT_CSV)

    # Force date parsing (robust)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop rows with invalid dates (defensible)
    n_bad = df["date"].isna().sum()
    if n_bad > 0:
        print(f"Dropping {n_bad} rows with invalid dates")
        df = df.dropna(subset=["date"])

    VALID_YEARS = [2023, 2024, 2025]

    df = df[df["date"].dt.year.isin(VALID_YEARS)]
    df["year"] = df["date"].dt.year

    years = VALID_YEARS

    print("Years:", years)

    fig = go.Figure()
    traces = {}

    for y in years:
        df_y = df[df["year"] == y]

        for m_idx, metric in enumerate(METRICS):
            mat, text, hover, months, days = build_matrix(df_y, metric, y)
            cfg = METRIC_CONFIG[metric]

            trace_id = len(fig.data)
            fig.add_trace(
                go.Heatmap(
                    z=mat,
                    x=days,
                    y=months,
                    text=text,
                    texttemplate="%{text}",
                    hovertext=hover,
                    hovertemplate="%{hovertext}<extra></extra>",
                    colorscale=cfg["colorscale"],
                    zmin=cfg["cmin"],
                    zmax=cfg["cmax"],
                    visible=False,
                    xgap=1,
                    ygap=1,
                    coloraxis=f"coloraxis{m_idx+1}",
                    showscale=False,
                )
            )
            traces[(y, m_idx)] = trace_id

    # Default view: first year, Blur
    fig.data[traces[(years[0], 0)]].visible = True

    # Visibility masks
    visibility = {}
    for y in years:
        for m_idx in range(len(METRICS)):
            mask = [False] * len(fig.data)
            mask[traces[(y, m_idx)]] = True
            visibility[(y, m_idx)] = mask

    # Metric buttons
    def metric_buttons(year):
        buttons = []
        for m_idx, metric in enumerate(METRICS):
            buttons.append(
                dict(
                    label=metric.capitalize(),
                    method="update",
                    args=[
                        {"visible": visibility[(year, m_idx)]},
                        {
                            **{
                                f"coloraxis{i+1}.showscale": i == m_idx
                                for i in range(len(METRICS))
                            }
                        },
                    ],
                )
            )
        return buttons

    # Year buttons
    year_buttons = []
    for y in years:
        year_buttons.append(
            dict(
                label=str(y),
                method="update",
                args=[
                    {"visible": visibility[(y, 0)]},  # default Blur
                    {
                        "updatemenus[1].buttons": metric_buttons(y),
                        "updatemenus[1].active": 0,
                        "coloraxis1.showscale": True,
                        "coloraxis2.showscale": False,
                        "coloraxis3.showscale": False,
                    },
                ],
            )
        )

    # Layout
    fig.update_layout(
        title=dict(text="Image Quality Calendar", x=0.5),
        width=1600,
        height=900,

        coloraxis1=dict(
            colorscale=METRIC_CONFIG["blur"]["colorscale"],
            cmin=METRIC_CONFIG["blur"]["cmin"],
            cmax=METRIC_CONFIG["blur"]["cmax"],
            colorbar=dict(
                title=METRIC_CONFIG["blur"]["label"],
                tickvals=METRIC_CONFIG["blur"]["ticks"],
                len=0.8,
                thickness=20,
            ),
        ),

        coloraxis2=dict(
            colorscale=METRIC_CONFIG["brightness"]["colorscale"],
            cmin=METRIC_CONFIG["brightness"]["cmin"],
            cmax=METRIC_CONFIG["brightness"]["cmax"],
            colorbar=dict(
                title=METRIC_CONFIG["brightness"]["label"],
                tickvals=METRIC_CONFIG["brightness"]["ticks"],
                len=0.8,
                thickness=20,
            ),
            showscale=False,
        ),

        coloraxis3=dict(
            colorscale=METRIC_CONFIG["contrast"]["colorscale"],
            cmin=METRIC_CONFIG["contrast"]["cmin"],
            cmax=METRIC_CONFIG["contrast"]["cmax"],
            colorbar=dict(
                title=METRIC_CONFIG["contrast"]["label"],
                tickvals=METRIC_CONFIG["contrast"]["ticks"],
                len=0.8,
                thickness=20,
            ),
            showscale=False,
        ),

        updatemenus=[
            dict(type="buttons", x=0.05, y=1.12, buttons=year_buttons),
            dict(type="buttons", x=0.40, y=1.12, buttons=metric_buttons(years[0])),
        ],

        yaxis=dict(autorange="reversed", ticks=""),
        xaxis=dict(ticks=""),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUTPUT_HTML)
    fig.show()

    print("Saved:", OUTPUT_HTML)


if __name__ == "__main__":
    main()
