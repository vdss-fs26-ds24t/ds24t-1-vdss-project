"""Editorial theme CSS injected into the Streamlit app."""

import streamlit as st

# Editorial palette — mirrors design_example/app.jsx THEMES.editorial
WARM = "#c0622a"       # oklch(0.55 0.18 35) ≈ burnt orange
COOL = "#3a7fa8"       # oklch(0.55 0.12 235) ≈ teal-blue
BG = "#fbf8f3"
BG2 = "#f3ede1"
TEXT = "#1a1a1a"
MUTED = "#6b6258"
GRID = "#e3dccd"
ACCENT = "#8c3a1a"     # oklch(0.42 0.18 25)

FONT_HEAD = "'Source Serif 4', 'Source Serif Pro', Georgia, serif"
FONT_BODY = "'Source Sans 3', 'Source Sans Pro', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Code', ui-monospace, monospace"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {{
  --warm: {WARM};
  --cool: {COOL};
  --bg: {BG};
  --bg2: {BG2};
  --text: {TEXT};
  --muted: {MUTED};
  --grid: {GRID};
  --head: {FONT_HEAD};
  --body: {FONT_BODY};
  --mono: {FONT_MONO};
}}

/* App background */
.stApp, [data-testid="stAppViewContainer"] {{
  background: var(--bg);
  font-family: var(--body);
  color: var(--text);
}}

/* Remove default Streamlit padding */
[data-testid="stMainBlockContainer"] {{
  padding-top: 0 !important;
  max-width: 1180px;
}}

/* Hide default header/toolbar */
[data-testid="stHeader"] {{ display: none; }}
#MainMenu, footer {{ visibility: hidden; }}

/* Chapter section dividers */
.chapter-divider {{
  border: none;
  border-top: 1px solid var(--grid);
  margin: 0;
}}

/* Eyebrow label above chapter title */
.eyebrow {{
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 12px;
}}

/* Chapter headings */
.chapter-title {{
  font-family: var(--head);
  font-size: clamp(36px, 4vw, 56px);
  line-height: 1.05;
  letter-spacing: -0.02em;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 16px 0;
  text-wrap: balance;
}}

/* Chapter lead text */
.chapter-lead {{
  font-family: var(--body);
  font-size: 18px;
  line-height: 1.5;
  color: var(--muted);
  margin-bottom: 40px;
  max-width: 680px;
  text-wrap: pretty;
}}

/* KPI tile */
.kpi-tile {{
  background: var(--bg2);
  border: 1px solid var(--grid);
  border-radius: 4px;
  padding: 28px 24px;
  position: relative;
  overflow: hidden;
}}
.kpi-bar-warm  {{ position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--warm); }}
.kpi-bar-cool  {{ position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--cool); }}
.kpi-bar-accent{{ position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: {ACCENT}; }}
.kpi-value {{
  font-family: var(--head);
  font-size: clamp(36px, 3.5vw, 52px);
  font-weight: 600;
  color: var(--text);
  line-height: 1;
  letter-spacing: -0.02em;
}}
.kpi-label {{
  margin-top: 12px;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}}

/* Hero */
.hero-section {{
  padding: 80px 0 60px;
}}
.hero-title {{
  font-family: var(--head);
  font-size: clamp(40px, 5vw, 72px);
  line-height: 0.98;
  letter-spacing: -0.025em;
  font-weight: 600;
  color: var(--text);
  text-wrap: balance;
}}
.hero-subtitle {{
  font-family: var(--body);
  font-size: 20px;
  line-height: 1.45;
  color: var(--muted);
  margin-top: 24px;
  max-width: 520px;
}}
.hero-number {{
  font-family: var(--head);
  font-size: clamp(48px, 5vw, 68px);
  font-weight: 600;
  color: var(--warm);
  line-height: 1;
  letter-spacing: -0.02em;
}}
.hero-number-label {{
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-top: 8px;
}}

/* Filter selects */
.filter-label {{
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 4px;
}}

/* Buttons (used for Chapter 3 step navigation) */
.stButton > button {{
  color: #ffffff;
  background: var(--text);
  border: 1px solid var(--text);
}}
.stButton > button:hover,
.stButton > button:active {{
  color: #ffffff;
  background: var(--text);
  border-color: var(--text);
}}

/* Methodology callout */
.method-note {{
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.04em;
  margin-top: 12px;
}}

/* Callout box */
.callout {{
  background: var(--bg2);
  border: 1px solid var(--grid);
  border-left: 4px solid var(--cool);
  border-radius: 6px;
  padding: 16px 18px;
  margin: 8px 0 28px;
}}
.callout-title {{
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 10px;
}}
.callout-text {{
  font-family: var(--body);
  font-size: 15px;
  line-height: 1.55;
  color: var(--text);
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
  gap: 8px;
  border-bottom: 1px solid var(--grid);
}}
.stTabs [data-baseweb="tab"] {{
  background: var(--bg2);
  color: var(--muted);
  border: 1px solid var(--grid);
  border-bottom: none;
  border-radius: 6px 6px 0 0;
  padding: 8px 12px;
  font-family: var(--mono);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
  background: var(--bg);
  color: var(--text);
  border-color: var(--text);
  border-bottom: 1px solid var(--bg);
}}

/* Scrolly step card */
.step-card {{
  border-left: 3px solid var(--grid);
  padding-left: 18px;
  margin-bottom: 48px;
}}
.step-card-active {{
  border-left: 3px solid var(--warm);
  padding-left: 18px;
  margin-bottom: 48px;
}}
.step-number {{
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}}
.step-text {{
  font-family: var(--head);
  font-size: 20px;
  line-height: 1.3;
  color: var(--text);
  font-weight: 600;
}}
.step-detail {{
  font-family: var(--body);
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
  margin-top: 8px;
}}

/* Footer */
.footer-section {{
  padding: 80px 0;
  border-top: 1px solid var(--grid);
  margin-top: 60px;
}}
.footer-title {{
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 12px;
}}
.footer-text {{
  font-family: var(--body);
  font-size: 16px;
  line-height: 1.55;
  color: var(--text);
  max-width: 680px;
}}
.footer-sources {{
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
  margin-top: 20px;
  letter-spacing: 0.04em;
}}
.warning-callout {{
  background: #fff4ea;
  border: 1px solid #f0d0b8;
  border-left: 4px solid var(--warm);
  border-radius: 6px;
  padding: 18px 20px;
  margin: 20px 0;
}}
.warning-callout-title {{
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text);
  margin-bottom: 8px;
}}
.warning-callout-text {{
  font-family: var(--body);
  font-size: 15px;
  line-height: 1.6;
  color: var(--text);
}}
</style>
"""


def inject() -> None:
    """Inject the editorial CSS into the Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def html(content: str) -> None:
    """Render raw HTML with unsafe_allow_html."""
    st.markdown(content, unsafe_allow_html=True)


def chapter_header(eyebrow: str, title: str, lead: str) -> None:
    html(f"""
<hr class="chapter-divider">
<div style="padding: 80px 0 0">
  <div class="eyebrow">{eyebrow}</div>
  <h2 class="chapter-title">{title}</h2>
  <p class="chapter-lead">{lead}</p>
</div>
""")


def kpi_tile(value: str, label: str, bar: str = "warm") -> None:
    html(f"""
<div class="kpi-tile">
  <div class="kpi-bar-{bar}"></div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-label">{label}</div>
</div>
""")
