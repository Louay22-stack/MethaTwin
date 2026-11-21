"""MethaTwin - design system: tokens, global CSS and the Plotly template.

Design language (v2): industrial instrument panel.
* Surfaces: sage-cream canvas, white work surfaces, a deep petrol application bar.
* Structure through 1 px rules and grid alignment, not rounded cards; 4 px radius maximum.
* Type: Space Grotesk (headings, key numbers), Inter (body), IBM Plex Mono (labels, units, tags).
* Colour carries meaning only: petrol/teal = brand and primary actions, coral = the current design
  and attention, status green/amber/red = constraint state (always with an icon and a word).
Chart slots (teal, blue, coral, violet) pass a colour-vision validator (worst adjacent CVD dE 19.6).
Coral is below 3:1 on white, so it is only used for marks that also carry a label.
"""
from __future__ import annotations

import base64
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

ASSETS = Path(__file__).resolve().parent / "assets"

# ---------------------------------------------------------------- tokens ----
PETROL_950 = "#061F1C"
PETROL_900 = "#0A2E2A"
PETROL_800 = "#0D3D37"
PETROL_600 = "#145A50"
TEAL = "#0E8A6E"          # brand + chart slot 1
MINT = "#9BE3BF"          # highlights on dark surfaces
MINT_SOFT = "#DDF3E7"
BLUE = "#2F6FDB"          # chart slot 2
CORAL = "#E2683F"         # chart slot 3 + "current design" marker
VIOLET = "#7E5BC2"        # chart slot 4
INK = "#0B2622"
INK_2 = "#3A4F4A"
MUTED = "#61736E"
CANVAS = "#EEF1EC"
SURFACE = "#FFFFFF"
SURFACE_2 = "#F6F8F5"
LINE = "#D3DBD5"
LINE_SOFT = "#E4E9E4"
GOOD, WARN, BAD = "#1F7A45", "#A86400", "#B42F25"
GOOD_BG, WARN_BG, BAD_BG = "#E5F3EA", "#FBF0DC", "#F9E3E0"
SERIES = [TEAL, BLUE, CORAL, VIOLET]
SEQ = ["#EAF6F0", "#C3E8D6", "#8FD0B5", "#4FB08F", "#1F8A6E", "#11604F", "#083B32"]
FONT_HEAD = "'Space Grotesk', 'Inter', 'Segoe UI', sans-serif"
FONT_BODY = "'Inter', 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_MONO = "'IBM Plex Mono', 'JetBrains Mono', Consolas, monospace"


def svg_data_uri(name: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {{
  --petrol-950:{PETROL_950}; --petrol-900:{PETROL_900}; --petrol-800:{PETROL_800}; --petrol-600:{PETROL_600};
  --teal:{TEAL}; --mint:{MINT}; --mint-soft:{MINT_SOFT}; --coral:{CORAL}; --blue:{BLUE}; --violet:{VIOLET};
  --ink:{INK}; --ink-2:{INK_2}; --muted:{MUTED}; --canvas:{CANVAS}; --surface:{SURFACE}; --surface-2:{SURFACE_2};
  --line:{LINE}; --line-soft:{LINE_SOFT};
  --good:{GOOD}; --warn:{WARN}; --bad:{BAD}; --good-bg:{GOOD_BG}; --warn-bg:{WARN_BG}; --bad-bg:{BAD_BG};
  --f-head:{FONT_HEAD}; --f-body:{FONT_BODY}; --f-mono:{FONT_MONO};
  --r:4px; --ease: cubic-bezier(.2,.7,.2,1);
}}

/* ---------- base ---------- */
html, body, .stApp, button, input, textarea, select, label, p, li, td, th, .stMarkdown, [data-testid="stWidgetLabel"] {{
  font-family: var(--f-body);
}}
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {{
  font-family: "Material Symbols Rounded" !important; letter-spacing: normal !important; text-transform: none !important;
}}
.stApp {{ background: var(--canvas); color: var(--ink); }}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] {{ display:none !important; }}
[data-testid="stHeader"] {{ background: transparent; height: 0; min-height: 0; overflow: visible; }}
[data-testid="stExpandSidebarButton"] {{ position: fixed !important; top: 12px; left: 10px; z-index: 999990; width: 34px !important; height: 32px !important;
  display:flex !important; align-items:center; justify-content:center; background: var(--petrol-600) !important; color:#fff !important;
  border-radius: var(--r); border: 1px solid rgba(255,255,255,.15); }}
