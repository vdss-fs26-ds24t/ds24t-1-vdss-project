"""Bundesrat Flugemissionen — scrollable Streamlit data story."""

import logging
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from lib import charts, styles
from lib.data import (
    add_destination_country,
    avg_leg_metrics,
    co2_for_distance,
    filter_flights,
    globe_routes,
    load_airports,
    load_flights,
    route_distance_km,
    top_routes,
    yearly_totals,
)
from lib.globe import render_globe

logging.basicConfig(level=logging.INFO)


@dataclass(frozen=True)
class RumbaReportInfo:
    """Metadata for a RUMBA report and its data year."""

    report_year: int
    data_year: int
    publisher: str
    publisher_short: str
    source: str


st.set_page_config(
    page_title="Bundesrat Flugemissionen",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

styles.inject()


# ── Data ────────────────────────────────────────────────────────────────────

flights = load_flights()
airports = load_airports()
flights = add_destination_country(flights, airports)

if flights.empty:
    st.error("Flugdaten konnten nicht geladen werden. Bitte prüfe den Pfad ../data/.")
    st.stop()

ytotals = yearly_totals(flights)
all_years = sorted(flights["source_year"].unique().tolist())
all_depts = ["Alle"] + sorted(flights["department"].dropna().unique().tolist())
all_countries = ["Alle"] + sorted(flights["dest_country"].dropna().unique().tolist())
latest_year = max(all_years)
latest_total_t = ytotals[ytotals["year"] == latest_year]["co2_t"].values[0]

RUMBA_REPORTS: list[RumbaReportInfo] = [
    RumbaReportInfo(
        report_year=2021,
        data_year=2020,
        publisher="Bundesamt für Energie (BFE)",
        publisher_short="BFE",
        source="RUMBA 2021, Kap. 1.1",
    ),
    RumbaReportInfo(
        report_year=2022,
        data_year=2021,
        publisher="Bundesamt für Energie (BFE)",
        publisher_short="BFE",
        source="RUMBA 2022, Kap. 1.2",
    ),
    RumbaReportInfo(
        report_year=2023,
        data_year=2022,
        publisher="GS-UVEK",
        publisher_short="GS-UVEK",
        source="RUMBA 2023, Kap. 1.2",
    ),
    RumbaReportInfo(
        report_year=2024,
        data_year=2023,
        publisher="GS-UVEK",
        publisher_short="GS-UVEK",
        source="RUMBA 2024, Kap. 1.1",
    ),
    RumbaReportInfo(
        report_year=2025,
        data_year=2024,
        publisher="GS-UVEK",
        publisher_short="GS-UVEK",
        source="RUMBA 2025, Kap. 1",
    ),
]

RUMBA_KEY_FIGURES = {
    2020: {
        "source": "RUMBA Umweltbericht 2021 (Datenjahr 2020, Kennzahlen-Seite, Kap. 2)",
        "total_thg_t": 18_604,
        "flight_thg_t": 6_719,
        "flight_share_pct": 36,
        "ubp_fte_mio": 1.3,
        "fte": 17_200,
        "reduction_since_2006_pct": -61,
    },
    2021: {
        "source": "RUMBA Umweltbericht 2022 (Datenjahr 2021, Kennzahlen-Seite, Kap. 2)",
        "total_thg_t": 22_221,
        "flight_thg_t": 10_020,
        "flight_share_pct": 45,
        "ubp_fte_mio": 1.4,
        "fte": 17_702,
        "reduction_since_2006_pct": -53,
    },
    2022: {
        "source": "RUMBA Umweltbericht 2023 (Datenjahr 2022, Kennzahlen-Seite, Kap. 2)",
        "total_thg_t": 25_479,
        "flight_thg_t": 14_409,
        "flight_share_pct": 57,
        "ubp_fte_mio": 1.5,
        "fte": 17_570,
        "reduction_since_2006_pct": -46,
    },
    2023: {
        "source": "RUMBA Umweltbericht 2024 (Datenjahr 2023, Kennzahlen-Seite, Kap. 2)",
        "total_thg_t": 27_612,
        "flight_thg_t": 16_904,
        "flight_share_pct": 61,
        "ubp_fte_mio": 1.5,
        "fte": 17_838,
        "reduction_since_2006_pct": -42,
    },
    2024: {
        "source": "RUMBA Umweltbericht 2025 (Datenjahr 2024, Kennzahlen-Seite, Kap. 2)",
        "total_thg_t": 24_929,
        "flight_thg_t": 15_220,
        "flight_share_pct": 61,
        "ubp_fte_mio": 1.8,
        "fte": 18_425,
        "reduction_since_2006_pct": -48,
    },
}


# ── Hero ─────────────────────────────────────────────────────────────────────
hero_left, hero_right = st.columns([1.2, 1])
with hero_left:
        styles.html("""
<div style="padding:80px 0 20px">
    <div class="eyebrow">Daten-Story · Frühlingssemester 2026 · ZHAW</div>
    <h1 class="hero-title">Wie viel CO₂ verursacht die Schweizer Regierung auf Reisen?</h1>
    <p class="hero-subtitle">
        Ein datengestützter Blick auf die Flugemissionen der Bundesverwaltung,
        2020–2024 — und die Frage: Ist die Schweiz auf Kurs?
    </p>
</div>
""")
        styles.html('<div class="filter-label">Jahr</div>')
        hero_col_left, hero_col_right = st.columns([3, 1])
        with hero_col_left:
            hero_year = st.radio(
                "Jahr",
                options=all_years,
                index=all_years.index(latest_year),
                horizontal=True,
                label_visibility="collapsed",
                key="hero_year",
            )
        hero_total_row = ytotals[ytotals["year"] == hero_year]
        hero_total_t = float(hero_total_row["co2_t"].iloc[0]) if not hero_total_row.empty else 0.0
        hero_rumba = RUMBA_KEY_FIGURES.get(hero_year)
        hero_rumba_t = hero_rumba["flight_thg_t"] if hero_rumba else None
        hero_diff_tooltip = (
            "Berechnet aus den bk.admin.ch-Fluglisten mit myClimate-Faktoren "
            "(0.255 / 0.185 / 0.147 kg CO₂eq/km, Business ×2.0). "
            "Die RUMBA-Zahl umfasst zusätzlich Bundesratsjets und Helikopter, "
            "nutzt andere Emissionsfaktoren (inkl. Vorkette/RFI) und basiert auf "
            "Buchhaltungsdaten der Reisestelle — daher die Diskrepanz."
        )
        if hero_rumba_t is not None:
            diff_pct = (hero_total_t - hero_rumba_t) / hero_rumba_t * 100
            rumba_block = f"""
<div style="margin-top:20px; display:flex; align-items:baseline; gap:14px;"
     title="{hero_diff_tooltip}">
    <div style="font-family:var(--head); font-size:22px; font-weight:600;
                color:var(--muted); letter-spacing:-0.01em;">
        {hero_rumba_t:,.0f} t
    </div>
    <div style="font-family:var(--mono); font-size:11px; letter-spacing:0.08em;
                text-transform:uppercase; color:var(--muted);
                border-bottom:1px dotted var(--muted); cursor:help;">
        Offiziell laut RUMBA · Δ {diff_pct:+.0f}%
    </div>
</div>"""
        else:
            rumba_block = ""
        styles.html(f"""
<div style="margin-top:32px">
    <div class="hero-number">{hero_total_t:,.0f} t</div>
    <div class="hero-number-label">CO₂eq aus Dienstflügen · {hero_year} · berechnet</div>
    {rumba_block}
</div>
<div style="margin-top:40px; display:flex; align-items:center; gap:12px;
                        font-family:var(--mono); font-size:11px; letter-spacing:0.1em;
                        text-transform:uppercase; color:var(--muted)">
    <div style="width:24px; height:1px; background:var(--muted)"></div>
    Scrollen, um zu erkunden
</div>
""")
with hero_right:
        styles.html("<div style='height:80px'></div>")
        hero_globe_data = globe_routes(flights, airports, year=hero_year, department=None, top_n=140)
        if hero_globe_data:
                render_globe(hero_globe_data, height=520)
        else:
                hero_routes = top_routes(flights, year=hero_year, department=None, top_n=60)
                st.plotly_chart(
                        charts.arc_map(hero_routes, airports),
                        use_container_width=True,
                        config={"displayModeBar": False},
                )

st.divider()


# ── Chapter 0 — Grundlagen ─────────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 0",
    title="Grundlagen zu den RUMBA-Umweltberichten",
    lead=(
        "RUMBA misst die Umweltwirkungen der Bundesverwaltung — von Dienstreisen "
        "über Gebäude bis Papier. Das Kapitel erklärt Begriffe, Systemgrenzen "
        "und die wichtigsten Programme, die die Zahlen prägen."
    ),
)
o1, o2, o3 = st.columns(3)
with o1:
        styles.html("""
<div class="kpi-tile" title="RUMBA umfasst Dienstreisen, Gebäude und Papier.">
  <div class="kpi-bar-warm"></div>
  <div class="kpi-value">🌍</div>
  <div class="kpi-label">RUMBA Umfang</div>
  <div style="margin-top:12px; font-family:var(--body); font-size:14px; color:var(--muted);">
        Dienstreisen, Gebäudeenergie, Wasser/Abfall und Papier fliessen in ein gemeinsames Bild.
  </div>
</div>
""")
with o2:
    styles.html("""
<div class="kpi-tile" title="VBS ist nicht Teil von RUMBA (eigenes System RUMS-VBS).">
  <div class="kpi-bar-accent"></div>
  <div class="kpi-value">🏛️</div>
  <div class="kpi-label">Organisation</div>
  <div style="margin-top:12px; font-family:var(--body); font-size:14px; color:var(--muted);">
        Sechs Departemente, Bundeskanzlei und Parlamentsdienste; das VBS läuft separat in RUMS-VBS.
  </div>
</div>
""")
with o3:
    styles.html("""
<div class="kpi-tile" title="Ab Bericht 2025 kommen Kältemittel und Satellit-Themen hinzu.">
  <div class="kpi-bar-cool"></div>
  <div class="kpi-value">🧪</div>
  <div class="kpi-label">Neue Themen</div>
  <div style="margin-top:12px; font-family:var(--body); font-size:14px; color:var(--muted);">
        Ab 2025: Kältemittel und Satellit-Themen wie IT, Verpflegung oder Pendeln.
  </div>
</div>
""")

