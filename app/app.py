"""Bundesrat Flugemissionen — scrollable Streamlit data story."""

import logging
from dataclasses import dataclass
import os

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


@dataclass(frozen=True)
class TrendStep:
    """Narrative step for the Chapter 3 trend story."""

    year: int
    label: str
    heading: str
    detail: str


st.set_page_config(
    page_title="Bundesrat Flugemissionen",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

styles.inject()


# ── Data ────────────────────────────────────────────────────────────────────
from pathlib import Path
import os
st.write("CWD:", os.getcwd())
st.write("data dir exists:", Path("data").exists())
st.write("data dir listing:", [p.name for p in Path("data").glob("*")] if Path("data").exists() else "NO DATA DIR")

flights = load_flights()
airports = load_airports()
flights = add_destination_country(flights, airports)

st.write("flights:", flights.shape)
st.write("airports:", airports.shape)
st.write("years:", sorted(flights["source_year"].unique()) if not flights.empty else "NO FLIGHTS")

if flights.empty:
    st.error("Flugdaten konnten nicht geladen werden. Bitte prüfe den Ordner data/ im Repo.")
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
        2020–2024 
    </p>
    <p class="hero-subtitle">
        Und die Frage: Ist die Schweiz auf Kurs?
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
                        key="hero_arcmap",
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
"---"
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

# styles.html('<div class="filter-label">RUMBA-Bericht auswählen</div>')
# rumba_years_cht1 = sorted(RUMBA_KEY_FIGURES)
# default_rumba_index = (
#     rumba_years_cht1.index(latest_year)
#     if latest_year in rumba_years_cht1
#     else len(rumba_years_cht1) - 1
# )
# report_by_label = {label: info for label, info in zip(rumba_years_cht1, RUMBA_REPORTS)}

# rumba_col_left, rumba_col_right = st.columns([3, 1])
# with rumba_col_left:
#     rumba_year_cht1 = st.radio(
#         "Datenjahr (RUMBA)",
#         options=rumba_years_cht1,
#         index=default_rumba_index,
#         horizontal=True,
#         label_visibility="collapsed",
#         key="ch0_rumba_year",
#     )
# selected_report = report_by_label[rumba_year_cht1]

# rc1, rc2, rc3 = st.columns(3)
# with rc1:
#     styles.kpi_tile(
#         value=str(selected_report.report_year),
#         label="Berichtsjahr",
#         bar="warm",
#     )
# with rc2:
#     styles.kpi_tile(
#         value=str(selected_report.data_year),
#         label="Datenjahr",
#         bar="accent",
#     )
# with rc3:
#     styles.kpi_tile(
#         value=selected_report.publisher_short,
#         label="Herausgeber",
#         bar="cool",
#     )

# styles.html(
#     f'<div class="method-note">'
#     f'Quellen: {selected_report.source}; RUMBA 2021, Kap. 1.1; RUMBA 2023, Kap. 1.2. '
#     'Hinweis: Herausgeberwechsel BFE (Berichte 2021–2022) → GS-UVEK (ab Bericht 2023).'
#     '</div>'
# )
"---"
tab_scope, tab_reports, tab_programs, tab_methods, tab_ubp, tab_other = st.tabs(
    [
        "Was ist RUMBA?",
        "Berichte",
        "Klimapaket & Aktionsplan",
        "Methodik & Referenzjahre",
        "UBP (Umweltbelastung)",
        "Weitere Informationen"
    ]
)

with tab_scope:
    st.markdown(
        """
        **RUMBA (Ressourcen- und Umweltmanagement der Bundesverwaltung)** erfasst die Umweltbelastungen der zivilen Bundesverwaltung.
        
        * **Organisationen:** Das System umfasst sechs Departemente, die Bundeskanzlei und die Parlamentsdienste. Wichtig: Das **VBS** (Verteidigung, Bevölkerungsschutz und Sport) ist nicht Teil von RUMBA. Es bilanziert seine Emissionen seit 2001 separat über das System «RUMS-VBS», um Doppelzählungen zu vermeiden.
        * **Themenbereiche:** Traditionell deckt RUMBA die grössten Hebel ab: Dienstreisen, den Gebäudebereich (Wärme, Strom, Wasser, Abfall) und den Papierverbrauch. 
        * **Ausblick:** Ab dem Berichtsjahr 2025 wird der Scope um Kältemittel sowie um fünf Satellit-Themen erweitert (IT-Material, Verpflegung, mobiles Arbeiten, Pendelfahrten und Plastikrecycling).
        """
    )
    styles.html(
        '<div class="method-note">Quellen: RUMBA 2021, Kap. 1.1; RUMBA 2025, Kap. 1.</div>'
    )
with tab_reports:
    # styles.html('<div class="filter-label">RUMBA-Bericht auswählen</div>')
    # rumba_years_cht1 = sorted(RUMBA_KEY_FIGURES)
    # default_rumba_index = (
    #     rumba_years_cht1.index(latest_year)
    #     if latest_year in rumba_years_cht1
    #     else len(rumba_years_cht1) - 1
    # )
    # report_by_label = {label: info for label, info in zip(rumba_years_cht1, RUMBA_REPORTS)}

    # rumba_col_left, rumba_col_right = st.columns([3, 1])
    # with rumba_col_left:
    #     rumba_year_cht1 = st.radio(
    #         "Datenjahr (RUMBA)",
    #         options=rumba_years_cht1,
    #         index=default_rumba_index,
    #         horizontal=True,
    #         label_visibility="collapsed",
    #         key="ch0_rumba_year",
    #     )
    # selected_report = report_by_label[rumba_year_cht1]

    # rc1, rc2, rc3 = st.columns(3)
    # with rc1:
    #     styles.kpi_tile(
    #         value=str(selected_report.report_year),
    #         label="Berichtsjahr",
    #         bar="warm",
    #     )
    # with rc2:
    #     styles.kpi_tile(
    #         value=str(selected_report.data_year),
    #         label="Datenjahr",
    #         bar="accent",
    #     )
    # with rc3:
    #     styles.kpi_tile(
    #         value=selected_report.publisher_short,
    #         label="Herausgeber",
    #         bar="cool",
    #     )

    # styles.html(
    #     f'<div class="method-note">'
    #     f'Quellen: {selected_report.source}; RUMBA 2021, Kap. 1.1; RUMBA 2023, Kap. 1.2. '
    #     'Hinweis: Herausgeberwechsel BFE (Berichte 2021–2022) → GS-UVEK (ab Bericht 2023).'
    #     '</div>'
    # )
    st.markdown(
        "Die folgende Tabelle bietet eine kompakte Übersicht über die publizierten RUMBA-Umweltberichte, "
        "die zugrundeliegenden Datenjahre sowie die jeweils zuständigen Herausgeber."
    )
    
    # Daten für die Tabelle aus der RUMBA_REPORTS Liste aufbereiten
    report_data = [
        {
            "Berichtsjahr": str(report.report_year),
            "Datenjahr": str(report.data_year),
            "Herausgeber": report.publisher,
            "Quelle": report.source
        }
        for report in RUMBA_REPORTS
    ]
    
    # Tabelle anzeigen
    st.dataframe(
        pd.DataFrame(report_data),
        use_container_width=True,
        hide_index=True
    )

    styles.html(
        '<div class="method-note">'
        'Hinweis: Herausgeberwechsel BFE (Berichte 2021–2022) → GS-UVEK (ab Bericht 2023).'
        '</div>'
    )

with tab_programs:
    st.markdown(
        """
        Die Reduktionspfade der Bundesverwaltung basieren auf zwei zentralen politischen Beschlüssen aus dem Jahr 2019, die vorgeben, ob RUMBA «auf Kurs» ist:
        
        **1. Das Klimapaket Bundesverwaltung (Juli 2019)**
        * **Das Ziel:** Reduktion der Treibhausgasemissionen (THG) der Verwaltung im Inland bis **2030 um 50 %** gegenüber dem Basisjahr 2006.
        * **Klimaneutralität:** Verbleibende Emissionen werden vollständig kompensiert (bis 2021 durch Zertifikate, ab 2022 durch internationale Bescheinigungen).
        
        **2. Der Aktionsplan Flugreisen (Dezember 2019)**
        Fokussiert spezifisch auf den grössten Hotspot der Verwaltung:
        * **Das Ziel:** Reduktion der THG-Emissionen aus Flugreisen um **30 % bis 2030** (gegenüber 2019).
        * **Konkrete Massnahmen:** * *Zug statt Flugzeug:* Bei einer Reisezeit unter 6 Stunden muss der Zug genutzt werden.
          * *Economy statt Business:* Direktflüge bis 9h und Flüge mit Zwischenlandung bis 11h erfolgen zwingend in Economy. (EDA und EDI haben 2024 sogar eine generelle «Economy-only»-Regel eingeführt).
          * *Kleinere Delegationen:* Mehr als 5 Personen müssen speziell begründet werden.
          * *Virtuelle Meetings:* Vermeidung von Reisen durch Telefon- und Videokonferenzen.
        """
    )
    styles.html(
        '<div class="method-note">Quellen: RUMBA 2021, Kap. 1.3 & 3.2; RUMBA 2024, Kap. 4; RUMBA 2025, Kap. 3.2.</div>'
    )

with tab_methods:
    st.markdown(
        """
        Bei der Interpretation der RUMBA-Daten müssen wichtige methodische Besonderheiten beachtet werden:
        
        **Das extrapolierte Referenzjahr 2020**
        Das reale Jahr 2020 war durch die Covid-19-Pandemie (Homeoffice, Flugverbote) ein massiver Ausreisser. Für die Zielüberwachung rechnet der Bundesrat daher nicht mit den realen Pandemie-Zahlen, sondern mit einem **extrapolierten (fiktiven) Referenzjahr 2020**. Dieses basiert auf den Werten von 2019 abzüglich des politisch geforderten Absenkpfads.
        
        **Erweiterte Systemgrenzen ab 2020**
        Zahlen vor 2020 sind nicht 1:1 mit den heutigen Werten vergleichbar. Ab 2020 wurden die Messungen deutlich verschärft:
        * **Bundesratsjets & Helikopter:** Werden seither vollumfänglich bei den Flugreisen mitgezählt. (Allein 2020 machten diese auf Anhieb 46 % der gesamten Flug-Emissionen aus).
        * **Papier:** Neu wurden sämtliche externen Druckaufträge (wie Abstimmungsbüchlein oder Publikationen) sowie Hygienepapier bilanziert.
        
        **⚠️ Wichtig bei Datenanalysen: Excel-Listen vs. RUMBA-Bericht**
        Es gibt einen fundamentalen Unterschied zwischen den verschiedenen Datensätzen der Bundesverwaltung:
        * **Die Excel-Fluglisten (Rohdaten):** Die öffentlich publizierten Excel-Dateien enthalten ausschliesslich die über zivile Reisebüros gebuchten *Linienflüge*. Die Flüge der Bundesratsjets und Armee-Helikopter (Lufttransportdienst des Bundes LTDB) fehlen in diesen Listen komplett.
        * **Der RUMBA-Umweltbericht (Gesamtabrechnung):** In den offiziellen Berichten und den dort ausgewiesenen CO₂-Gesamtemissionen (die als Grundlage für die Kapitel 1 und 3 dieser Story dienen) sind die Staatsjets seit 2020 *vollständig eingerechnet*.
        
        *Wer für eigene Auswertungen nur die Excel-Listen nutzt, übersieht daher systematisch den CO₂-Ausstoss der Regierungsflieger.*
        """
    )
    styles.html(
        '<div class="method-note">'
        'Quellen: RUMBA 2021, Kap. 3.1; RUMBA 2022, Fussnote 7 zu Kap. 2.1; UVEK-Dokumentation zu den Fluglisten.</div>'
    )

with tab_ubp:
    st.markdown(
        """
        Neben den Treibhausgasen (THG) weist RUMBA die **UBP (Umweltbelastungspunkte)** als zweite Hauptkennzahl aus. Das Ziel ist eine Reduktion der UBP pro Vollzeitstelle (FTE) um 21 % bis 2027.
        
        * **Die Methode:** Die UBP basieren auf der «Methode der ökologischen Knappheit» des BAFU. Sie messen nicht nur Klimagase, sondern vollaggregiert auch Emissionen in Boden, Wasser und Luft sowie Lärm und Ressourcenerschöpfung (wie Kies, Süsswasser oder Landnutzung).
        * **Ein anderer Blickwinkel:** Die UBP-Sichtweise verschiebt die Gewichtung der Umwelt-Hotspots dramatisch. Während *Flugreisen* bei den CO₂-Emissionen unangefochten auf Platz 1 stehen, ist in der UBP-Perspektive oft das **Papier** der grösste Hebel. Der Frischfaserverbrauch von externen Druckaufträgen fällt bei der Ressourcenerschöpfung extrem stark ins Gewicht.
        """
    )
    styles.html(
        '<div class="method-note">Quellen: RUMBA 2021, Kap. 2.2.3 & Fussnote 1; '
        'RUMBA 2024, Kap. 2.2.</div>'
    )
with tab_other:
    st.markdown(
        """
        Neben den Flugreisen treibt die Bundesverwaltung die Dekarbonisierung auch in ihren anderen Kernbereichen durch strikte Vorgaben voran:
        
        **Fahrzeugflotte (Mobilität am Boden)**
        * **Elektrifizierung:** Gemäss einer revidierten Weisung (seit Januar 2021) dürfen grundsätzlich nur noch Fahrzeuge mit alternativen Antrieben (Energieeffizienzklasse A oder B) beschafft werden. 
        * **Langfristiger Wandel:** Der Umstieg von fossilen Fahrzeugen auf Elektroautos geschieht schrittweise, da Fahrzeuge erst am Ende ihrer Lebensdauer ersetzt werden. Dennoch hat sich die elektrisch zurückgelegte Strecke zwischen 2020 und 2024 bereits **ver-13-facht**.
        * **Mobilitätsprinzipien:** Priorität hat der Verzicht auf Fahrten, gefolgt vom öffentlichen Verkehr (ÖV) und Carsharing/Carpooling.
        
        **Gebäudebereich (Wärme & Strom)**
        * **Abschied von Fossilenergie:** Die Umsetzungskonzepte der Bau- und Liegenschaftsorgane (ab 2020) sehen den Verzicht auf den Einbau neuer fossiler Heizungen sowie den kompletten Ersatz bestehender Ölheizungen bis 2030 vor. 
        * **Nachhaltiges Bauen:** Neubauten und Sanierungen orientieren sich an strengen Zertifizierungen wie dem Standard Nachhaltiges Bauen Schweiz (SNBS) Hochbau oder Minergie-P/A/ECO.
        * **Betriebsoptimierung:** Auch kleine Massnahmen zeigen Wirkung. So half beispielsweise die Winter-Energiespar-Initiative 2022/2023 (u.a. Reduktion der Raumtemperatur auf 20 °C) den Energiebedarf spürbar zu senken.
        """
    )
    styles.html(
        '<div class="method-note">Quellen: RUMBA 2021, Kap. 1.3.3 & 3.3; RUMBA 2023, Kap. 2.3.2; RUMBA 2024, Kap. 4.3; RUMBA 2025, Kap. 2.2.1 & 2.2.2.</div>'
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
            key="ch2_arcmap",
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

rumba_2021 = charts.RUMBA_SERIES[2021]
rumba_2022 = charts.RUMBA_SERIES[2022]
rumba_2023 = charts.RUMBA_SERIES[2023]
rumba_2024 = charts.RUMBA_SERIES[2024]
rumba_baseline = charts.RUMBA_2019_BASELINE_T
target_2030 = rumba_baseline * 0.70
reduction_pct = round((rumba_baseline - rumba_2024) / rumba_baseline * 100, 0)
gap_2024 = rumba_2024 - target_2030

# Lineare Fortsetzung basierend auf den offiziellen 2019–2024 Werten.
forecast_years = 2024 - 2019
forecast_slope = (rumba_2024 - rumba_baseline) / forecast_years
forecast_2025_t = rumba_2024 + forecast_slope

styles.chapter_header(
    eyebrow="Kapitel 3",
    title="Ist die Bundesverwaltung auf Kurs?",
    lead=(
        f"Der Aktionsplan Flugreisen strebt bis 2030 eine Reduktion von 30 Prozent der THG-Emissionen "
        f"aus Flugreisen gegenüber 2019 an (Zielwert: {target_2030:,.0f} t CO₂eq). "
        f"Zwischen 2019 und 2024 konnten die Emissionen bereits um {reduction_pct:.0f} Prozent gesenkt werden."
        f"Das heisst, die Bundesverwaltung befindet sich laut RUMBA-Umweltbericht 2025 weiterhin «auf Kurs»."
    ),
)

chart_slot = st.container()
steps_slot = st.container()

steps: list[TrendStep] = [
    TrendStep(
        year=2019,
        label="2019",
        heading=f"Das Vorkrisen-Basisjahr — {rumba_baseline:,.0f} t",
        detail="""
        Mit rund 20'200 Tonnen CO₂-eq** bildet das Jahr 2019 den historischen Massstab für den 
        Aktionsplan Flugreisen. Es repräsentiert die administrative Realität vor der Pandemie: 
        Der Flugbetrieb lief auf Hochtouren, internationale Diplomatie fand fast ausschliesslich 
        physisch statt und virtuelle Meetings waren in der Bundesverwaltung noch die absolute Ausnahme. 
        Hier wurde der Grundstein für die geforderte Reduktion um 30 % bis 2030 gelegt.
        """,
    ),
    TrendStep(
        year=2020,
        label="2020",
        heading="Der Corona-Schock & neue Messgrössen — 6'719 t",
        detail="""
        Die Emissionen brechen durch den globalen Lockdown, strenge Reiserestriktionen und den 
        massiven Wechsel ins Homeoffice historisch auf 6'719 Tonnen CO₂-eq ein (ein Minus von fast 67 %). 
        Methodischer Meilenstein: Mitten in der Krise verschärft der Bundesrat die Systemgrenzen. 
        Ab 2020 werden die Bundesratsjets (LTDB) und sämtliche externen Druckaufträge (z. B. Abstimmungsbüchlein) 
        vollständig mitgezählt. Ohne die Pandemie hätte dies zu einem massiven Sprung nach oben geführt.
        """,
    ),
    TrendStep(
        year=2021,
        label="2021",
        heading=f"Die gedämpfte Rückkehr — {rumba_2021:,.0f} t",
        detail="""
        Mit 10'020 Tonnen CO₂-eq erholen sich die Emissionen leicht, bleiben aber künstlich gedämpft. 
        Das Jahr ist immer noch stark von der Pandemie geprägt: Laufende Quarantäneregelungen, 
        internationale Einreisebeschränkungen und das etablierte Bewusstsein für digitale Konferenzen 
        halten den Flugverkehr auf einem niedrigen Niveau. Die Verwaltung beweist, dass Betrieb auch mit 
        weniger Reisetätigkeit funktioniert.
        """,
    ),
    TrendStep(
        year=2022,
        label="2022",
        heading=f"Der Rebound-Effekt & die Energiekrise — {rumba_2022:,.0f} t",
        detail="""
        Die Emissionen schiessen nach dem Wegfall fast aller Corona-Massnahmen auf 14'409 Tonnen CO₂-eq hoch. 
        Nachholbedarf bei der physischen Diplomatie und aufgestaute Reiselust führen zu einer regelrechten 
        Flug-Explosion. Demgegenüber steht ein Erfolg im Gebäudebereich: Die *Winter-Energiespar-Initiative 2022/2023* (u. a. Absenkung der Raumtemperatur in Bundesbauten auf 20 °C) dämpft den fossilen Energieverbrauch spürbar.
        """,
    ),
    TrendStep(
        year=2023,
        label="2023",
        heading=f"Der Post-Corona-Peak & politischer Druck — {rumba_2023:,.0f} t",
        detail="""
        Die Emissionen erreichen mit 16'904 Tonnen CO₂-eq ihren Höchststand nach der Pandemie. 
        Die Reisetätigkeit nähert sich gefährlich nah dem Vorkrisenniveau. Es wird politisch und medial 
        offensichtlich: Freiwilliger Verzicht reicht nicht aus, um die Klimaziele einzuhalten. 
        Die Departemente geraten unter Zugzwang. Das EDA und das EDI reagieren und bereiten für das 
        Folgejahr verschärfte, verbindliche Richtlinien vor (u. a. weitreichende 'Economy-Only'-Zwänge).
        """,
    ),
    TrendStep(
        year=2024,
        label="2024",
        heading=f"Die Trendwende durch Struktur — {rumba_2024:,.0f} t",
        detail="""
        Erstmals sinken die Emissionen im regulären Betrieb wieder spürbar auf **15'220 Tonnen CO₂-eq (ca. -10 % zum Vorjahr). 
        Dieser Rückgang ist kein Zufall oder Pandemie-Effekt mehr, sondern das Resultat struktureller Vorgaben. 
        Die griffigen Massnahmen des Aktionsplans,  wie das strikte Zug-Gebot bei Reisen unter 6 Stunden und die 
        restriktiven Economy-Vorgaben bei Langstrecken, greifen nun flächendeckend im Alltag der Bundesangestellten. 
        Die Kurve biegt endlich in die richtige Richtung ab.
        """,
    ),
    TrendStep(
        year=2025,
        label="2025",
        heading=f"Prognose — {forecast_2025_t:,.0f} t",
        detail=(
            "Lineare Fortsetzung 2019–2024; keine offizielle RUMBA-Zahl."
        ),
    ),
]

default_step_index = next(
    (i for i, step in enumerate(steps) if step.year == 2024),
    0,
)
if "ch3_step_index" not in st.session_state:
    st.session_state["ch3_step_index"] = default_step_index

max_step_index = len(steps) - 1
current_index = st.session_state["ch3_step_index"]

with steps_slot:
    nav_left, nav_mid, nav_right = st.columns([1, 5, 1])
    with nav_left:
        if st.button("←", key="ch3_prev"):
            st.session_state["ch3_step_index"] = max(0, current_index - 1)
    with nav_right:
        if st.button("→", key="ch3_next"):
            st.session_state["ch3_step_index"] = min(max_step_index, current_index + 1)

    current_index = st.session_state["ch3_step_index"]
    with nav_mid:
        styles.html(
            f"<div class=\"step-number\" style=\"text-align:center; margin-top:6px\">"
            f"Schritt {str(current_index + 1).zfill(2)} / {str(len(steps)).zfill(2)}"
            "</div>"
        )
    current_step = steps[current_index]

    st.markdown("<div style='padding-top:24px'></div>", unsafe_allow_html=True)
    styles.html(f"""
<div class="step-card-active">
  <div class="step-number">Schritt {str(current_index+1).zfill(2)} / {str(len(steps)).zfill(2)}</div>
  <div class="step-text">{current_step.label}: {current_step.heading}</div>
  <div class="step-detail">{current_step.detail}</div>
</div>
""")

with chart_slot:
    st.plotly_chart(
        charts.trend_chart(
            computed_2024_t=latest_total_t,
            forecast_2025_t=forecast_2025_t,
            max_year=current_step.year,
            
        ),
        use_container_width=True,
        config={"displayModeBar": False},
        key=f"ch3_trend_{current_step.year}"
    )

styles.html("""
<div class="method-note">
  Quelle: RUMBA-Umweltberichte 2021 bis 2025 (Datenjahre 2020–2024); historische Grundlagendaten gemäss Aktionsplan Flugreisen (Basisjahr 2019).
</div>
""")

st.divider()


# ── Chapter 4 — Comparison ──────────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 4",
    title="Im Vergleich",
    lead=(
        "Wie unterscheiden sich die Klimaziele der Schweizer Bundesverwaltung von jenen "
        "der britischen Regierung? Dieser Vergleich zeigt: Die Schweiz nimmt sich mehr Zeit, "
        "setzt dafür aber auf viel striktere Verbote."
    ),
)

styles.html(
    """
<div class="warning-callout">
  <div class="warning-callout-title">Wichtiger Hinweis</div>
  <div class="warning-callout-text">
    In diesem Kapitel werden die unterschiedliche Zielmodelle der Schweiz und Grossbritanien verglichen. 
    Ein direkter Vergleich der Bilanzen ist nicht seriös möglich, da sich die Basisjahre, 
    die Systemgrenzen (z.B. Einbezug des Militärs) und die Messgrössen (CO₂-Ausstoss vs. 
    geflogene Distanz) fundamental unterscheiden.
  </div>
</div>
"""
)
st.subheader("Der Blick über die Grenze")

st.markdown(
    """
    #### Transparenz & Policy-Vergleich
    Anstatt absoluter Zahlen lohnt sich ein Blick auf die Spielregeln. Die Schweiz sticht international vor allem durch ihre Daten-Transparenz hervor (jeder zivile Linienflug ist in Excel-Listen einsehbar). 
    
    | Kriterium | 🇨🇭 Schweiz (Aktionsplan Flugreisen) | 🇬🇧 UK (Greening Gov. Commitments) |
    | :--- | :--- | :--- |
    | **Vergleichstyp** | Relative Zielkurve für Flugemissionen | Zielpfad für reduzierte Flugdistanz |
    | **Basisjahr** | 2019 | 2017/18 |
    | **Bemessungsgröße** | Flug-CO₂ laut RUMBA | Geflogene Distanz |
    | **Hauptziel** | - 30 % CO₂ (bis 2030) | - 30 % Distanz (bis 2025) |
    | **Zug-Vorgaben** | Zug obligatorisch bei Reise < 6h | Keine harte, generelle Stunden-Regel |
    | **Economy-Regel** | Zwingend bis 9h (Direkt) / 11h | "Economy Class first"-Policy |
    | **Inlandflüge** | Keine spezifische Regelung | Explizites Ziel: -30% "Domestic Flights" |
    """
)

# Render new indexed chart
fig_comp = charts.indexed_comparison_chart()
st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False}, key="ch4_comparison")

