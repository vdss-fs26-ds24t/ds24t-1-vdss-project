"""Bundesrat Flugemissionen — scrollable Streamlit data story."""

import logging

import streamlit as st

from lib import charts, styles
from lib.data import (
    add_destination_country,
    filter_flights,
    globe_routes,
    load_airports,
    load_flights,
    top_routes,
    yearly_totals,
)
from lib.globe import render_globe

logging.basicConfig(level=logging.INFO)

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


# ── Hero ─────────────────────────────────────────────────────────────────────
hero_left, hero_right = st.columns([1.2, 1])
with hero_left:
        styles.html("""
<div style="padding:80px 0 20px">
    <div class="eyebrow">Daten-Story · Frühlingssemester 2026 · ZHAW</div>
    <h1 class="hero-title">Wie viel CO₂ verursacht die Schweizer Regierung auf Reisen?</h1>
    <p class="hero-subtitle">
        Ein datengestützter Blick auf die Flugemissionen der Bundesverwaltung,
        2021–2024 — und die Frage: Ist die Schweiz auf Kurs?
    </p>
</div>
""")
        styles.html('<div class="filter-label">Jahr</div>')
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
        styles.html(f"""
<div style="margin-top:32px">
    <div class="hero-number">{hero_total_t:,.0f} t</div>
    <div class="hero-number-label">CO₂eq aus Dienstflügen · {hero_year}</div>
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


# ── Chapter 1 — KPIs ────────────────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 1",
    title="Der Bundesratsjet im Kontext",
    lead=(
        "Flugreisen stellen mit 61 Prozent den grössten Hotspot der Treibhausgasemissionen "
        "der Bundesverwaltung dar (RUMBA-Umweltbericht 2025). "
        f"2024 beliefen sich die Emissionen aus Dienstflügen auf {latest_total_t:,.0f} Tonnen CO₂eq."
    ),
)

col1, col2, col3 = st.columns(3)
with col1:
    styles.kpi_tile(
        value=f"{latest_total_t:,.0f} t",
        label=f"CO₂eq aus Dienstflügen · {latest_year}",
        bar="warm",
    )
with col2:
    styles.kpi_tile(
        value="61 %",
        label="Anteil Flugreisen an Gesamtemissionen Bundesverwaltung (2024)",
        bar="accent",
    )
with col3:
    n_legs = len(flights[flights["source_year"] == latest_year])
    styles.kpi_tile(
        value=f"{n_legs:,}",
        label=f"Einzelne Flugabschnitte · {latest_year}",
        bar="cool",
    )

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.divider()


# ── Chapter 2 — Who flies where ─────────────────────────────────────────────

styles.chapter_header(
    eyebrow="Kapitel 2",
    title="Wer fliegt wohin?",
    lead=(
        "Zwischen 2021 und 2024 flogen Mitarbeitende der Bundesverwaltung zu Treffen, "
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
        "mit den durchschnittlichen Flugemissionen einer Schweizer Bürgerin oder eines Schweizer Bürgers?"
    ),
)

# Per-person estimate: total CO₂ divided by approximate number of BK staff who flew
# We use total flight legs ÷ average legs per trip as a rough proxy for unique travellers.
# A better estimate requires headcount data not available in this dataset.
n_staff_estimate = 5_000  # approximate number of frequent-flying staff (rough proxy)
bk_per_person_t = round(latest_total_t / n_staff_estimate, 1)

pc_col, text_col = st.columns([1, 1])
with pc_col:
    st.plotly_chart(
        charts.per_capita_chart(bk_per_person_t),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with text_col:
    ratio = round(bk_per_person_t / charts.BAFU_SWISS_AVG_T, 1)
    styles.html(f"""
<div style="padding-top:20px">
  <div class="eyebrow">Einordnung</div>
  <div class="chapter-title" style="font-size:clamp(32px,3vw,48px)">
    ~{ratio}×
  </div>
  <p class="chapter-lead">
    Eine Person der Bundesverwaltung verursacht durch Dienstflüge schätzungsweise
    <strong>{bk_per_person_t}</strong> t CO₂eq pro Jahr —
    rund {ratio} Mal so viel wie der Schweizer Durchschnitt
    ({charts.BAFU_SWISS_AVG_T} t, Quelle: BAFU).
  </p>
  <div class="method-note">
    ⚠ Hinweis: Der Pro-Kopf-Wert ist eine Schätzung basierend auf ca. {n_staff_estimate:,}
    fliegenden Mitarbeitenden. Das Datenmaterial enthält keine Personenangaben.
  </div>
</div>
""")

st.divider()


# ── Footer ───────────────────────────────────────────────────────────────────

styles.html("""
<div class="footer-section">
  <div class="footer-title">Methodik &amp; Quellen</div>
  <p class="footer-text">
    Kapitel 2 verwendet berechnete Emissionen aus den Flugdaten der Bundeskanzlei (2021–2024).
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