styles.html(
    '<div class="method-note">'
    'Quellen: RUMBA 2021, Kap. 1.1; RUMBA 2025, Kap. 1.'
    '</div>'
)

styles.html("""
<div class="callout">
    <div class="callout-title">Grundlage zur Frage: Ist die Schweiz auf Kurs?</div>
    <div class="callout-text">
        Die Klimastrategie der Schweizer Bundesverwaltung basiert massgeblich auf dem im Juli 2019 verabschiedeten „Klimapaket Bundesverwaltung“ sowie dem ergänzenden „Aktionsplan Flugreisen“ vom Dezember 2019. Das übergeordnete Ziel des Klimapakets ist eine Reduktion der Treibhausgasemissionen (THG) im Inland um 50 % bis 2030 gegenüber dem Basisjahr 2006. Speziell für den Mobilitätsbereich, der laut aktuellem Umweltbericht mit 61 % den grössten Emissions-Hotspot darstellt, sieht der Aktionsplan Flugreisen eine Senkung der flugbedingten THG-Emissionen um 30 % bis 2030 im Vergleich zum Referenzjahr 2019 vor.

Zur praktischen Umsetzung wurden im Rahmen des Programms „RUMBA 2020+“ verbindliche Massnahmen definiert, wie die Verpflichtung zur Bahnnutzung bei Reisezeiten unter sechs Stunden oder der Verzicht auf die Business-Klasse bei Flügen unter neun Stunden. Die Bilanz der letzten Jahre zeigt eine positive Entwicklung: Bis zum Berichtsjahr 2024 konnten die gesamten THG-Emissionen seit 2020 bereits um 23 % gesenkt werden. Im Bereich der Flugreisen wurde bereits eine Reduktion von 25 % gegenüber 2019 erreicht, womit die Bundesverwaltung aktuell auf Kurs ist, ihre für 2030 gesteckten Ziele zu erreichen.
        <div class="method-note">
            Quellen: RUMBA 2021, Management Summary; RUMBA 2024, Kap. 2/3;
            RUMBA 2025, Kap. 2/3.2.
        </div>
    </div>
</div>
""")

