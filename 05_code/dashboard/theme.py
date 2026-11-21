"""MethaTwin dashboard - brand palette, CSS and Plotly template.

Palette: deep-ink text, MethaTwin teal as the brand colour, a flame amber accent.
The categorical chart slots (teal, blue, amber, violet) were checked with a colour-vision
validator: worst adjacent CVD separation dE 19.6, all inside the lightness band. Amber is
below 3:1 contrast on white, so it is only used with visible labels.
"""
from __future__ import annotations

import base64
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

ASSETS = Path(__file__).resolve().parent / "assets"

INK = "#0B1F2A"
INK_2 = "#3E5560"
MUTED = "#6B7C83"
TEAL = "#0E8A6E"
TEAL_DARK = "#0B6E5B"
TEAL_LIGHT = "#D7F0E8"
AMBER = "#E39B2F"
FLAME = "#F2A93B"
BLUE = "#2F6FDB"
VIOLET = "#8B5CC4"
PAGE = "#F4F7F6"
CARD = "#FFFFFF"
BORDER = "#E2E8E6"
GRID = "#EBEFEE"
GOOD, WARN, BAD = "#15803D", "#B45309", "#B91C1C"
SERIES = [TEAL, BLUE, AMBER, VIOLET]
SEQ = ["#E8F6F1", "#BFE6D8", "#86CDB5", "#45AE8E", "#0E8A6E", "#0A5E4B", "#073D31"]


def svg_data_uri(name: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, button, input, label, textarea, select {{
  font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif !important;
}}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ visibility: hidden; height: 0; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1380px; }}
[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] .block-container {{ padding-top: 1rem; }}
h1, h2, h3, h4 {{ color: {INK}; letter-spacing: -0.01em; }}

