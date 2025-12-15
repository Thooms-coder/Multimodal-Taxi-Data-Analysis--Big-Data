import numpy as np
import pandas as pd
import calendar
import plotly.graph_objects as go


# ======================================================
# BUILD 12×31 MATRIX WITH NaN FOR BLANK CELLS
# ======================================================
def build_month_day_matrix(df_year, column, year):
    mat   = np.full((12, 31), np.nan)
    hover = np.full((12, 31), "", dtype=object)
    label = np.full((12, 31), "", dtype=object)

    months = [calendar.month_abbr[m] for m in range(1, 13)]
    days   = [str(d) for d in range(1, 32)]

    # Mark invalid days
    for m in range(12):
        dim = calendar.monthrange(year, m + 1)[1]
        for d in range(dim, 31):
            mat[m, d] = np.nan

    # Fill actual data
    for _, row in df_year.iterrows():
        m = row["date"].month - 1
        d = row["date"].day - 1
        val = float(row[column])

        mat[m, d] = val
        label[m, d] = f"{val:.0f}"
        hover[m, d] = f"{row['date'].date()}<br>{column}: {val}"

    # Fill hover for valid-but-empty cells
    months_list = [calendar.month_abbr[m] for m in range(1, 13)]
    for m in range(12):
        for d in range(31):
            if np.isnan(mat[m, d]):
                continue
            if label[m, d] == "":
                hover[m, d] = f"{months_list[m]} {d+1}, {year}<br>No data"

    return mat, label, hover, months, days