styles.html('<div class="filter-label">RUMBA-Bericht auswählen</div>')
# report_labels = [
#     f"{info.report_year} (Datenjahr {info.data_year})" for info in RUMBA_REPORTS
# ]
rumba_years_cht1 = sorted(RUMBA_KEY_FIGURES)
default_rumba_index = (
    rumba_years_cht1.index(latest_year)
    if latest_year in rumba_years_cht1
    else len(rumba_years_cht1) - 1
)
report_by_label = {label: info for label, info in zip(rumba_years_cht1, RUMBA_REPORTS)}

rumba_col_left, rumba_col_right = st.columns([3, 1])
with rumba_col_left:
    rumba_year_cht1 = st.radio(
        "Datenjahr (RUMBA)",
        options=rumba_years_cht1,
        index=default_rumba_index,
        horizontal=True,
        label_visibility="collapsed",
        key="ch0_rumba_year",
    )
# report_col_left, report_col_right = st.columns([4, 1])
# with report_col_left:
#     # constrain the radio group's width similar to the hero control
#     selected_report_label = st.radio(
#         "RUMBA-Bericht auswählen",
#         options=report_labels,
#         index=len(report_labels) - 1,
#         horizontal=True,
#         label_visibility="collapsed",
#         key="ch0_report",
#     )
# selected_report_label = st.radio(
#     "RUMBA-Bericht auswählen",
#     options=report_labels,
#     index=len(report_labels) - 1,
#     horizontal=True,
#     label_visibility="visible",
#     key="ch0_report",
# )
selected_report = report_by_label[rumba_year_cht1]

rc1, rc2, rc3 = st.columns(3)
with rc1:
    styles.kpi_tile(
        value=str(selected_report.report_year),
        label="Berichtsjahr",
        bar="warm",
    )
with rc2:
    styles.kpi_tile(
        value=str(selected_report.data_year),
        label="Datenjahr",
        bar="accent",
    )
with rc3:
    styles.kpi_tile(
        value=selected_report.publisher_short,
        label="Herausgeber",
        bar="cool",
    )

styles.html(
    f'<div class="method-note">'
    f'Quellen: {selected_report.source}; RUMBA 2021, Kap. 1.1; RUMBA 2023, Kap. 1.2. '
    'Hinweis: Herausgeberwechsel BFE (Berichte 2021–2022) → GS-UVEK (ab Bericht 2023).'
    '</div>'
)

tab_overview, tab_scope, tab_programs, tab_methods, tab_ubp = st.tabs(
    [
        "Überblick",
        "Systemgrenzen",
        "Programme",
        "Methodik",
        "UBP erklärt",
    ]
)

with tab_overview:
        st.markdown(
                """
Bevor wir die Zahlen vergleichen, lohnt sich ein kurzer Rahmen: RUMBA bündelt
die wichtigsten Umweltwirkungen der Bundesverwaltung in einem einheitlichen System.
"""
        )

with tab_scope:
    st.markdown(
        """
Die Systemgrenze ist entscheidend: RUMBA umfasst die Bundesverwaltung
**ohne VBS**. Seit 2020 werden VBS-Einheiten nur noch im System
**RUMS-VBS** ausgewiesen, damit es keine Doppelzählungen gibt.
"""
    )
    styles.html(
        '<div class="method-note">Quelle: RUMBA 2021, Kap. 1.1.</div>'
    )

with tab_programs:
    st.markdown(
        """
Zwei Programme geben die Richtung vor: das Klimapaket für die Gesamtverwaltung
und der Aktionsplan für Flugreisen. Beide liefern den Referenzrahmen für die Frage,
ob die Schweiz «auf Kurs» ist.
"""
    )