/* header */
.mt-hero {{ display:flex; align-items:center; justify-content:space-between; gap:24px;
  background: linear-gradient(120deg, {INK} 0%, #0F3A3A 55%, {TEAL_DARK} 100%);
  border-radius: 18px; padding: 22px 28px; margin-bottom: 18px; color: #fff;
  box-shadow: 0 10px 30px rgba(11,31,42,0.18); }}
.mt-hero-left {{ display:flex; align-items:center; gap:18px; }}
.mt-hero-mark {{ width:58px; height:58px; background:#fff; border-radius:14px; padding:6px; }}
.mt-hero .ttl {{ color:#fff; font-size: 1.95rem; font-weight: 800; margin: 0; line-height:1.1; letter-spacing:-0.02em; }}
.mt-hero .ttl span {{ color: #5EE0B8; font-weight: 600; }}
.mt-hero p {{ color: #C9DCD8; margin: 4px 0 0 0; font-size: 0.93rem; }}
.mt-tags {{ display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-end; max-width: 520px; }}
.mt-tag {{ border:1px solid rgba(255,255,255,0.22); color:#E7F2EF; border-radius:999px;
  padding:4px 11px; font-size:0.76rem; font-weight:500; background: rgba(255,255,255,0.06); white-space:nowrap; }}

/* banner */
.mt-banner {{ border-radius: 12px; padding: 12px 16px; margin: 2px 0 16px 0; font-size: 0.92rem;
  display:flex; gap:12px; align-items:flex-start; border:1px solid; }}
.mt-banner b {{ font-weight: 700; }}
.mt-banner.ok {{ background:#ECF8F1; border-color:#BFE5CF; color:#0F5132; }}
.mt-banner.warn {{ background:#FFF6E8; border-color:#F6D7A6; color:#7A3E06; }}
.mt-banner.bad {{ background:#FDEEEE; border-color:#F3C4C4; color:#7F1D1D; }}
.mt-banner .ico {{ font-weight:800; font-size:1.05rem; line-height:1.2; }}

/* KPI cards */
.mt-kpis {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:14px; margin-bottom: 16px; }}
@media (max-width: 1100px) {{ .mt-kpis {{ grid-template-columns: repeat(2, minmax(0,1fr)); }} }}
.mt-kpi {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px;
  box-shadow: 0 1px 2px rgba(11,31,42,0.04); position:relative; overflow:hidden; }}
.mt-kpi::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:{TEAL}; }}
.mt-kpi.amber::before {{ background:{AMBER}; }}
.mt-kpi.blue::before {{ background:{BLUE}; }}
.mt-kpi.violet::before {{ background:{VIOLET}; }}
.mt-kpi .lbl {{ color:{MUTED}; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; }}
.mt-kpi .val {{ color:{INK}; font-size:1.9rem; font-weight:800; margin-top:4px; letter-spacing:-0.02em; }}
.mt-kpi .val small {{ font-size:0.9rem; font-weight:600; color:{INK_2}; margin-left:4px; }}
.mt-kpi .sub {{ font-size:0.82rem; margin-top:2px; color:{INK_2}; }}
.mt-kpi .sub.good {{ color:{GOOD}; font-weight:600; }}
.mt-kpi .sub.bad {{ color:{BAD}; font-weight:600; }}
.mt-kpi .sub.warn {{ color:{WARN}; font-weight:600; }}

/* panels */
.mt-panel-title {{ font-weight:700; color:{INK}; font-size:1.0rem; margin: 0 0 2px 0; }}
.mt-panel-sub {{ color:{MUTED}; font-size:0.82rem; margin: 0 0 10px 0; }}
.mt-table {{ width:100%; border-collapse:collapse; font-size:0.86rem; border:none !important; margin:0; }}
.mt-table tr, .mt-table tr:nth-child(even) {{ background:transparent !important; border:none !important; }}
.mt-table td {{ padding:8px 6px !important; border:none !important; border-bottom:1px solid {GRID} !important; color:{INK}; vertical-align:middle; background:transparent !important; }}
.mt-table td.k {{ color:{INK_2}; }}
.mt-table td.v {{ font-weight:700; text-align:right; white-space:nowrap; font-variant-numeric: tabular-nums; }}
.mt-table td.l {{ color:{MUTED}; text-align:right; font-size:0.78rem; white-space:nowrap; }}
.mt-table td.s {{ text-align:right; width:1%; white-space:nowrap; }}
.chip {{ display:inline-block; border-radius:999px; padding:2px 9px; font-size:0.74rem; font-weight:700; }}
.chip.ok {{ background:#E3F5EA; color:{GOOD}; }}
.chip.warn {{ background:#FFF1DB; color:{WARN}; }}
.chip.bad {{ background:#FDE4E4; color:{BAD}; }}
.mt-note {{ color:{MUTED}; font-size:0.8rem; margin-top:6px; }}
.mt-section {{ font-weight:800; color:{INK}; font-size:1.15rem; margin: 6px 0 2px 0; }}
.mt-section-sub {{ color:{MUTED}; font-size:0.88rem; margin-bottom: 12px; }}
.mt-side-brand {{ display:flex; align-items:center; gap:10px; margin: 0 0 6px 0; }}
.mt-side-brand img {{ width:34px; }}
.mt-side-brand div {{ font-weight:800; color:{INK}; font-size:1.1rem; }}
.mt-side-brand div span {{ color:{TEAL}; font-weight:600; }}
.mt-foot {{ color:{MUTED}; font-size:0.78rem; text-align:center; margin-top: 28px; padding-top: 14px; border-top:1px solid {BORDER}; }}

/* streamlit widgets */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{ height: 44px; padding: 0 16px; font-weight: 600; color: {INK_2}; }}
.stTabs [aria-selected="true"] {{ color: {TEAL_DARK} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {TEAL}; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px; }}
[data-testid="stExpander"] details {{ border-radius: 12px; border-color: {BORDER}; }}
[data-testid="stExpander"] summary p {{ font-weight: 650; color:{INK}; }}
</style>
"""


def plotly_template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", size=12.5, color=INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=SERIES,
        margin=dict(l=10, r=14, t=44, b=10),
        title=dict(font=dict(size=14.5, color=INK, family="Inter, Segoe UI, sans-serif"), x=0, xanchor="left"),
        xaxis=dict(gridcolor=GRID, zeroline=False, linecolor="#C9D3D0", ticks="outside", tickcolor="#C9D3D0",
                   title=dict(font=dict(size=12, color=MUTED))),
        yaxis=dict(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)", title=dict(font=dict(size=12, color=MUTED))),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(color=INK, size=12.5)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=11.5),
                    bgcolor="rgba(0,0,0,0)"),
        bargap=0.35,
    )
    return t


pio.templates["methatwin"] = plotly_template()
pio.templates.default = "methatwin"