# ======================================================
# MAIN CALENDAR
# ======================================================
# ======================================================
# MAIN CALENDAR
# ======================================================
def plotly_monthday_calendar(df, years):

    years = [int(y) for y in years]
    df["year"] = df["date"].dt.year.astype(int)

    fig = go.Figure()
    modes = ["image", "audio", "diff"]

    current_mode = {"value": 0}

    # Colorscales
    mode_colors = {
        "image": [[0.0, "#FFFFFF"], [1.0, "#08519C"]],
        "audio": [[0.0, "#FFFFFF"], [1.0, "#004D40"]],
        "diff" : [
            [0.0, "#004D40"],   # negative
            [0.5, "#FFFFFF"],   # zero
            [1.0, "#08519C"]    # positive
        ]
    }

    traces = {}
    diff_ranges = {}       # <-- FIXED: defined early

    # ======================================================
    # BUILD TRACES FOR EACH (YEAR, MODE)
    # ======================================================
    for y in years:

        df_y = df[df["year"] == y].copy()
        agg = df_y.groupby(["date", "modality"])["file_count"].sum().unstack(fill_value=0)

        agg["image"] = agg.get("image", 0)
        agg["audio"] = agg.get("audio", 0)
        agg["diff"]  = agg["image"] - agg["audio"]

        df_year = agg.reset_index()

        for mode_idx, mode in enumerate(modes):

            mat, label, hover, months, days = build_month_day_matrix(df_year, mode, y)

            real_vals = mat[~np.isnan(mat)]

            # Determine z-scaling
            if len(real_vals) == 0:
                zmin, zmax = 0, 1

                if mode == "diff":
                    diff_ranges[y] = 1     # fallback symmetric scale

            else:
                if mode == "diff":
                    max_abs = max(abs(real_vals.min()), abs(real_vals.max()))
                    if max_abs == 0:
                        max_abs = 1       # prevent cmin=cmax=0

                    zmin, zmax = -max_abs, max_abs
                    diff_ranges[y] = max_abs

                else:
                    zmin, zmax = 0, real_vals.max()

            trace_index = len(fig.data)

            fig.add_trace(
                go.Heatmap(
                    z=mat,
                    x=days,
                    y=months,
                    text=label,
                    hovertext=hover,
                    hovertemplate="%{hovertext}<extra></extra>",
                    texttemplate="%{text}",
                    textfont=dict(size=10, color="black"),
                    colorscale=mode_colors[mode],
                    zmin=zmin, zmax=zmax,
                    visible=False,
                    showscale=True,
                    xgap=1, ygap=1,
                    coloraxis="coloraxis"
                )
            )

            traces[(y, mode_idx)] = trace_index


    # ======================================================
    # VISIBILITY MASKS
    # ======================================================
    n_traces = len(fig.data)
    visibility = {}

    for y in years:
        for mode_idx in range(len(modes)):
            mask = [False] * n_traces
            mask[traces[(y, mode_idx)]] = True
            visibility[(y, mode_idx)] = mask

    default_year = years[0]
    fig.data[traces[(default_year, 0)]].visible = True


    # ======================================================
    # MODE BUTTONS
    # ======================================================
    def make_mode_buttons(year):
        return [
            # IMAGE MODE
            dict(
                label="Image",
                method="update",
                args=[
                    {"visible": visibility[(year, 0)]},
                    {
                        #"title.text": f"Image — {year}",
                        "coloraxis.colorscale": mode_colors["image"],
                        "coloraxis.colorbar.title.text": "Image",
                        "coloraxis.cmin": 0,
                        "coloraxis.cmax": None,
                        # RESET tick labels from Diff mode
                        "coloraxis.colorbar.tickvals": None,
                        "coloraxis.colorbar.ticktext": None
                    }
                ]
            ),

            # AUDIO MODE
            dict(
                label="Audio",
                method="update",
                args=[
                    {"visible": visibility[(year, 1)]},
                    {
                        #"title.text": f"Audio — {year}",
                        "coloraxis.colorscale": mode_colors["audio"],
                        "coloraxis.colorbar.title.text": "Audio",
                        "coloraxis.cmin": 0,
                        "coloraxis.cmax": None,
                        # RESET tick labels from Diff mode
                        "coloraxis.colorbar.tickvals": None,
                        "coloraxis.colorbar.ticktext": None
                    }
                ]
            ),

            # DIFF MODE
            dict(
                label="Diff",
                method="update",
                args=[
                    {"visible": visibility[(year, 2)]},
                    {
                        #"title.text": f"Diff — {year}",
                        "coloraxis.colorscale": mode_colors["diff"],
                        "coloraxis.colorbar.title.text": "Diff",
                        "coloraxis.cmin": -diff_ranges.get(year, 1),
                        "coloraxis.cmax":  diff_ranges.get(year, 1),
                        # descriptive tick labels
                        "coloraxis.colorbar.tickvals": [
                            -diff_ranges.get(year, 1),
                            0,
                            diff_ranges.get(year, 1),
                        ],
                        "coloraxis.colorbar.ticktext": [
                            "More Audio",
                            "Balanced",
                            "More Images",
                        ]
                    }
                ]
            ),
        ]

    # ======================================================
    # YEAR BUTTONS
    # ======================================================
    year_buttons = []
    for y in years:
        year_buttons.append(
            dict(
                label=str(y),
                method="update",
                args=[
                    # Always show IMAGE mode for the selected year
                    {"visible": visibility[(y, 0)]},

                    # Reset mode buttons to this year and reset coloraxis to IMAGE
                    {
                        # If you want a year–mode title again, uncomment:
                        # "title.text": f"Image — {y}",

                        # Swap the mode buttons to be bound to this year
                        "updatemenus[1].buttons": make_mode_buttons(y),
                        "updatemenus[1].active": 0,

                        # Reset the shared coloraxis to IMAGE scale
                        "coloraxis.colorscale": mode_colors["image"],
                        "coloraxis.colorbar.title.text": "Image",
                        "coloraxis.cmin": 0,
                        "coloraxis.cmax": None,
                        "coloraxis.colorbar.tickvals": None,
                        "coloraxis.colorbar.ticktext": None,
                    }
                ],
            )
        )

    # ======================================================
    # SHAPES (GRIDLINES)
    # ======================================================
    shapes = []
    for d in range(32):
        shapes.append(dict(
            type="line",
            xref="x",
            yref="paper",
            x0=str(d + 0.5),
            x1=str(d + 0.5),
            y0=0,
            y1=1,
            line=dict(color="#CCCCCC", width=0.7)
        ))

    for m in range(13):
        shapes.append(dict(
            type="line",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=m - 0.5,
            y1=m - 0.5,
            line=dict(color="#CCCCCC", width=0.7)
        ))


    # ======================================================
    # FINAL LAYOUT
    # ======================================================
    fig.update_layout(
        title=dict(text="Calendar Heatmap", x=0.5, y=0.92),

        width=1600,
        height=900,
        margin=dict(l=40, r=40, t=110, b=40),

        shapes=shapes,

        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.05, y=1.12,
                buttons=year_buttons,
                active=0,  # first year highlighted
            ),
            dict(
                type="buttons",
                direction="right",
                x=0.40, y=1.12,
                buttons=make_mode_buttons(default_year),
                active=0,  # Image highlighted by default
            ),
        ],

        coloraxis=dict(
            colorscale=mode_colors["image"],
            colorbar=dict(title="Image", len=0.8, thickness=20)
        ),

        xaxis=dict(
            showgrid=False, showline=False, zeroline=False,
            ticks="", constrain="domain",
            tickfont=dict(size=13, family="Arial", color="black", weight="bold")
        ),

        yaxis=dict(
            showgrid=False, showline=False, zeroline=False,
            ticks="", autorange="reversed",
            tickfont=dict(size=14, family="Arial", color="black", weight="bold"),
        ),

        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.write_html("../figures/calendar_FINAL.html")
    fig.show()
    print("Saved calendar_FINAL.html")

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    df = pd.read_csv("../results/dataset_summary.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    years = sorted(df["date"].dt.year.unique())
    print("Years:", years)

    plotly_monthday_calendar(df, years)