with st.expander("Klimapaket Bundesverwaltung (Beschluss 2019)", expanded=True):
    st.markdown(
            """
Das Klimapaket definiert den Gesamtpfad der Bundesverwaltung:

- **Ziel:** −50 % THG-Emissionen bis 2030 vs. 2006 (ohne VBS).
- **Kompensation:** bis 2021 über Zertifikate, ab 2022 über internationale Bescheinigungen.
- **VBS:** eigenes Ziel im System RUMS-VBS (−40 % vs. 2001).
"""
        )
    styles.html(
            '<div class="method-note">Quelle: RUMBA 2021, Kap. 1.3; '
            'RUMBA 2025, Kap. 3.1.</div>'
        )

with st.expander("Aktionsplan Flugreisen (Dezember 2019)", expanded=False):
        st.markdown(
            """
Der Aktionsplan fokussiert spezifisch auf Flugreisen:

- **Ziel:** −30 % THG aus Flugreisen bis 2030 vs. 2019.
- **Hebel:** Economy statt Business, Zug statt Flug, Video-/Telefonkonferenzen,
  kleinere Delegationen.
"""
        )
        styles.html(
            '<div class="method-note">Quelle: RUMBA 2021, Kap. 1.3.1 & 3.2; '
            'RUMBA 2025, Kap. 3.2.</div>'
        )

with tab_methods:
    st.markdown(
        """
Für die Einordnung der Trends sind zwei Punkte wichtig. Erstens war 2020
ein pandemiebedingtes **Ausnahmejahr**. Für die Zielberechnung wurde daher
ein **extrapoliertes Referenzjahr 2020** eingeführt (Bundesratsbeschluss
vom 11. Dezember 2020); dieses Referenzjahr ist nicht identisch mit den realen
2020er-Werten.
"""
    )
    st.markdown(
        """
Zweitens gab es methodische Anpassungen, die die Vergleichbarkeit einschränken:

- 2017: Anpassungen (Details nicht spezifiziert).
- 2020: erneuerbarer Strommix, Erfassung Bundesratsjets/Helikopter, externer Druck.
- Ab Bericht 2022: aktualisierte KBOB-Faktoren für Wärme.
"""
    )
    styles.html(
        '<div class="method-note">'
        'Quellen: RUMBA 2022, Fussnote 7 zu Kap. 2.1; RUMBA 2021, Kap. 3.1; '
        'RUMBA 2022, Fussnote 8 zu Kap. 2.3.2.</div>'
    )

# with tab_ontrack:
#     st.markdown(
#         """
# **Warum die Frage «auf Kurs?»** RUMBA arbeitet mit Zielperioden und Referenzjahren.
# Die Bundesverwaltung (ohne VBS) steuert zwei Pfade:

# - **Klimapaket:** −50 % THG bis 2030 vs. 2006; verbleibende Emissionen werden kompensiert.
# - **Aktionsplan Flugreisen:** −30 % Flug-THG bis 2030 vs. 2019.

# Zusätzlich bewertet RUMBA Zielperioden gegenüber dem **extrapolierten Referenzjahr 2020**:

# - **Zielperiode 2020–2023:** −9 % THG und −8 % UBP/FTE; 2023 erreicht (−14 % THG, −17 % UBP/FTE).
# - **Zielperiode 2024–2027:** −24 % THG und −21 % UBP/FTE; 2024 bei −23 % THG und −25 % UBP/FTE.

# Für Flugreisen zeigt RUMBA: **−16 % (2023)** bzw. **−25 % (2024)** gegenüber 2019.
# """
#     )
#     styles.html(
#         '<div class="method-note">'
#         'Quellen: RUMBA 2021, Management Summary; RUMBA 2024, Kap. 2/3; '
#         'RUMBA 2025, Kap. 2/3.2.</div>'
#     )

with tab_ubp:
    st.markdown(
        """
**UBP (Umweltbelastungspunkte)** basieren auf der Methode der ökologischen
Knappheit. Sie berücksichtigen Emissionen in Boden, Wasser und Luft sowie
Ressourcenerschöpfung. Dadurch kann z.B. **Papier** in der UBP-Perspektive
stärker ins Gewicht fallen als bei THG.
"""
    )
    styles.html(
        '<div class="method-note">Quellen: RUMBA 2021, Fussnote 1; '
        'RUMBA 2024, Kap. 2.2.</div>'
    )

st.divider()


# ── Chapter 1 — KPIs ────────────────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 1",
    title="Der Bundesratsjet im Kontext",
    lead=(
        "Flugreisen stellen mit 36–61 Prozent den grössten Hotspot der Treibhausgasemissionen "
        "der Bundesverwaltung dar (RUMBA-Umweltberichte 2021–2025). "
        "Die Key Figures stammen aus den offiziellen RUMBA-Kennzahlen pro Datenjahr."
    ),
)

styles.html('<div class="filter-label">Datenjahr (RUMBA)</div>')
rumba_years = sorted(RUMBA_KEY_FIGURES)
default_rumba_index = (
    rumba_years.index(latest_year)
    if latest_year in rumba_years
    else len(rumba_years) - 1
)
rumba_col_left, rumba_col_right = st.columns([3, 1])
with rumba_col_left:
    rumba_year = st.radio(
        "Datenjahr (RUMBA)",
        options=rumba_years,
        index=default_rumba_index,
        horizontal=True,
        label_visibility="collapsed",
        key="ch1_rumba_year",
    )
