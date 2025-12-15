#!/usr/bin/env python3
"""
audio_quality_calendar.py

Interactive calendar heatmap for DAILY AUDIO QUALITY.

Modes:
- RMS (dBFS)
- ZCR (zero-crossing rate)

Features:
- Year selector
- Metric selector (RMS ↔ ZCR)
- Annotated calendar cells
- Blank days for missing / invalid data
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
INPUT_CSV   = PROJECT_ROOT / "results" / "audio_quality_daily.csv"
OUTPUT_HTML = PROJECT_ROOT / "figures" / "audio_quality_calendar.html"


# ======================================================
# METRIC CONFIG
# ======================================================
METRICS = ["rms", "zcr"]

METRIC_CONFIG = {
    "rms": {
        "column": "rms_dbfs_mean",
        "label": "RMS Loudness (dBFS)",
        "cmin": -20,
        "cmax": -80,
        "colorscale": "Plasma",
        "fmt": "{:.1f}",
        "ticks": [-20, -30, -40, -50, -60, -70, -80],
    },
    "zcr": {
        "column": "zcr_mean",
        "label": "Zero Crossing Rate",
        "cmin": 0.0,
        "cmax": 0.15,
        "colorscale": "Viridis",
        "fmt": "{:.3f}",
        "ticks": [0.00, 0.03, 0.06, 0.09, 0.12, 0.15],
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

    for m in range(12):
        dim = calendar.monthrange(year, m + 1)[1]
        for d in range(dim, 31):
            mat[m, d] = np.nan

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
            f"n_audio: {int(row['n_audio'])}"
        )

    months = [calendar.month_abbr[m] for m in range(1, 13)]
    days   = [str(d) for d in range(1, 32)]

    return mat, text, hover, months, days


# ======================================================
# MAIN
# ======================================================
def main():

    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    df["year"] = df["date"].dt.year

    # --------------------------------------------------
    # STRICT INVALID-AUDIO MASKING (DEFENSIBLE)
    # --------------------------------------------------
    invalid = (df["zcr_mean"] == 0) | (df["rms_dbfs_mean"] <= -120)
    df.loc[invalid, "rms_dbfs_mean"] = np.nan

    years = sorted(df["year"].unique())
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
                    coloraxis="coloraxis" if metric == "rms" else "coloraxis2",
                    showscale = False,
                )
            )
            traces[(y, m_idx)] = trace_id

    # Default view
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
        return [
            # RMS BUTTON
            dict(
                label="RMS",
                method="update",
                args=[
                    {"visible": visibility[(year, 0)]},
                    {
                        "coloraxis.showscale": True,
                        "coloraxis2.showscale": False,
                    },
                ],
            ),

            # ZCR BUTTON
            dict(
                label="ZCR",
                method="update",
                args=[
                    {"visible": visibility[(year, 1)]},
                    {
                        "coloraxis.showscale": False,
                        "coloraxis2.showscale": True,
                    },
                ],
            ),
        ]

    # Year buttons
    year_buttons = []
    for y in years:
        year_buttons.append(
            dict(
                label=str(y),
                method="update",
                args=[
                    {"visible": visibility[(y, 0)]},  # default to RMS
                    {
                        "updatemenus[1].buttons": metric_buttons(y),
                        "updatemenus[1].active": 0,

                        # 🔑 FORCE RMS COLORAXIS ON YEAR CHANGE
                        "coloraxis.showscale": True,
                        "coloraxis2.showscale": False,
                    },
                ],
            )
        )

    # Layout
    fig.update_layout(
        title=dict(text="Audio Quality Calendar", x=0.5),
        width=1600,
        height=900,

        # RMS COLORAXIS (default visible)
        coloraxis=dict(
            colorscale=METRIC_CONFIG["rms"]["colorscale"],
            cmin=-90,
            cmax=-10,
            colorbar=dict(
                title=METRIC_CONFIG["rms"]["label"],
                tickvals=METRIC_CONFIG["rms"]["ticks"],
                len=0.8,
                thickness=20,
            ),
        ),

        # ZCR COLORAXIS (initially hidden)
        coloraxis2=dict(
            colorscale=METRIC_CONFIG["zcr"]["colorscale"],
            cmin=0.0,
            cmax=0.15,
            colorbar=dict(
                title=METRIC_CONFIG["zcr"]["label"],
                tickvals=METRIC_CONFIG["zcr"]["ticks"],
                len=0.8,
                thickness=20,
            ),
            showscale=False,  # 🔑 start hidden
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