styles.html("""
<div class="method-note">
  Quellen: UK Greening Government Commitments (2021-2025); RUMBA Aktionsplan Flugreisen. 
  Der Chart indexiert die unterschiedlichen Basisjahre (CH: 2019, UK: 2017/2018) und stellt reale Schweizer Ziele
  neben dem offiziellen UK-Zielpfad dar. Dieser Vergleich soll die Ambition der Zielpfade verdeutlichen, nicht
  eine direkte absolute CO₂-Bilanz.
</div>
""")

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
            key=f"ch5_light_pc_{light_year}"
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
            key=f"ch5_adv_pc_{adv_year}"
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


# # ── Footer ───────────────────────────────────────────────────────────────────

# styles.html("""
# <div class="footer-section">
#   <div class="footer-title">Methodik &amp; Quellen</div>
#   <p class="footer-text">
#     Kapitel 2 verwendet berechnete Emissionen aus den Flugdaten der Bundeskanzlei (2020–2024).
#     Emissionsfaktor: myClimate-Methodik (kg CO₂eq/km/Passagier, inkl. RFI):
#     0.255 kg/km (Kurzstrecke &lt;1'500 km), 0.185 kg/km (Mittelstrecke), 0.147 kg/km (Langstrecke).
#     Business Class: Faktor 2.0.
#     Kapitel 3 verwendet offizielle RUMBA-Zahlen aus den Umweltberichten 2021–2025 (GS-UVEK):
#     2019 = 20'200 t (Aktionsplan-Basisjahr, abgeleitet), 2020 = 6'719 t, 2021 = 10'020 t,
#     2022 = 14'409 t, 2023 = 16'904 t, 2024 = 15'220 t. Zusätzlich: 2024 berechnet (Flugdaten)
#     und Prognose 2025 als lineare Fortsetzung 2019–2024.
#     Kapitel 4: UK-Vergleichswert aus Greening Government Commitments Report (gov.uk).
#     Kapitel 5: Schweizer Durchschnitt 1.4 t/Person (BAFU).
#   </p>
#   <p class="footer-sources">
#     Originalquellen: bk.admin.ch · admin.ch/gov/de/start/bundesrat/flugreisen ·
#     RUMBA-Bericht GS-UVEK · gov.uk Greening Government Commitments · BAFU Treibhausgasinventar
#   </p>
#   <p class="footer-sources" style="margin-top:12px">
#     ZHAW Semesterarbeit Frühlingssemester 2026 · L. Locarnini · A. Wyder
#   </p>
# </div>
# """)
# ── Footer ───────────────────────────────────────────────────────────────────