rumba = RUMBA_KEY_FIGURES[rumba_year]
rumba_note = (
    f'Quelle: {rumba["source"]}. '
    'Hinweis: 2020 ist ein Pandemie-Ausreisser; ab 2020 wurden zudem Bundesratsjets/'
    'Helikopter und externe Druckaufträge vollumfänglich erfasst. '
    'Diskrepanzen in den Berichten: Business-Klasse-Anteil 2019 '
    '(RUMBA 2024: 56 %, RUMBA 2025: 40 %); Bundesratsjets-Trend '
    '2019–2023 +39 % (RUMBA 2024) vs. 2019–2024 −2 % (RUMBA 2025); '
    'Reduktion Flugemissionen vs. 2019: −16 % (RUMBA 2024) vs. −25 % '
    '(RUMBA 2025); methodische Anpassungen 2017/2020 schränken die '
    'Vergleichbarkeit ein.'
)
if rumba_year == 2020:
    rumba_note += " FTE 2020 ca. 17'200."

k1, k2, k3 = st.columns(3)
with k1:
    styles.kpi_tile(
        value=f"{rumba['total_thg_t']:,.0f} t",
        label=f"THG gesamt · {rumba_year}",
        bar="warm",
    )
with k2:
    styles.kpi_tile(
        value=f"{rumba['flight_thg_t']:,.0f} t",
        label="THG Flugreisen",
        bar="accent",
    )
with k3:
    styles.kpi_tile(
        value=f"{rumba['flight_share_pct']} %",
        label="Anteil Flugreisen an THG",
        bar="cool",
    )

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

k4, k5, k6 = st.columns(3)
with k4:
    styles.kpi_tile(
        value=f"{rumba['reduction_since_2006_pct']:.0f} %",
        label="Reduktion seit 2006",
        bar="warm",
    )
with k5:
    styles.kpi_tile(
        value=f"{rumba['ubp_fte_mio']:.1f} Mio.",
        label="UBP pro FTE",
        bar="accent",
    )
with k6:
    styles.kpi_tile(
        value=f"{rumba['fte']:,}",
        label="Vollzeitstellen (FTE)",
        bar="cool",
    )

styles.html(f'<div class="method-note">{rumba_note}</div>')

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.divider()


# ── Chapter 2 — Who flies where ─────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 2",
    title="Wer fliegt wohin?",
    lead=(
        "Zwischen 2020 und 2024 flogen Mitarbeitende der Bundesverwaltung zu Treffen, "
        "Konferenzen und Staatsbesuchen rund um die Welt. "
        "Die Karte zeigt die häufigsten Routen mit Start- und Zielorten weltweit."
    ),
)

# Filters
fc1, fc2, fc3, _ = st.columns([1, 1, 1, 2])
with fc1:
    styles.html('<div class="filter-label">Jahr</div>')
    sel_year_raw = st.selectbox(
        "Jahr", options=["Alle"] + [str(y) for y in all_years],
        label_visibility="collapsed", key="ch2_year",
    )
    sel_year: int | None = None if sel_year_raw == "Alle" else int(sel_year_raw)
with fc2:
    styles.html('<div class="filter-label">Departement</div>')
    sel_dept = st.selectbox(
        "Departement", options=all_depts,
        label_visibility="collapsed", key="ch2_dept",
    )
with fc3:
    styles.html('<div class="filter-label">Zielland</div>')
    sel_country = st.selectbox(
        "Zielland", options=all_countries,
        label_visibility="collapsed", key="ch2_country",
    )

routes = top_routes(
    flights,
    year=sel_year,
    department=sel_dept,
    dest_country=sel_country,
    top_n=60,
)
globe_data = globe_routes(
    flights,
    airports,
    year=sel_year,
    department=sel_dept,
    dest_country=sel_country,
    top_n=120,
)

filtered = filter_flights(
    flights,
    year=sel_year,
    department=sel_dept,
    dest_country=sel_country,
)
n_filtered = len(filtered)
co2_filtered_t = filtered["co2_kg"].sum() / 1000


styles.html(
    f'<div class="method-note" style="margin-bottom:16px">'
    f'{n_filtered:,} Flugabschnitte · {co2_filtered_t:,.0f} t CO₂eq</div>'
)

map_col, table_col = st.columns([1.1, 1])
with map_col:
    if globe_data:
        render_globe(globe_data, height=520)
    else:
        st.plotly_chart(
            charts.arc_map(routes, airports),
            use_container_width=True,
            config={"displayModeBar": False},
        )
with table_col:
    table_data = (
        filtered
        .assign(co2_t=lambda d: (d["co2_kg"] / 1000).round(2))
        .sort_values("co2_t", ascending=False)
        [[
            "source_year", "departure_airport", "iata_from",
            "arrival_airport", "iata_to", "final_destination",
            "class_", "department", "unit", "co2_t",
        ]]
        .rename(columns={
            "source_year": "Jahr",
            "departure_airport": "Abflug",
            "iata_from": "Von",
            "arrival_airport": "Ankunft",
            "iata_to": "Nach",
            "final_destination": "Enddestination",
            "class_": "Klasse",
            "department": "Departement",
            "unit": "Einheit",
            "co2_t": "CO₂ (t)",
        })
        .head(500)
    )
    st.dataframe(
        table_data,
        use_container_width=True,
        height=460,
        hide_index=True,
        column_config={
            "CO₂ (t)": st.column_config.NumberColumn(format="%.2f"),
        },
    )

