"""Plotly figure builders for each chapter."""

import pandas as pd
import plotly.graph_objects as go

from lib.styles import WARM, COOL, BG, BG2, TEXT, MUTED, GRID, FONT_BODY, FONT_MONO, ACCENT

# RUMBA official flight emissions time series (t CO₂eq, Bundesverwaltung Flugreisen).
# Covers all Linienflüge + Bundesratsjets + Bundesratshelikopter.
# Sources: RUMBA Umweltberichte 2021–2025, GS-UVEK (Fachstelle RUMBA).
# Werte wurden mit data/rumba_extraktion.md gegengeprueft.
#
# 2019 baseline derived from 4.2 Umweltbericht 2024:
#   "3300 Tonnen reduziert zwischen 2019 und 2023, was 16 Prozent entspricht"
#   → 16 904 + 3 300 = 20 204 t (rounded to 20 200)
# 2020 = real COVID year (from RUMBA Umweltbericht 2021)
# 2020 "Referenzjahr" used in RUMBA targets = extrapolated value ~19 700 t (not used here)
#
# Target: Aktionsplan Flugreisen → −30 % vs 2019 by 2030
#   = 20 200 × 0.70 = 14 140 t
#
# Status as of 2024: RUMBA reports "auf Kurs" (−25 % vs 2019).
RUMBA_SERIES: dict[int, float] = {
    2019: 20_200,
    2020:  6_719,   # COVID — not meaningful for trend; shown for context
    2021: 10_020,
    2022: 14_409,
    2023: 16_904,
    2024: 15_220,
}
RUMBA_2019_BASELINE_T: float = RUMBA_SERIES[2019]