styles.html("""
<div class="footer-section">
  <div class="footer-title">Methodik</div>
  <ul class="footer-text" style="list-style-type: none; padding-left: 0; margin-bottom: 32px; display: flex; flex-direction: column; gap: 12px;">
    <li>
      <strong>Kapitel 2 & 5 (Berechnungen):</strong> Basieren auf den veröffentlichten zivilen Flugdaten. 
      Verwendete Emissionsfaktoren (myClimate-Methodik inkl. RFI): 0.255 kg CO₂eq/km (Kurzstrecke &lt;1'500 km), 
      0.185 kg/km (Mittelstrecke), 0.147 kg/km (Langstrecke). Business Class: Faktor 2.0. 
      Schweizer Durchschnitt: 1.4 t/Person (BAFU).
    </li>
    <li>
      <strong>Kapitel 1 & 3 (RUMBA-Zahlen):</strong> Verwenden die offiziellen RUMBA-Umweltberichte 2021–2025 
      (Herausgeber GS-UVEK). Die historischen Werte für 2019 (20'200 t) dienen als Aktionsplan-Basisjahr. 
      Die Prognose für 2025 ist eine einfache lineare Fortsetzung der Jahre 2019–2024.
    </li>
    <li>
      <strong>Kapitel 4 (UK-Vergleich):</strong> Zieht für die Gegenüberstellung die offiziellen 
      Greening Government Commitments der britischen Regierung heran.
    </li>
  </ul>

  <div class="footer-title">Quellen & Links</div>
  <ul class="footer-text" style="list-style-type: none; padding-left: 0; margin-bottom: 32px; display: flex; flex-direction: column; gap: 8px;">
    <li><a href="https://vdss-fs26-ds24t.github.io/ds24t-1-vdss-project/" target="_blank" style="color: inherit; text-decoration: underline;">Dokumentation der Data Story (GitHub)</a></li>
    <li><a href="https://www.uvek.admin.ch/de/rumba#Liste-der-Flugreisen" target="_blank" style="color: inherit; text-decoration: underline;">Liste der zivilen Flugreisen (UVEK/RUMBA)</a></li>
    <li><a href="https://www.uvek.admin.ch/de/lufttransportdienst-des-bundes-fluege-der-departementsvorsteherin-des-departementvorstehers" target="_blank" style="color: inherit; text-decoration: underline;">Lufttransportdienst des Bundes (Bundesratsjets & Helikopter)</a></li>
    <li><a href="https://www.gov.uk/government/collections/greening-government-commitments" target="_blank" style="color: inherit; text-decoration: underline;">UK Greening Government Commitments (Übersicht)</a></li>
    <li><a href="https://www.gov.uk/government/publications/greening-government-commitments-2021-to-2025/greening-government-commitments-2021-to-2025" target="_blank" style="color: inherit; text-decoration: underline;">UK Greening Government Commitments (2021 bis 2025)</a></li>
  </ul>

  <div style="border-top: 1px solid var(--muted); padding-top: 16px; margin-top: 16px;">
    <p class="footer-sources" style="margin: 0;">
      <strong>ZHAW Semesterarbeit Frühlingssemester 2026</strong> · L. Locarnini · A. Wyder
    </p>
  </div>
</div>
""")