styles.html(
    '<div class="method-note">'
    'Tabelle zeigt max. 500 Einträge, sortiert nach CO₂. '
    'Ziellandfilter = Ankunftsland; enthält Hin- und Rückflüge.'
    '</div>'
)
st.divider()


# ── Chapter 3 — Trend ───────────────────────────────────────────────────────

rumba_2023 = charts.RUMBA_SERIES[2023]
rumba_baseline = charts.RUMBA_2019_BASELINE_T
target_2030 = rumba_baseline * 0.70
reduction_pct = round((rumba_baseline - rumba_2023) / rumba_baseline * 100, 0)
gap_2023 = rumba_2023 - target_2030

styles.chapter_header(
    eyebrow="Kapitel 3",
    title="Ist die Bundesverwaltung auf Kurs?",
    lead=(
        f"Der Aktionsplan Flugreisen strebt bis 2030 eine Reduktion von 30 Prozent der THG-Emissionen "
        f"aus Flugreisen gegenüber 2019 an (Zielwert: {target_2030:,.0f} t CO₂eq). "
        f"Zwischen 2019 und 2023 konnten die Emissionen bereits um {reduction_pct:.0f} Prozent gesenkt werden — "
        f"die Bundesverwaltung befindet sich laut RUMBA-Umweltbericht 2024 «auf Zielkurs»."
    ),
)

trend_col, steps_col = st.columns([1.6, 1])
with trend_col:
    st.plotly_chart(
        charts.trend_chart(computed_2024_t=latest_total_t),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with steps_col:
    steps = [
        ("2019", f"Basisjahr — {rumba_baseline:,.0f} t",
         "Referenzwert für das −30%-Reduktionsziel bis 2030. "
         "Quelle: RUMBA Umweltbericht 2024, GS-UVEK."),
        ("2020", "COVID-Einbruch — 6'719 t",
         "Der globale Reisestopp halbierte die Emissionen. Kein klimapolitischer Erfolg, "
         "sondern ein Pandemieeffekt — daher aus der Trendlinie ausgeblendet."),
        ("2021–2023", "Erholung und Massnahmen",
         "Mit dem Ende der Pandemie stiegen die Emissionen wieder. Massnahmen wie "
         "Bahnvorrang und Economy-Pflicht bremsten den Wiederanstieg."),
        ("2023", f"«Auf Zielkurs» — {rumba_2023:,.0f} t",
         f"Die Emissionen liegen {gap_2023:,.0f} t über dem 2030-Ziel, "
         f"aber noch auf dem linearen Absenkpfad. "
         f"BR-Jet-Emissionen sind seit 2019 allerdings um 39% gestiegen."),
    ]

    st.markdown("<div style='padding-top:40px'></div>", unsafe_allow_html=True)
    for i, (year_lbl, heading, detail) in enumerate(steps):
        styles.html(f"""
<div class="step-card">
  <div class="step-number">Schritt {str(i+1).zfill(2)} / {str(len(steps)).zfill(2)}</div>
  <div class="step-text">{year_lbl}: {heading}</div>
  <div class="step-detail">{detail}</div>
</div>
""")

st.divider()


# ── Chapter 4 — Comparison ──────────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 4",
    title="Im Vergleich",
    lead=(
        "Wie steht die Schweizer Bundesverwaltung im Vergleich zu anderen Regierungen? "
        "Öffentlich zugängliche Emissionsdaten aus Dienstreisen sind selten — "
        "die meisten Regierungen publizieren diese Zahlen nicht. "
        "Das Vereinigte Königreich bildet eine Ausnahme."
    ),
)

st.plotly_chart(
    charts.comparison_chart(ch_total_t=latest_total_t),
    use_container_width=True,
    config={"displayModeBar": False},
)
styles.html("""
<div class="method-note">
  ⚠ Methodische Unterschiede zwischen Berichten —
  der Vergleich dient der Grössenordnung, nicht der Bewertung.<br>
  Datenquellen: Bundesverwaltung CH (berechnet), UK Greening Government Commitments Report.
</div>
""")
st.divider()


# ── Chapter 5 — Per-capita ───────────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 5",
    title="Was bedeutet das für mich?",
    lead=(
        "Wie vergleicht sich eine Person der Bundesverwaltung "
        "mit den durchschnittlichen Flugemissionen einer Schweizer Bürgerin oder "
        "eines Schweizer Bürgers — und mit dir selbst? "
        "Trage unten deine Flugreisen ein und sieh den Vergleich."
    ),
)

# Per-person estimate: total CO₂ divided by approximate number of BK staff who flew.
# A precise figure would require headcount data not present in the dataset.
n_staff_estimate = 5_000


def _bk_per_person_t(year: int) -> float:
    row = ytotals[ytotals["year"] == year]
    if row.empty:
        return 0.0
    return round(float(row["co2_t"].iloc[0]) / n_staff_estimate, 2)


# Searchable IATA labels: "ZRH — Zürich (Schweiz)". One row per IATA, sorted.
_ap_for_options = (
    airports.dropna(subset=["iata"])
    .drop_duplicates("iata")
    .sort_values("iata")
)


def _iata_label(iata: str, city: object, country: object) -> str:
    city_str = "" if pd.isna(city) else str(city)
    country_str = "" if pd.isna(country) else str(country)
    name = city_str or iata
    return f"{iata} — {name} ({country_str})" if country_str else f"{iata} — {name}"


iata_options: list[str] = [
    _iata_label(row["iata"], row["city"], row["country"])
    for _, row in _ap_for_options.iterrows()
]