[data-testid="stExpandSidebarButton"] span {{ color:#fff !important; }}
.stApp:has([data-testid="stSidebar"][aria-expanded="false"]) .mt-brand {{ padding-left: 58px !important; }}
.st-key-mtnav {{ overflow-x: auto; overflow-y: hidden; }}
.block-container {{ padding: 0 1.6rem 3rem 1.6rem !important; max-width: 1480px; }}
h1, h2, h3, h4 {{ font-family: var(--f-head); color: var(--ink); letter-spacing: -0.01em; }}
p, li {{ color: var(--ink-2); font-size: 0.92rem; line-height: 1.55; }}
a {{ color: var(--teal); }}
@keyframes mt-in {{ from {{ opacity:0; transform: translateY(4px); }} to {{ opacity:1; transform:none; }} }}
[data-testid="stMainBlockContainer"] > div {{ animation: mt-in .28s var(--ease) both; }}

/* ---------- application bar ---------- */
.mt-appbar {{ position: relative; margin: 0 -1.6rem 0 -1.6rem; width: calc(100% + 3.2rem); background: var(--petrol-900); color: #fff;
  display:flex; align-items:stretch; min-height: 56px; border-bottom: 1px solid var(--petrol-950); }}
.mt-brand {{ display:flex; align-items:center; gap:10px; padding: 0 22px 0 1.6rem; border-right: 1px solid rgba(255,255,255,.10); }}
.mt-brand img {{ width:30px; height:30px; }}
.mt-brand .nm {{ font-family: var(--f-head); font-weight:600; font-size: 1.12rem; letter-spacing:-0.01em; color:#fff; }}
.mt-brand .nm span {{ color: var(--mint); font-weight:500; }}
.mt-brand .ver {{ font-family: var(--f-mono); font-size: .62rem; color: rgba(255,255,255,.55); border:1px solid rgba(255,255,255,.2);
  padding: 1px 5px; border-radius: 3px; margin-left: 4px; }}
.mt-appbar-right {{ margin-left:auto; display:flex; align-items:center; gap: 16px; padding: 0 1.6rem; }}
.mt-status {{ font-family: var(--f-mono); font-size: .68rem; letter-spacing:.06em; text-transform: uppercase; color: rgba(255,255,255,.78);
  display:flex; align-items:center; gap:8px; white-space:nowrap; }}
.mt-dot {{ width:8px; height:8px; border-radius:50%; background: var(--mint); box-shadow: 0 0 0 3px rgba(155,227,191,.18); }}
.mt-dot.warn {{ background:#F2B544; box-shadow: 0 0 0 3px rgba(242,181,68,.2); }}
.mt-dot.bad {{ background:#F07A6A; box-shadow: 0 0 0 3px rgba(240,122,106,.2); }}

/* page-link navigation (container key "mtnav"), restyled as an instrument strip */
.st-key-mtnav {{ background: var(--petrol-800); margin: 0 -1.6rem 0 -1.6rem; width: calc(100% + 3.2rem) !important; padding: 0 1.2rem; border-bottom: 1px solid var(--petrol-950); }}
.st-key-mtnav [data-testid="stHorizontalBlock"] {{ gap: 0 !important; overflow-x: auto; flex-wrap: nowrap !important; scrollbar-width: thin; }}
.st-key-mtnav [data-testid="stHorizontalBlock"] > div {{ flex: 0 0 auto !important; width:auto !important; min-width:0 !important; }}
.st-key-mtnav [data-testid="stPageLink"] a {{ border-radius:0 !important; padding: 11px 16px !important; margin:0 !important; background: transparent !important;
  border-right: 1px solid rgba(255,255,255,.08); transition: background .18s var(--ease); }}
.st-key-mtnav [data-testid="stPageLink"] a p, .st-key-mtnav [data-testid="stPageLink"] a span {{ font-family: var(--f-mono) !important; font-size: .73rem !important;
  letter-spacing: .07em; text-transform: uppercase; color: rgba(255,255,255,.7) !important; white-space: nowrap; }}
.st-key-mtnav [data-testid="stPageLink"] a:hover {{ background: rgba(255,255,255,.06) !important; }}
.st-key-mtnav [data-testid="stPageLink"] a:hover p {{ color:#fff !important; }}
.st-key-mtnav [data-testid="stPageLink"] a[aria-current="page"] {{ box-shadow: inset 0 -2px 0 var(--mint); background: rgba(255,255,255,.06) !important; }}
.st-key-mtnav [data-testid="stPageLink"] a[aria-current="page"] p, .st-key-mtnav [data-testid="stPageLink"] a[aria-current="page"] span {{ color: #fff !important; }}
/* in-page links (next steps) */
.st-key-nextsteps [data-testid="stPageLink"] a {{ border: 1px solid var(--line); border-radius: var(--r); background: var(--surface); padding: 8px 12px;
  transition: border-color .18s var(--ease), background .18s var(--ease); }}
.st-key-nextsteps [data-testid="stPageLink"] a:hover {{ border-color: var(--teal); background: var(--mint-soft); }}
.st-key-nextsteps [data-testid="stPageLink"] a p {{ font-weight: 500; color: var(--ink); font-size: .86rem; }}

/* ---------- page header ---------- */
.mt-pagehead {{ display:flex; align-items:flex-end; justify-content:space-between; gap:24px; padding: 18px 0 14px 0;
  border-bottom: 1px solid var(--line); margin-bottom: 16px; }}
.mt-crumb {{ font-family: var(--f-mono); font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; color: var(--muted); margin-bottom:4px; }}
.mt-crumb b {{ color: var(--teal); font-weight:600; }}
.mt-title {{ font-family: var(--f-head); font-size: 1.42rem; font-weight: 600; color: var(--ink); line-height:1.15; }}
.mt-title em {{ font-style: normal; color: var(--teal); }}
.mt-lede {{ color: var(--muted); font-size: .88rem; max-width: 760px; margin-top: 4px; }}
.mt-head-meta {{ font-family: var(--f-mono); font-size:.7rem; color: var(--muted); text-align:right; line-height:1.6; white-space:nowrap; }}
.mt-head-meta b {{ color: var(--ink); font-weight:600; }}

/* ---------- section label ---------- */
.mt-sec {{ display:flex; align-items:baseline; gap:10px; margin: 22px 0 10px 0; padding-bottom: 6px; border-bottom: 1px solid var(--line-soft); }}
.mt-sec .idx {{ font-family: var(--f-mono); font-size:.7rem; color: var(--teal); letter-spacing:.06em; }}
.mt-sec .t {{ font-family: var(--f-head); font-weight:600; font-size: 1.0rem; color: var(--ink); }}
.mt-sec .s {{ color: var(--muted); font-size: .82rem; margin-left: auto; text-align:right; }}

/* ---------- verdict bar ---------- */
.mt-verdict {{ display:flex; align-items:stretch; border:1px solid var(--line); background: var(--surface); border-radius: var(--r); overflow:hidden; }}
.mt-verdict .flag {{ width: 6px; background: var(--good); }}
.mt-verdict.warn .flag {{ background: #D99A21; }}
.mt-verdict.bad .flag {{ background: var(--bad); }}
.mt-verdict .body {{ padding: 11px 16px; display:flex; gap: 14px; align-items:center; flex-wrap: wrap; width:100%; }}
.mt-verdict .tag {{ font-family: var(--f-mono); font-size: .68rem; letter-spacing:.08em; text-transform: uppercase; font-weight:600;
  padding: 3px 8px; border-radius: 3px; background: var(--good-bg); color: var(--good); white-space:nowrap; }}
.mt-verdict.warn .tag {{ background: var(--warn-bg); color: var(--warn); }}
.mt-verdict.bad .tag {{ background: var(--bad-bg); color: var(--bad); }}
.mt-verdict .msg {{ color: var(--ink); font-size: .9rem; flex: 1 1 380px; }}
.mt-verdict .msg b {{ font-weight: 600; }}

/* ---------- KPI strip (instrument readouts, divided by rules) ---------- */
.mt-kpis {{ display:grid; grid-template-columns: repeat(var(--n, 5), minmax(0,1fr)); background: var(--surface);
  border:1px solid var(--line); border-radius: var(--r); margin: 12px 0 4px 0; }}
.mt-kpi {{ padding: 12px 16px 12px 16px; border-right: 1px solid var(--line-soft); min-width: 0; transition: background .18s var(--ease); }}
.mt-kpi:last-child {{ border-right: none; }}
.mt-kpi:hover {{ background: var(--surface-2); }}
.mt-kpi .l {{ font-family: var(--f-mono); font-size:.66rem; letter-spacing:.08em; text-transform: uppercase; color: var(--muted);
  display:flex; align-items:center; gap:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mt-kpi .l i {{ width:8px; height:8px; border-radius:2px; display:inline-block; flex: none; }}
.mt-kpi .v {{ font-family: var(--f-head); font-size: 1.65rem; font-weight: 600; color: var(--ink); letter-spacing:-0.02em; margin-top: 4px;
  font-variant-numeric: tabular-nums; white-space:nowrap; }}
.mt-kpi .v small {{ font-family: var(--f-mono); font-size:.72rem; font-weight:500; color: var(--muted); margin-left: 5px; letter-spacing:0; }}
.mt-kpi .d {{ font-size:.78rem; color: var(--ink-2); margin-top: 2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mt-kpi .d.good {{ color: var(--good); font-weight:600; }}
.mt-kpi .d.bad {{ color: var(--bad); font-weight:600; }}
.mt-kpi .d.warn {{ color: var(--warn); font-weight:600; }}
@media (max-width: 1100px) {{ .mt-kpis {{ grid-template-columns: repeat(3, minmax(0,1fr)); }} .mt-kpi {{ border-bottom: 1px solid var(--line-soft); }} }}
@media (max-width: 640px) {{ .mt-kpis {{ grid-template-columns: repeat(2, minmax(0,1fr)); }} .mt-kpi .v {{ font-size: 1.35rem; }} }}

/* ---------- panels (flat, ruled) ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > div > .mt-ph), div[data-testid="stVerticalBlock"]:has(> div > .stMarkdown .mt-ph) {{ }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: var(--r) !important; border-color: var(--line) !important; background: var(--surface); }}
.mt-ph {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin: -2px 0 8px 0; }}
.mt-ph .t {{ font-family: var(--f-head); font-weight: 600; font-size: .98rem; color: var(--ink); }}
.mt-ph .s {{ font-family: var(--f-mono); font-size: .66rem; letter-spacing:.07em; text-transform: uppercase; color: var(--muted); text-align:right; }}

/* ---------- constraint / spec table ---------- */
.mt-scroll {{ width:100%; overflow-x:auto; -webkit-overflow-scrolling: touch; }}
.mt-spec {{ width:100%; border-collapse: collapse; font-size: .85rem; border:none !important; }}
.mt-spec tr, .mt-spec tr:nth-child(even) {{ background: transparent !important; border: none !important; }}
.mt-spec th {{ font-family: var(--f-mono); font-size:.64rem; letter-spacing:.08em; text-transform: uppercase; color: var(--muted) !important; font-weight:500;
  text-align:left; padding: 0 8px 6px 0 !important; border:none !important; border-bottom: 1px solid var(--line) !important; background: transparent !important; }}
.mt-spec td {{ padding: 8px 8px 8px 0 !important; border:none !important; border-bottom: 1px solid var(--line-soft) !important; vertical-align: middle;
  color: var(--ink); background: transparent !important; }}
.mt-spec td.n {{ color: var(--ink-2); }}
.mt-spec td.v {{ font-family: var(--f-mono); font-weight: 600; text-align:right; white-space:nowrap; font-variant-numeric: tabular-nums; }}
.mt-spec td.lim {{ font-family: var(--f-mono); font-size:.74rem; color: var(--muted); white-space:nowrap; text-align:right; }}
.mt-spec td.bar {{ width: 30%; min-width: 90px; padding-top: 10px !important; }}
.mt-spec td.bar .lt {{ font-family: var(--f-mono); font-size:.66rem; color: var(--muted); margin-top: 5px; white-space: nowrap; }}
.mt-spec td.st {{ text-align:right; white-space:nowrap; width:1%; }}
.mt-gauge {{ position:relative; height: 6px; background: var(--line-soft); border-radius: 3px; overflow: visible; }}
.mt-gauge .fill {{ position:absolute; left:0; top:0; bottom:0; border-radius:3px; background: var(--teal); transition: width .35s var(--ease); }}
.mt-gauge .fill.warn {{ background: #D99A21; }} .mt-gauge .fill.bad {{ background: var(--bad); }}
.mt-gauge .lim {{ position:absolute; top:-3px; width: 2px; height: 12px; background: var(--ink); }}
.st-chip {{ display:inline-flex; align-items:center; gap:5px; font-family: var(--f-mono); font-size:.66rem; letter-spacing:.06em; text-transform: uppercase;
  font-weight:600; padding: 2px 7px; border-radius: 3px; }}
.st-chip.ok {{ background: var(--good-bg); color: var(--good); }}
.st-chip.warn {{ background: var(--warn-bg); color: var(--warn); }}
.st-chip.bad {{ background: var(--bad-bg); color: var(--bad); }}
.st-chip.info {{ background: var(--surface-2); color: var(--ink-2); border:1px solid var(--line); }}

/* ---------- process flow diagram ---------- */
.mt-pfd {{ width:100%; background: var(--surface); border:1px solid var(--line); border-radius: var(--r); padding: 6px 4px 2px 4px; }}
.mt-pfd svg {{ width:100%; height:auto; display:block; }}
.mt-pfd svg .unit {{ transition: opacity .18s var(--ease); cursor: help; }}
.mt-pfd svg .unit:hover rect.box, .mt-pfd svg .unit:hover path.box {{ stroke: var(--teal); stroke-width: 2; }}
.mt-pfd svg .flow {{ stroke-dasharray: 6 5; animation: mt-flow 1.6s linear infinite; }}
@keyframes mt-flow {{ to {{ stroke-dashoffset: -22; }} }}
@media (prefers-reduced-motion: reduce) {{ .mt-pfd svg .flow {{ animation: none; }} [data-testid="stMainBlockContainer"] > div {{ animation:none; }} }}
.mt-legend {{ display:flex; gap: 16px; flex-wrap: wrap; font-family: var(--f-mono); font-size: .66rem; letter-spacing:.06em;
  text-transform: uppercase; color: var(--muted); margin: 6px 2px 0 2px; }}
.mt-legend span {{ display:inline-flex; align-items:center; gap:6px; }}
.mt-legend i {{ width: 18px; height: 3px; display:inline-block; border-radius:2px; }}

/* ---------- empty / info states ---------- */
.mt-empty {{ border: 1px dashed var(--line); border-radius: var(--r); background: var(--surface-2); padding: 28px 20px; text-align:center; }}
.mt-empty .t {{ font-family: var(--f-head); font-weight:600; color: var(--ink); font-size: 1rem; }}
.mt-empty .s {{ color: var(--muted); font-size: .86rem; margin-top: 4px; }}
.mt-note {{ font-size: .78rem; color: var(--muted); margin-top: 6px; }}
.mt-note b {{ color: var(--ink-2); }}
.mt-callout {{ border-left: 3px solid var(--teal); background: var(--mint-soft); padding: 10px 14px; border-radius: 0 var(--r) var(--r) 0;
  font-size: .86rem; color: var(--ink); margin: 8px 0; }}
.mt-callout.blue {{ border-left-color: var(--blue); background: #E8EFFC; }}
.mt-callout.warn {{ border-left-color: #D99A21; background: var(--warn-bg); }}
.mt-kv {{ display:grid; grid-template-columns: auto 1fr; gap: 6px 16px; font-size: .86rem; }}
.mt-kv dt {{ font-family: var(--f-mono); font-size: .68rem; letter-spacing:.07em; text-transform:uppercase; color: var(--muted); padding-top: 2px; }}
.mt-kv dd {{ margin:0; color: var(--ink); }}

/* ---------- sidebar = design console ---------- */
[data-testid="stSidebar"] {{ background: var(--surface); border-right: 1px solid var(--line); }}
[data-testid="stSidebar"][aria-expanded="true"] {{ min-width: 300px !important; }}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{ padding-top: 0; }}
[data-testid="stSidebarUserContent"] {{ padding: 0 1.1rem 2rem 1.1rem !important; }}
.mt-console-head {{ margin: 0 -1.1rem 12px -1.1rem; padding: 14px 1.1rem 12px 1.1rem; background: var(--petrol-900); color:#fff; }}
.mt-console-head .k {{ font-family: var(--f-mono); font-size: .64rem; letter-spacing:.1em; text-transform: uppercase; color: var(--mint); }}
.mt-console-head .t {{ font-family: var(--f-head); font-size: 1.02rem; font-weight: 600; margin-top: 2px; color:#fff; }}
.mt-console-head .s {{ font-size: .78rem; color: rgba(255,255,255,.66); margin-top: 2px; }}
.mt-group {{ display:flex; align-items:center; gap:8px; margin: 16px 0 4px 0; font-family: var(--f-mono); font-size: .66rem; letter-spacing:.09em;
  text-transform: uppercase; color: var(--ink-2); font-weight: 600; }}
.mt-group::after {{ content:""; flex:1; height:1px; background: var(--line-soft); }}
.mt-group .n {{ color: var(--teal); }}
.mt-derived {{ display:flex; justify-content:space-between; font-family: var(--f-mono); font-size:.72rem; color: var(--muted); padding: 2px 0; }}
.mt-derived b {{ color: var(--ink); font-weight:600; }}
.mt-mod {{ display:inline-block; font-family: var(--f-mono); font-size:.62rem; letter-spacing:.06em; text-transform: uppercase; color: var(--coral);
  border: 1px solid rgba(226,104,63,.45); border-radius: 3px; padding: 0 5px; margin-left: 6px; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ font-size: .82rem !important; color: var(--ink-2) !important; font-weight: 500; }}
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"] {{ font-family: var(--f-mono); font-size: .72rem; }}
[data-testid="stSidebar"] [data-testid="stExpander"] details {{ border-radius: var(--r); border-color: var(--line); }}

/* ---------- widgets ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stPopover"] > div > button {{ border-radius: var(--r) !important; font-weight: 500;
  border: 1px solid var(--line) !important; transition: all .18s var(--ease); font-size: .86rem; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: var(--teal) !important; color: var(--teal) !important; }}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"]:hover {{ color:#fff !important; }}
[data-testid="stBaseButton-primary"] p {{ color:#fff !important; }}
[data-testid="stBaseButton-primary"] {{ background: var(--petrol-800) !important; border-color: var(--petrol-800) !important; }}
[data-testid="stBaseButton-primary"]:hover {{ background: var(--teal) !important; border-color: var(--teal) !important; }}
[data-testid="stBaseButton-primary"]:disabled, .stButton > button:disabled {{ background: var(--surface-2) !important; border-color: var(--line) !important;
  color: var(--muted) !important; cursor: not-allowed; }}
[data-testid="stBaseButton-primary"]:disabled p {{ color: var(--muted) !important; }}
.stButton > button[kind="primary"] {{ background: var(--petrol-800) !important; color: #fff !important; border-color: var(--petrol-800) !important; }}
.stButton > button[kind="primary"]:hover {{ background: var(--teal) !important; border-color: var(--teal) !important; color:#fff !important; }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--line); border-radius: var(--r); }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div {{ border-radius: var(--r) !important; }}
[data-testid="stSegmentedControl"] button p, [data-testid="stPills"] button p {{ font-size: .8rem; }}
[data-testid="stExpander"] details {{ border-radius: var(--r) !important; border-color: var(--line) !important; background: var(--surface); }}
[data-testid="stExpander"] summary p {{ font-weight: 600; color: var(--ink); font-size: .88rem; }}
[data-testid="stPlotlyChart"] {{ border-radius: var(--r); }}
[data-testid="stToast"] {{ border-radius: var(--r); border: 1px solid var(--line); }}

.mt-foot {{ display:flex; justify-content:space-between; gap: 16px; flex-wrap: wrap; font-family: var(--f-mono); font-size:.66rem; letter-spacing:.06em;
  text-transform: uppercase; color: var(--muted); margin-top: 32px; padding-top: 12px; border-top: 1px solid var(--line); }}

@media (max-width: 760px) {{
  .block-container {{ padding: 0 .9rem 2rem .9rem !important; }}
  .mt-appbar {{ margin: 0 -.9rem; width: calc(100% + 1.8rem); }}
  .mt-brand {{ padding-left: .9rem; border-right: none; }}
  .mt-status span.txt {{ display:none; }}
  .st-key-mtnav {{ margin: 0 -.9rem; padding: 0 .4rem; width: calc(100% + 1.8rem) !important; }}
  .mt-pagehead {{ flex-direction: column; align-items: flex-start; }}
  .mt-head-meta {{ text-align:left; }}
  .mt-sec .s {{ display:none; }}
  .mt-spec td.bar {{ min-width: 70px; width: 26%; }}
  .mt-spec td.n {{ min-width: 92px; }}
  .mt-verdict .msg {{ flex-basis: 100%; }}
  .mt-pfd {{ overflow-x: auto; }}
  .mt-pfd svg {{ min-width: 720px; }}
}}
</style>
"""


def plotly_template() -> go.layout.Template:
    t = go.layout.Template()
    axis = dict(gridcolor=LINE_SOFT, zeroline=False, linecolor=LINE, ticks="outside", tickcolor=LINE, ticklen=4,
                tickfont=dict(family="IBM Plex Mono, Consolas, monospace", size=10.5, color=MUTED),
                title=dict(font=dict(family="Inter, sans-serif", size=11.5, color=MUTED), standoff=8))
    t.layout = go.Layout(
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=SERIES,
        margin=dict(l=8, r=12, t=36, b=8),
        title=dict(font=dict(family="Space Grotesk, Inter, sans-serif", size=13.5, color=INK), x=0, xanchor="left", y=0.98),
        xaxis=axis, yaxis={**axis, "linecolor": "rgba(0,0,0,0)"},
        hoverlabel=dict(bgcolor=PETROL_900, bordercolor=PETROL_900, font=dict(color="#FFFFFF", size=12, family="Inter, sans-serif")),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11, family="Inter, sans-serif")),
        bargap=0.3, hovermode="closest",
    )
    return t


pio.templates["methatwin"] = plotly_template()
pio.templates.default = "methatwin"
PLOT_CFG = {"displaylogo": False, "responsive": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
            "toImageButtonOptions": {"format": "png", "scale": 2}}