_PLOTLY_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(family=FONT_BODY, color=TEXT, size=12),
    margin=dict(t=30, b=40, l=60, r=30),
    xaxis=dict(
        showgrid=False,
        linecolor=GRID,
        tickcolor=MUTED,
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
        title=dict(font=dict(family=FONT_MONO, size=11, color=TEXT)),
    ),
    yaxis=dict(
        gridcolor=GRID,
        gridwidth=1,
        linecolor="rgba(0,0,0,0)",
        tickcolor=MUTED,
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
        title=dict(font=dict(family=FONT_MONO, size=11, color=TEXT)),
    ),
    hoverlabel=dict(
        bgcolor=BG2,
        bordercolor=GRID,
        font=dict(family=FONT_BODY, color=TEXT),
    ),
)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _mix_color(cool_hex: str, warm_hex: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(cool_hex)
    r2, g2, b2 = _hex_to_rgb(warm_hex)
    t = max(0.0, min(1.0, t))
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"rgb({r}, {g}, {b})"


def _base_layout(**overrides) -> dict:
    layout = dict(_PLOTLY_LAYOUT)
    layout.update(overrides)
    return layout


# ──────────────────────────────────────────────
# Chapter 2 — Arc map
# ──────────────────────────────────────────────

def arc_map(routes: pd.DataFrame, airports: pd.DataFrame) -> go.Figure:
    """Plotly Scattergeo arc-map: departure → arrival airport.

    Args:
        routes: Output of data.top_routes() with iata_from, iata_to, co2_kg, trips.
        airports: Output of data.load_airports() with iata, lat, lon.

    Returns:
        Plotly Figure with arc traces scaled by CO₂.
    """
    if routes.empty or airports.empty:
        return _empty_fig("Keine Routendaten verfügbar")

    ap = airports.set_index("iata")

    def get_coords(iata: str) -> tuple[float, float] | None:
        if iata in ap.index:
            row = ap.loc[iata]
            return float(row["lat"]), float(row["lon"])
        return None

    co2_max = max(routes["co2_kg"].max(), 1)

    traces: list[go.BaseTraceType] = []
    for _, row in routes.iterrows():
        src = get_coords(row["iata_from"])
        dst = get_coords(row["iata_to"])
        if src is None or dst is None:
            continue

        intensity = row["co2_kg"] / co2_max
        color = _mix_color(COOL, WARM, intensity)
        weight = max(0.4, intensity * 3.5)
        opacity = 0.3 + 0.5 * intensity
        co2_t = row["co2_kg"] / 1000

        traces.append(go.Scattergeo(
            lat=[src[0], dst[0]],
            lon=[src[1], dst[1]],
            mode="lines",
            line=dict(width=weight, color=color),
            opacity=opacity,
            hoverinfo="text",
            text=f"{row['departure_airport']} → {row['final_destination']}<br>"
                 f"{co2_t:.1f} t CO₂ · {row['trips']} Legs",
            showlegend=False,
        ))

    # Destination dots
    dest_iatas = routes["iata_to"].unique()
    dest_ap = airports[airports["iata"].isin(dest_iatas)].copy()
    dest_co2 = routes.groupby("iata_to")["co2_kg"].sum().reset_index()
    dest_ap = dest_ap.merge(dest_co2, on="iata_to", how="left") if "iata_to" in dest_ap.columns else dest_ap
    dest_ap = airports[airports["iata"].isin(dest_iatas)].merge(
        routes.groupby("iata_to")["co2_kg"].sum().rename("co2_kg").reset_index(),
        left_on="iata", right_on="iata_to", how="left",
    )

    dest_ap["color"] = dest_ap["co2_kg"].fillna(0).apply(
        lambda value: _mix_color(COOL, WARM, value / co2_max)
    )

    traces.append(go.Scattergeo(
        lat=dest_ap["lat"],
        lon=dest_ap["lon"],
        mode="markers",
        marker=dict(
            size=(dest_ap["co2_kg"].fillna(0) / co2_max * 10 + 4).clip(upper=14),
            color=dest_ap["color"],
            opacity=0.7,
            line=dict(width=0.5, color=BG),
        ),
        hoverinfo="text",
        text=dest_ap["name"],
        showlegend=False,
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        geo=dict(
            showland=True, landcolor="#ebe0c8",
            showocean=True, oceancolor="#d6cbb5",
            showlakes=False,
            showcountries=True, countrycolor="#a89770",
            showcoastlines=True, coastlinecolor="#a89770",
            coastlinewidth=0.5,
            bgcolor=BG,
            projection_type="natural earth",
            showframe=False,
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        height=480,
    )
    return fig


# ──────────────────────────────────────────────
# Chapter 3 — Emission trend
# ──────────────────────────────────────────────

def trend_chart(
    computed_2024_t: float | None = None,
    forecast_2025_t: float | None = None,
    max_year: int | None = None,
) -> go.Figure:
    """Line + area chart using official RUMBA data with 2030 target line.

    Uses RUMBA_SERIES for 2019–2024 (official figures).
    If computed_2024_t is provided, appends it as an estimate for 2024
    labeled as 'berechnet' to distinguish from official values.
    If forecast_2025_t is provided, appends it as a linear 2025 projection.

    Args:
        computed_2024_t: Optional computed 2024 total (t) from Excel data.
        forecast_2025_t: Optional linear projection for 2025 (t).
        max_year: Optional max year to display for the narrative steps.

    Returns:
        Plotly Figure.
    """
    target_2030 = RUMBA_2019_BASELINE_T * 0.70  # Aktionsplan: −30 % vs 2019

    # Build series — exclude 2020 COVID outlier from main line (show as separate marker)
    series_years = sorted(RUMBA_SERIES)
    if max_year is not None:
        series_years = [year for year in series_years if year <= max_year]
    main_years = [year for year in series_years if year != 2020]
    main_vals = [RUMBA_SERIES[year] for year in main_years]

    fig = go.Figure()

    # Area fill
    fig.add_trace(go.Scatter(
        x=main_years, y=main_vals,
        fill="tozeroy",
        fillcolor="rgba(192,98,42,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        showlegend=False,
    ))

    # Main RUMBA line
    fig.add_trace(go.Scatter(
        x=main_years, y=main_vals,
        mode="lines+markers",
        line=dict(color=WARM, width=2.5),
        marker=dict(size=7, color=WARM, line=dict(width=1.5, color=BG)),
        name="RUMBA offiziell (Linienfluege + BR-Jets/Heli)",
        hovertemplate="%{x}: %{y:,.0f} t CO₂eq (RUMBA)<extra></extra>",
    ))

    # 2020 COVID marker — isolated dot so it doesn't kink the trend line
    if 2020 in series_years:
        fig.add_trace(go.Scatter(
            x=[2020], y=[RUMBA_SERIES[2020]],
            mode="markers",
            marker=dict(size=7, color=MUTED, symbol="circle-open", line=dict(width=2)),
            name="2020 COVID-Ausreisser (nicht im Trend)",
            hovertemplate="2020: %{y:,.0f} t CO₂eq (COVID)<extra></extra>",
        ))

    # Optional 2024 computed estimate
    show_computed = computed_2024_t is not None and (
        max_year is None or max_year >= 2024
    )
    if show_computed:
        fig.add_trace(go.Scatter(
            x=[2024], y=[computed_2024_t],
            mode="markers",
            marker=dict(size=8, color=ACCENT, symbol="diamond",
                        line=dict(width=1.5, color=BG)),
            name="2024 berechnet (Flugdaten, Vergleich)",
            hovertemplate="2024: %{y:,.0f} t CO₂eq (berechnet)<extra></extra>",
        ))

    show_forecast = forecast_2025_t is not None and (
        max_year is None or max_year >= 2025
    )
    if show_forecast:
        fig.add_trace(go.Scatter(
            x=[2024, 2025], y=[RUMBA_SERIES[2024], forecast_2025_t],
            mode="lines",
            line=dict(color=MUTED, width=2, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[2025], y=[forecast_2025_t],
            mode="markers",
            marker=dict(size=8, color=MUTED, symbol="triangle-up-open",
                        line=dict(width=1.5, color=BG)),
            name="Prognose 2025 (linear 2019–2024)",
            hovertemplate="2025: %{y:,.0f} t CO₂eq (Prognose)<extra></extra>",
        ))

    # Target path 2019 → 2030 (−30 %)
    fig.add_trace(go.Scatter(
        x=[2019, 2030], y=[RUMBA_2019_BASELINE_T, target_2030],
        mode="lines+markers",
        line=dict(color=COOL, width=2, dash="dash"),
        marker=dict(size=6, color=COOL),
        name=f"Zielpfad 2030 (−30% vs 2019)",
        hovertemplate="%{x}: %{y:,.0f} t CO₂eq (Ziel)<extra></extra>",
    ))

    # 2019 baseline annotation
    fig.add_annotation(
        x=2019, y=RUMBA_2019_BASELINE_T,
        text=f"Basisjahr 2019<br>{RUMBA_2019_BASELINE_T:,.0f} t",
        showarrow=True, arrowhead=0, arrowcolor=MUTED,
        ax=0, ay=-48,
        font=dict(family=FONT_MONO, size=10, color=MUTED),
        bgcolor=BG, borderpad=3,
    )

    # 2023 status annotation
    if max_year is None or max_year >= 2024:
        fig.add_annotation(
            x=2024, y=RUMBA_SERIES[2024],
            text="«auf Kurs»<br>(RUMBA 2025)",
            showarrow=True, arrowhead=0, arrowcolor=COOL,
            ax=40, ay=-40,
            font=dict(family=FONT_MONO, size=10, color=COOL),
            bgcolor=BG, borderpad=3,
        )

    fig.update_layout(
        **_base_layout(
            height=420,
            title=dict(
                text="Trend Flugemissionen der Bundesverwaltung",
                x=0.0,
                xanchor="left",
                font=dict(family=FONT_BODY, size=14, color=TEXT),
            ),
            yaxis_title="Tonnen CO₂eq",
            xaxis=dict(
                tickvals=list(range(2019, 2031)),
                tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
                range=[2018.5, 2030.5],
                showgrid=False,
            ),
            legend=dict(
                orientation="v",
                x=1.02,
                xanchor="left",
                y=1.0,
                yanchor="top",
                font=dict(family=FONT_MONO, size=10, color=TEXT),
                title=dict(font=dict(family=FONT_MONO, size=10, color=TEXT)),
            ),
            legend_title_text="Datenreihen",
            margin=dict(t=60, b=40, l=60, r=200),
        )
    )
    fig.update_yaxes(
        title_font=dict(family=FONT_MONO, size=11, color=TEXT),
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
    )
    return fig


# ──────────────────────────────────────────────
# Chapter 4 — Comparison dot-plot
# ──────────────────────────────────────────────

# UK data from Greening Government Commitments annual report.
# Note: methodologies differ between countries — this is an order-of-magnitude comparison only.
_COMPARISON_DATA = [
    {"name": "Schweizer Bundesverwaltung",        "value_t": None,   "type": "self",
     "note": "Berechnet aus Flugdaten 2020–2024"},
    {"name": "UK Central Government",             "value_t": 48_000, "type": "gov",
     "note": "Greening Gov. Commitments, ca. 2022–23"},
]


def comparison_chart(ch_total_t: float) -> go.Figure:
    """Dot-plot comparing CH Bundesverwaltung emissions to UK Central Government.

    Args:
        ch_total_t: Total Swiss federal flight emissions in tonnes (most recent year).

    Returns:
        Plotly Figure with dumbbell-style dot-plot.
    """
    data = []
    for row in _COMPARISON_DATA:
        val = ch_total_t if row["type"] == "self" else row["value_t"]
        data.append({"name": row["name"], "value_t": val, "type": row["type"], "note": row["note"]})

    df = pd.DataFrame(data).sort_values("value_t")

    fig = go.Figure()

    colors = {
        "self": WARM,
        "gov": COOL,
    }

    for _, row in df.iterrows():
        color = colors.get(row["type"], MUTED)
        size = 16 if row["type"] == "self" else 12
        fig.add_trace(go.Scatter(
            x=[row["value_t"]],
            y=[row["name"]],
            mode="markers+text",
            marker=dict(size=size, color=color, line=dict(width=1.5, color=BG)),
            text=[f"  {row['value_t']:,.0f} t"],
            textposition="middle right",
            textfont=dict(family=FONT_MONO, size=11, color=TEXT),
            hovertemplate=f"{row['name']}<br>{row['value_t']:,.0f} t CO₂eq<br>{row['note']}<extra></extra>",
            showlegend=False,
        ))
        fig.add_shape(
            type="line", x0=0, x1=row["value_t"],
            y0=row["name"], y1=row["name"],
            line=dict(color=color if row["type"] == "self" else GRID, width=2 if row["type"] == "self" else 1),
        )

    fig.update_layout(
        **_base_layout(
            height=200,
            xaxis_title="Tonnen CO₂eq pro Jahr",
            xaxis=dict(
                range=[0, df["value_t"].max() * 1.25],
                showgrid=True, gridcolor=GRID,
                tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
                title=dict(font=dict(family=FONT_MONO, size=11, color=TEXT)),
            ),
            yaxis=dict(showgrid=False, tickfont=dict(family=FONT_BODY, size=13, color=TEXT)),
            margin=dict(t=20, b=60, l=240, r=120),
        )
    )
    fig.update_yaxes(
        title_font=dict(family=FONT_MONO, size=11, color=TEXT),
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
    )
    fig.update_xaxes(
        title_font=dict(family=FONT_MONO, size=11, color=TEXT),
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
    )
    return fig

# ──────────────────────────────────────────────
# Chapter 4 revised — Indexierter Vergleich (CH vs. UK)
# ──────────────────────────────────────────────

def indexed_comparison_chart() -> go.Figure:
    """Liniendiagramm zum Vergleich von CH und UK bezüglich ihrer Reduktionsziele.
    
    Da absolute Zahlen nicht vergleichbar sind, zeigen wir die relative Entwicklung
    und die gesetzten Ziele ab dem jeweiligen Basisjahr (Index = 100%).
    CH Basisjahr: 2019
    UK Basisjahr: 2017/18
    """
    fig = go.Figure()

    # Daten Schweiz (RUMBA)
    # Basisjahr 2019 = 20'200 t = 100%
    # Ziel 2030 = -30% = 70% (11 Jahre nach Basisjahr)
    ch_years_since_base = [0, 2, 3, 4, 5] # 2019, 2021, 2022, 2023, 2024 (ohne 2020 COVID)
    ch_vals = [20200, 10020, 14409, 16904, 15220]
    ch_index = [v / 20200 * 100 for v in ch_vals]
    
    # Reale RUMBA Werte
    fig.add_trace(go.Scatter(
        x=ch_years_since_base,
        y=ch_index,
        mode="lines+markers",
        line=dict(color=WARM, width=2.5),
        marker=dict(size=8, color=WARM, line=dict(width=1.5, color=BG)),
        name="CH Bundesverwaltung<br>(Reale CO₂-Emissionen)",
        hovertemplate="CH Jahr %{x} (seit 2019): %{y:.1f}%<extra></extra>"
    ))

    # Ziel Schweiz
    fig.add_trace(go.Scatter(
        x=[0, 11], # 2019 bis 2030
        y=[100, 70],
        mode="lines+markers",
        line=dict(color=WARM, width=2, dash="dash"),
        marker=dict(size=6, color=WARM, symbol="diamond"),
        name="CH Zielpfad 2030<br>(-30% CO₂)",
        hoverinfo="skip"
    ))

    # Daten UK (Greening Government Commitments)
    # Basisjahr 2017/18 = 100%
    # Ziel 2025 = -30% = 70% (7 Jahre nach Basisjahr)
    # Da wir keine sauberen UK-Rohdaten pro Jahr haben, zeichnen wir den harten Zielpfad.
    fig.add_trace(go.Scatter(
        x=[0, 7], 
        y=[100, 70],
        mode="lines+markers",
        line=dict(color=COOL, width=2.5, dash="dot"),
        marker=dict(size=8, color=COOL, symbol="square", line=dict(width=1.5, color=BG)),
        name="UK Government Ziel 2025<br>(-30% geflogene Distanz)",
        hovertemplate="UK Ziel Jahr %{x} (seit 2017): %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        **_base_layout(
            height=380,
            title=dict(
                text="Relative Reduktionsziele: CH vs. UK (Basisjahr = 100%)",
                x=0.0,
                xanchor="left",
                font=dict(family=FONT_BODY, size=14, color=TEXT),
            ),
            xaxis_title="Jahre seit dem jeweiligen Basisjahr",
            yaxis_title="Zielerreichung in %",
            xaxis=dict(
                showgrid=False,
                tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
                tickvals=list(range(0, 12)),
            ),
            yaxis=dict(
                range=[40, 110],
                showgrid=True,
                gridcolor=GRID,
                tickvals=[40, 50, 60, 70, 80, 90, 100],
                ticktext=["40%", "50%", "60%", "70% (Ziel)", "80%", "90%", "100% (Basisjahr)"]
            ),
            legend=dict(
                orientation="v",
                x=1.02,
                xanchor="left",
                y=1.0,
                yanchor="top",
                font=dict(family=FONT_MONO, size=10, color=TEXT),
            ),
            margin=dict(t=50, b=40, l=60, r=200),
        )
    )
    
    # Horizontale Orientierungslinie für 100%
    fig.add_shape(
        type="line", x0=0, x1=11, y0=100, y1=100,
        line=dict(color=MUTED, width=1),
        layer="below"
    )
    fig.update_yaxes(
        title_font=dict(family=FONT_MONO, size=11, color=TEXT),
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
    )
    fig.update_xaxes(
        title_font=dict(family=FONT_MONO, size=11, color=TEXT),
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
    )
    return fig

# ──────────────────────────────────────────────
# Chapter 5 — Per-capita bar
# ──────────────────────────────────────────────

# BAFU reference: average Swiss resident flight CO₂ per capita.
# Source: BAFU Treibhausgasinventar / Umweltbericht 2024.
BAFU_SWISS_AVG_T = 1.4  # t CO₂eq per person per year from aviation


def per_capita_chart(
    bk_per_person_t: float,
    user_t: float | None = None,
) -> go.Figure:
    """Horizontal bar comparing one BK person vs. Swiss average.

    Optionally adds a third bar for the reader's personal estimate so the
    interactive Chapter-5 calculators can show «Du» alongside the BAFU and
    BK references.

    Args:
        bk_per_person_t: Estimated per-person CO₂ from BK flight data (tonnes).
        user_t: Optional user-supplied personal estimate (tonnes). When None
            the chart shows the original two-bar layout.

    Returns:
        Plotly Figure.
    """
    if user_t is None:
        categories = ["Ø Schweizer:in\n(BAFU)", "Ø Person Bundesverwaltung\n(berechnet)"]
        values = [BAFU_SWISS_AVG_T, bk_per_person_t]
        colors_list = [COOL, WARM]
        widths = [0.5, 0.5]
        height = 200
        left_margin = 200
    else:
        categories = [
            "Ø Schweizer:in\n(BAFU)",
            "Ø Person Bundesverwaltung\n(berechnet)",
            "Du\n(geschätzt)",
        ]
        values = [BAFU_SWISS_AVG_T, bk_per_person_t, user_t]
        colors_list = [COOL, MUTED, WARM]
        widths = [0.5, 0.5, 0.65]
        height = 260
        left_margin = 200

    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation="h",
        marker_color=colors_list,
        text=[f"{v:.1f} t" for v in values],
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=12, color=TEXT),
        hovertemplate="%{y}: %{x:.2f} t CO₂eq<extra></extra>",
        width=widths,
    ))

    x_max = max([v for v in values if v is not None] + [0.1]) * 1.3

    fig.update_layout(
        **_base_layout(
            height=height,
            xaxis_title="Tonnen CO₂eq / Jahr",
            xaxis=dict(range=[0, x_max], showgrid=True, gridcolor=GRID),
            yaxis=dict(showgrid=False),
            margin=dict(t=20, b=50, l=left_margin, r=80),
        )
    )
    fig.update_yaxes(
        title_font=dict(family=FONT_MONO, size=11, color=TEXT),
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
    )
    fig.update_xaxes(
        title_font=dict(family=FONT_MONO, size=11, color=TEXT),
        tickfont=dict(family=FONT_MONO, size=11, color=TEXT),
    )
    return fig


def _empty_fig(msg: str = "Keine Daten") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        x=0.5, y=0.5, xref="paper", yref="paper",
        text=msg, showarrow=False,
        font=dict(family=FONT_BODY, size=14, color=MUTED),
    )
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, margin=dict(t=20, b=20, l=20, r=20), height=200)
    return fig