def _iata_from_label(label: str | None) -> str | None:
    if not label or not isinstance(label, str):
        return None
    return label.split(" — ", 1)[0].strip() or None


tab_light, tab_advanced = st.tabs(["Schnell-Modus", "Erweitert"])

# ── Schnell-Modus ──────────────────────────────────────────────────────────
with tab_light:
    light_year = latest_year
    metrics = avg_leg_metrics(flights, light_year)
    mean_co2_kg = metrics["mean_co2_kg"]
    mean_distance_km = metrics["mean_distance_km"]

    styles.html(
        f'<div class="filter-label">Wie viele Flüge bist du {light_year} geflogen?</div>'
    )
    n_flights_col, _ = st.columns([1, 3])
    with n_flights_col:
        n_flights = st.number_input(
            f"Anzahl Flüge {light_year}",
            min_value=0,
            max_value=200,
            value=4,
            step=1,
            label_visibility="collapsed",
            key="ch5_light_n_flights",
        )

    user_t_light = n_flights * mean_co2_kg / 1000.0
    bk_pp_light = _bk_per_person_t(light_year)

    pc_col, text_col = st.columns([1, 1])
    with pc_col:
        st.plotly_chart(
            charts.per_capita_chart(bk_pp_light, user_t_light),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with text_col:
        ratio_swiss = (
            round(user_t_light / charts.BAFU_SWISS_AVG_T, 1)
            if charts.BAFU_SWISS_AVG_T > 0
            else 0.0
        )
        ratio_bk = (
            round(user_t_light / bk_pp_light, 1) if bk_pp_light > 0 else 0.0
        )
        if n_flights == 0:
            verdict = (
                "Du hast keine Flüge angegeben — dein Beitrag in dieser "
                "Kategorie ist Null."
            )
        elif user_t_light >= charts.BAFU_SWISS_AVG_T:
            verdict = (
                f"Du verursachst aus Flügen schätzungsweise "
                f"<strong>{user_t_light:.2f} t</strong> CO₂eq — rund "
                f"{ratio_swiss}× den Schweizer Durchschnitt "
                f"({charts.BAFU_SWISS_AVG_T} t)."
            )
        else:
            verdict = (
                f"Du verursachst aus Flügen schätzungsweise "
                f"<strong>{user_t_light:.2f} t</strong> CO₂eq — etwa "
                f"{ratio_swiss}× des Schweizer Durchschnitts "
                f"({charts.BAFU_SWISS_AVG_T} t)."
            )

        styles.html(f"""
<div style="padding-top:20px">
  <div class="eyebrow">Dein Vergleich · {light_year}</div>
  <div class="chapter-title" style="font-size:clamp(32px,3vw,48px)">
    {user_t_light:.2f} t
  </div>
  <p class="chapter-lead">
    {verdict}
    Eine Ø Person der Bundesverwaltung verursacht ca.
    <strong>{bk_pp_light:.2f} t</strong> CO₂eq pro Jahr aus Dienstflügen
    {f"(du = {ratio_bk}×)." if bk_pp_light > 0 else "."}
  </p>
  <div class="method-note">
    Annahme: Ø Distanz pro Flug {mean_distance_km:,.0f} km · Ø Emission pro Flug
    {mean_co2_kg:,.0f} kg CO₂eq (Basis: alle {int(metrics["n_legs"]):,} Flugabschnitte
    der Bundesverwaltung {light_year}). Schweizer Durchschnitt {charts.BAFU_SWISS_AVG_T} t (BAFU).
    BK-Pro-Kopf-Schätzung: Gesamttotal / ~{n_staff_estimate:,} fliegende Mitarbeitende.
  </div>
</div>
""")

# ── Erweitert ──────────────────────────────────────────────────────────────
with tab_advanced:
    styles.html('<div class="filter-label">Bezugsjahr</div>')
    adv_year_col, _ = st.columns([3, 1])
    with adv_year_col:
        adv_year = st.radio(
            "Bezugsjahr",
            options=all_years,
            index=all_years.index(latest_year),
            horizontal=True,
            label_visibility="collapsed",
            key="ch5_adv_year",
        )

    styles.html(
        '<div class="filter-label" style="margin-top:24px">'
        'Deine Flüge — Abflug, Ziel, Klasse und Anzahl wählen'
        '</div>'
    )

    default_origin = _iata_label("ZRH", "Zurich", "Switzerland")
    default_jfk = next((opt for opt in iata_options if opt.startswith("JFK ")), None)
    default_bru = next((opt for opt in iata_options if opt.startswith("BRU ")), None)
    default_origin_opt = (
        default_origin
        if default_origin in iata_options
        else next((opt for opt in iata_options if opt.startswith("ZRH ")), None)
    )

    default_trips = pd.DataFrame(
        [
            {"Abflug": default_origin_opt, "Ziel": default_jfk,
             "Klasse": "Economy", "Anzahl": 1},
            {"Abflug": default_origin_opt, "Ziel": default_bru,
             "Klasse": "Economy", "Anzahl": 2},
        ]
    )

    edited = st.data_editor(
        default_trips,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Abflug": st.column_config.SelectboxColumn(
                "Abflug",
                options=iata_options,
                required=False,
                help="IATA-Code oder Stadt suchen",
            ),
            "Ziel": st.column_config.SelectboxColumn(
                "Ziel",
                options=iata_options,
                required=False,
                help="IATA-Code oder Stadt suchen",
            ),
            "Klasse": st.column_config.SelectboxColumn(
                "Klasse",
                options=["Economy", "Business"],
                required=True,
            ),
            "Anzahl": st.column_config.NumberColumn(
                "Anzahl Flüge",
                min_value=0,
                max_value=200,
                step=1,
                default=1,
            ),
        },
        key="ch5_adv_editor",
    )

    user_kg_total = 0.0
    counted_legs = 0
    skipped: list[str] = []
    for _, row in edited.iterrows():
        iata_from = _iata_from_label(row.get("Abflug"))
        iata_to = _iata_from_label(row.get("Ziel"))
        count = row.get("Anzahl")
        class_ = row.get("Klasse") or "Economy"
        try:
            count_int = int(count) if pd.notna(count) else 0
        except (TypeError, ValueError):
            count_int = 0
        if not iata_from or not iata_to or count_int <= 0:
            continue
        distance = route_distance_km(airports, iata_from, iata_to)
        if distance is None or distance <= 0:
            skipped.append(f"{iata_from} → {iata_to}")
            continue
        user_kg_total += co2_for_distance(distance, class_) * count_int
        counted_legs += count_int

    user_t_adv = user_kg_total / 1000.0
    bk_pp_adv = _bk_per_person_t(adv_year)

    if skipped:
        st.warning(
            "Folgende Strecken konnten nicht berechnet werden (unbekannte IATA "
            "oder fehlende Koordinaten): " + ", ".join(skipped)
        )

    pc_col_adv, text_col_adv = st.columns([1, 1])
    with pc_col_adv:
        st.plotly_chart(
            charts.per_capita_chart(bk_pp_adv, user_t_adv),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with text_col_adv:
        ratio_swiss_adv = (
            round(user_t_adv / charts.BAFU_SWISS_AVG_T, 1)
            if charts.BAFU_SWISS_AVG_T > 0
            else 0.0
        )
        ratio_bk_adv = (
            round(user_t_adv / bk_pp_adv, 1) if bk_pp_adv > 0 else 0.0
        )
        if counted_legs == 0:
            verdict_adv = (
                "Trage oben mindestens einen Flug mit gültigen IATA-Codes ein, "
                "um deinen Vergleich zu sehen."
            )
        else:
            verdict_adv = (
                f"Deine {counted_legs} Flug(e) verursachen schätzungsweise "
                f"<strong>{user_t_adv:.2f} t</strong> CO₂eq — rund "
                f"{ratio_swiss_adv}× den Schweizer Durchschnitt "
                f"({charts.BAFU_SWISS_AVG_T} t)"
                + (f" und etwa {ratio_bk_adv}× eine Ø Person der "
                   f"Bundesverwaltung ({bk_pp_adv:.2f} t)." if bk_pp_adv > 0
                   else ".")
            )

        styles.html(f"""
<div style="padding-top:20px">
  <div class="eyebrow">Dein Vergleich · {adv_year}</div>
  <div class="chapter-title" style="font-size:clamp(32px,3vw,48px)">
    {user_t_adv:.2f} t
  </div>
  <p class="chapter-lead">{verdict_adv}</p>
  <div class="method-note">
    Berechnung: Großkreis-Distanz (Haversine) × myClimate-Faktor pro Strecke
    (0.255 / 0.185 / 0.147 kg CO₂eq/km für Kurz-/Mittel-/Langstrecke) × 2.0 bei Business.
    Vergleichswerte: BK-Pro-Kopf = Gesamtemissionen {adv_year} / ~{n_staff_estimate:,}
    fliegende Mitarbeitende. Schweizer Durchschnitt {charts.BAFU_SWISS_AVG_T} t (BAFU).
  </div>
</div>
""")

st.divider()


# ── Footer ───────────────────────────────────────────────────────────────────

styles.html("""
<div class="footer-section">
  <div class="footer-title">Methodik &amp; Quellen</div>
  <p class="footer-text">
    Kapitel 2 verwendet berechnete Emissionen aus den Flugdaten der Bundeskanzlei (2020–2024).
    Emissionsfaktor: myClimate-Methodik (kg CO₂eq/km/Passagier, inkl. RFI):
    0.255 kg/km (Kurzstrecke &lt;1'500 km), 0.185 kg/km (Mittelstrecke), 0.147 kg/km (Langstrecke).
    Business Class: Faktor 2.0.
    Kapitel 3 verwendet offizielle RUMBA-Zahlen aus den Umweltberichten 2021–2024 (GS-UVEK):
    2019 = 20'200 t (Aktionsplan-Basisjahr, abgeleitet), 2020 = 6'719 t, 2021 = 10'020 t,
    2022 = 14'409 t, 2023 = 16'904 t. Der Wert 2024 ist aus Flugdaten berechnet (keine offizielle RUMBA-Zahl verfügbar).
    Kapitel 4: UK-Vergleichswert aus Greening Government Commitments Report (gov.uk).
    Kapitel 5: Schweizer Durchschnitt 1.4 t/Person (BAFU).
  </p>
  <p class="footer-sources">
    Originalquellen: bk.admin.ch · admin.ch/gov/de/start/bundesrat/flugreisen ·
    RUMBA-Bericht GS-UVEK · gov.uk Greening Government Commitments · BAFU Treibhausgasinventar
  </p>
  <p class="footer-sources" style="margin-top:12px">
    ZHAW Semesterarbeit Frühlingssemester 2026 · L. Locarnini · A. Wyder
  </p>
</div>
""")
