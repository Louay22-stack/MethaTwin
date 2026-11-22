"""MethaTwin - design system v3 "Bioluminescent lab": tokens, global CSS and the Plotly template.

Direction: an AI-biotech product. Deep ink surfaces, light emitted by the data rather than painted on
the chrome: a mint → cyan → violet spectrum (living cells → computation) used for the brand, the active
state and primary actions; data colours stay disciplined and validated.
* Surfaces: ink canvas with faint fixed light fields, elevated panels with 1 px hairlines,
  14 px radius, a soft inner top highlight. Glass (backdrop blur) only on the floating app bar.
* Type: Space Grotesk (display, numbers), Inter (text), IBM Plex Mono (labels, units, tags).
* Motion: 180-450 ms ease-out on hover, focus, page entry and flowing process lines;
  all disabled under prefers-reduced-motion.
Chart slots on the #0E1525 surface: teal #14AA82, blue #3D8BF0, coral #E5663A, violet #9175F5
(validator, dark mode: lightness band, chroma floor, CVD dE 19.8, normal-vision and 3:1 contrast all pass).
"""
from __future__ import annotations

import base64
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

ASSETS = Path(__file__).resolve().parent / "assets"

# ---------------------------------------------------------------- tokens ----
BG = "#070B14"            # page
BG_1 = "#0A101C"          # sidebar
SURFACE = "#0E1525"       # panels, chart surface
SURFACE_2 = "#131D31"     # raised / inputs
SURFACE_3 = "#1A2640"
INK = "#E8EEF8"           # primary text (light on dark)
INK_2 = "#AEBBD0"
MUTED = "#72819A"
LINE = "#22304A"
LINE_SOFT = "#18233A"
# brand spectrum (UI light, not data)
MINT = "#5EF2C8"
CYAN = "#56CCF2"
LILAC = "#A78BFA"
GRAD = f"linear-gradient(90deg, {MINT} 0%, {CYAN} 52%, {LILAC} 100%)"
# validated data colours
TEAL = "#14AA82"
BLUE = "#3D8BF0"
CORAL = "#E5663A"
VIOLET = "#9175F5"
BLUE_SOFT = "#2A4F86"
SERIES = [TEAL, BLUE, CORAL, VIOLET]
SEQ = ["#0F1A2C", "#103446", "#0F5257", "#127462", "#1F9A78", "#52C69A", "#B5F3D9"]
# status (always with icon + word)
GOOD, WARN, BAD = "#34D399", "#FBBF24", "#F87171"
GOOD_BG, WARN_BG, BAD_BG = "rgba(52,211,153,.12)", "rgba(251,191,36,.12)", "rgba(248,113,113,.13)"
# compatibility aliases used by the components
PETROL_900, PETROL_600 = SURFACE_2, MINT
MINT_SOFT = "rgba(94,242,200,.10)"
CANVAS = BG
FONT_HEAD = "'Space Grotesk', 'Inter', 'Segoe UI', sans-serif"
FONT_BODY = "'Inter', 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_MONO = "'IBM Plex Mono', 'JetBrains Mono', Consolas, monospace"


def svg_data_uri(name: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {{
  --bg:{BG}; --bg-1:{BG_1}; --surface:{SURFACE}; --surface-2:{SURFACE_2}; --surface-3:{SURFACE_3};
  --ink:{INK}; --ink-2:{INK_2}; --muted:{MUTED}; --line:{LINE}; --line-soft:{LINE_SOFT};
  --mint:{MINT}; --cyan:{CYAN}; --lilac:{LILAC}; --grad:{GRAD};
  --teal:{TEAL}; --blue:{BLUE}; --coral:{CORAL}; --violet:{VIOLET};
  --good:{GOOD}; --warn:{WARN}; --bad:{BAD}; --good-bg:{GOOD_BG}; --warn-bg:{WARN_BG}; --bad-bg:{BAD_BG};
  --f-head:{FONT_HEAD}; --f-body:{FONT_BODY}; --f-mono:{FONT_MONO};
  --r:14px; --r-sm:8px; --ease: cubic-bezier(.22,.8,.24,1);
  --shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 30px -18px rgba(0,0,0,.8);
}}

/* ---------- base ---------- */
html, body, .stApp, button, input, textarea, select, label, p, li, td, th, .stMarkdown, [data-testid="stWidgetLabel"] {{
  font-family: var(--f-body);
}}
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {{
  font-family: "Material Symbols Rounded" !important; letter-spacing: normal !important; text-transform: none !important;
}}
.stApp {{ color: var(--ink);
  background:
    radial-gradient(900px 520px at 8% -6%, rgba(94,242,200,.10), transparent 60%),
    radial-gradient(800px 520px at 96% -10%, rgba(167,139,250,.11), transparent 62%),
    radial-gradient(1200px 700px at 50% 120%, rgba(86,204,242,.05), transparent 60%),
    var(--bg) !important;
  background-attachment: fixed !important; }}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] {{ display:none !important; }}
[data-testid="stHeader"] {{ background: transparent; height: 0; min-height: 0; overflow: visible; }}
[data-testid="stExpandSidebarButton"] {{ position: fixed !important; top: 13px; left: 12px; z-index: 999990; width: 34px !important; height: 32px !important;
  display:flex !important; align-items:center; justify-content:center; background: var(--surface-2) !important;
  border-radius: var(--r-sm); border: 1px solid var(--line); }}
[data-testid="stExpandSidebarButton"] span {{ color: var(--mint) !important; }}
.stApp:has([data-testid="stSidebar"][aria-expanded="false"]) .mt-brand {{ padding-left: 60px !important; }}
.block-container {{ padding: 0 1.8rem 3rem 1.8rem !important; max-width: 1500px; }}
h1, h2, h3, h4 {{ font-family: var(--f-head); color: var(--ink); letter-spacing: -0.01em; }}
p, li {{ color: var(--ink-2); font-size: 0.92rem; line-height: 1.6; }}
strong, b {{ color: var(--ink); }}
a {{ color: var(--cyan); }}
::selection {{ background: rgba(94,242,200,.25); }}
@keyframes mt-in {{ from {{ opacity:0; transform: translateY(6px); }} to {{ opacity:1; transform:none; }} }}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{ animation: mt-in .32s var(--ease) both; }}
*::-webkit-scrollbar {{ width: 10px; height: 10px; }}
*::-webkit-scrollbar-thumb {{ background: #1F2B44; border-radius: 10px; border: 2px solid var(--bg); }}
*::-webkit-scrollbar-track {{ background: transparent; }}

/* ---------- floating application bar ---------- */
.mt-appbar {{ position: relative; margin: 12px 0 0 0; width: 100%;
  background: rgba(14,21,37,.72); backdrop-filter: blur(14px) saturate(140%); -webkit-backdrop-filter: blur(14px) saturate(140%);
  border: 1px solid var(--line); border-radius: var(--r); color: var(--ink);
  display:flex; align-items:center; min-height: 58px; box-shadow: var(--shadow); overflow: hidden; }}
.mt-appbar::after {{ content:""; position:absolute; left:0; right:0; bottom:0; height:1px; background: var(--grad); opacity:.55; }}
.mt-brand {{ display:flex; align-items:center; gap:11px; padding: 0 20px 0 18px; height: 58px; border-right: 1px solid var(--line); }}
.mt-brand img {{ width:30px; height:30px; filter: drop-shadow(0 0 10px rgba(94,242,200,.35)); }}
.mt-brand .nm {{ font-family: var(--f-head); font-weight:600; font-size: 1.14rem; letter-spacing:-0.01em; color: var(--ink); }}
.mt-brand .nm span {{ background: var(--grad); -webkit-background-clip: text; background-clip: text; color: transparent; font-weight: 600; }}
.mt-brand .ver {{ font-family: var(--f-mono); font-size: .6rem; color: var(--mint); border:1px solid rgba(94,242,200,.35);
  background: rgba(94,242,200,.07); padding: 1px 6px; border-radius: 999px; margin-left: 2px; letter-spacing:.04em; }}
.mt-appbar-right {{ margin-left:auto; display:flex; align-items:center; gap: 8px; padding: 0 14px; flex-wrap: nowrap; }}
.mt-status {{ font-family: var(--f-mono); font-size: .66rem; letter-spacing:.06em; text-transform: uppercase; color: var(--ink-2);
  display:flex; align-items:center; gap:7px; white-space:nowrap; padding: 5px 10px; border-radius: 999px;
  background: var(--surface-2); border: 1px solid var(--line); }}
.mt-dot {{ width:7px; height:7px; border-radius:50%; background: var(--good); animation: mt-pulse 2.2s var(--ease) infinite; }}
.mt-dot.warn {{ background: var(--warn); }}
.mt-dot.bad {{ background: var(--bad); }}
@keyframes mt-pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(94,242,200,.45); }} 70% {{ box-shadow: 0 0 0 7px rgba(94,242,200,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(94,242,200,0); }} }}

/* ---------- navigation (segmented pill rail) ---------- */
.st-key-mtnav {{ margin: 10px 0 0 0; padding: 4px; width: fit-content !important; max-width: 100%;
  background: var(--surface); border: 1px solid var(--line); border-radius: 999px; overflow-x: auto; overflow-y: hidden; scrollbar-width: none; }}
.st-key-mtnav::-webkit-scrollbar {{ display:none; }}
.st-key-mtnav [data-testid="stHorizontalBlock"] {{ gap: 2px !important; flex-wrap: nowrap !important; }}
.st-key-mtnav [data-testid="stHorizontalBlock"] > div {{ flex: 0 0 auto !important; width:auto !important; min-width:0 !important; }}
.st-key-mtnav [data-testid="stPageLink"] a {{ border-radius: 999px !important; padding: 8px 16px !important; margin:0 !important;
  background: transparent !important; transition: background .2s var(--ease), box-shadow .2s var(--ease); }}
.st-key-mtnav [data-testid="stPageLink"] a p, .st-key-mtnav [data-testid="stPageLink"] a span {{ font-family: var(--f-body) !important; font-size: .82rem !important;
  font-weight: 500; color: var(--ink-2) !important; white-space: nowrap; letter-spacing: 0; }}
.st-key-mtnav [data-testid="stPageLink"] a:hover {{ background: var(--surface-2) !important; }}
.st-key-mtnav [data-testid="stPageLink"] a:hover p {{ color: var(--ink) !important; }}
.st-key-mtnav [data-testid="stPageLink"] a[aria-current="page"] {{ background: linear-gradient(180deg, rgba(94,242,200,.16), rgba(86,204,242,.08)) !important;
  box-shadow: inset 0 0 0 1px rgba(94,242,200,.35), 0 0 18px -6px rgba(94,242,200,.5); }}
.st-key-mtnav [data-testid="stPageLink"] a[aria-current="page"] p, .st-key-mtnav [data-testid="stPageLink"] a[aria-current="page"] span {{ color: var(--mint) !important; font-weight: 600; }}
/* in-page action links */
.st-key-nextsteps [data-testid="stPageLink"] a {{ border: 1px solid var(--line); border-radius: var(--r-sm); background: var(--surface); padding: 10px 14px;
  transition: border-color .2s var(--ease), background .2s var(--ease), transform .2s var(--ease); }}
.st-key-nextsteps [data-testid="stPageLink"] a:hover {{ border-color: rgba(94,242,200,.5); background: var(--surface-2); transform: translateY(-1px); }}
.st-key-nextsteps [data-testid="stPageLink"] a p {{ font-weight: 500; color: var(--ink); font-size: .86rem; }}

/* ---------- page header ---------- */
.mt-pagehead {{ display:flex; align-items:flex-end; justify-content:space-between; gap:24px; padding: 26px 0 18px 0; margin-bottom: 14px; }}
.mt-crumb {{ font-family: var(--f-mono); font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; color: var(--muted); margin-bottom:8px;
  display:flex; align-items:center; gap:8px; }}
.mt-crumb::before {{ content:""; width:18px; height:1px; background: var(--grad); }}
.mt-crumb b {{ color: var(--mint); font-weight:500; }}
.mt-title {{ font-family: var(--f-head); font-size: 1.85rem; font-weight: 600; color: var(--ink); line-height:1.12; letter-spacing:-0.025em; }}
.mt-title em {{ font-style: normal; background: var(--grad); -webkit-background-clip: text; background-clip: text; color: transparent; }}
.mt-lede {{ color: var(--ink-2); font-size: .92rem; max-width: 780px; margin-top: 8px; line-height:1.6; }}
.mt-head-meta {{ font-family: var(--f-mono); font-size:.68rem; color: var(--muted); text-align:right; line-height:1.8; white-space:nowrap;
  padding: 8px 12px; border:1px solid var(--line); border-radius: var(--r-sm); background: rgba(14,21,37,.6); }}
.mt-head-meta b {{ color: var(--ink); font-weight:500; }}

/* ---------- section label ---------- */
.mt-sec {{ display:flex; align-items:center; gap:12px; margin: 30px 0 12px 0; }}
.mt-sec .idx {{ font-family: var(--f-mono); font-size:.66rem; color: var(--bg); background: var(--grad); letter-spacing:.04em;
  padding: 2px 7px; border-radius: 999px; font-weight:600; }}
.mt-sec .t {{ font-family: var(--f-head); font-weight:600; font-size: 1.08rem; color: var(--ink); letter-spacing:-0.01em; }}
.mt-sec::after {{ content:""; order: 2; flex: 1; height:1px; background: linear-gradient(90deg, var(--line), transparent); }}
.mt-sec .s {{ order: 3; color: var(--muted); font-size: .8rem; text-align:right; }}

/* ---------- verdict ---------- */
.mt-verdict {{ display:flex; align-items:stretch; border:1px solid var(--line); background: var(--surface); border-radius: var(--r); overflow:hidden;
  box-shadow: var(--shadow); position: relative; }}
.mt-verdict::before {{ content:""; position:absolute; inset:0; background: radial-gradient(500px 120px at 0% 50%, rgba(52,211,153,.10), transparent 70%); pointer-events:none; }}
.mt-verdict.warn::before {{ background: radial-gradient(500px 120px at 0% 50%, rgba(251,191,36,.10), transparent 70%); }}
.mt-verdict.bad::before {{ background: radial-gradient(500px 120px at 0% 50%, rgba(248,113,113,.12), transparent 70%); }}
.mt-verdict .flag {{ width: 3px; background: var(--good); box-shadow: 0 0 14px var(--good); }}
.mt-verdict.warn .flag {{ background: var(--warn); box-shadow: 0 0 14px var(--warn); }}
.mt-verdict.bad .flag {{ background: var(--bad); box-shadow: 0 0 14px var(--bad); }}
.mt-verdict .body {{ padding: 13px 18px; display:flex; gap: 14px; align-items:center; flex-wrap: wrap; width:100%; position:relative; }}
.mt-verdict .tag {{ font-family: var(--f-mono); font-size: .66rem; letter-spacing:.08em; text-transform: uppercase; font-weight:600;
  padding: 4px 10px; border-radius: 999px; background: var(--good-bg); color: var(--good); white-space:nowrap; border:1px solid rgba(52,211,153,.3); }}
.mt-verdict.warn .tag {{ background: var(--warn-bg); color: var(--warn); border-color: rgba(251,191,36,.3); }}
.mt-verdict.bad .tag {{ background: var(--bad-bg); color: var(--bad); border-color: rgba(248,113,113,.3); }}
.mt-verdict .msg {{ color: var(--ink-2); font-size: .9rem; flex: 1 1 380px; }}

/* ---------- KPI tiles ---------- */
.mt-kpis {{ display:grid; grid-template-columns: repeat(var(--n, 5), minmax(0,1fr)); gap: 10px; margin: 12px 0 4px 0; }}
.mt-kpi {{ position: relative; padding: 15px 16px 14px 16px; min-width: 0; background: var(--surface); border:1px solid var(--line);
  border-radius: var(--r); box-shadow: var(--shadow); overflow:hidden; transition: border-color .25s var(--ease), transform .25s var(--ease); }}
.mt-kpi::after {{ content:""; position:absolute; left:16px; right:16px; top:0; height:1px; background: var(--c, var(--mint)); opacity:.75;
  box-shadow: 0 0 12px var(--c, var(--mint)); }}
.mt-kpi:hover {{ border-color: #2C3D5E; transform: translateY(-2px); }}
.mt-kpi .l {{ font-family: var(--f-mono); font-size:.63rem; letter-spacing:.1em; text-transform: uppercase; color: var(--muted);
  display:flex; align-items:center; gap:7px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mt-kpi .l i {{ width:6px; height:6px; border-radius:50%; display:inline-block; flex: none; }}
.mt-kpi .v {{ font-family: var(--f-head); font-size: 1.85rem; font-weight: 600; color: var(--ink); letter-spacing:-0.03em; margin-top: 8px;
  font-variant-numeric: tabular-nums; white-space:nowrap; line-height: 1.05; }}
.mt-kpi .v small {{ font-family: var(--f-mono); font-size:.7rem; font-weight:500; color: var(--muted); margin-left: 6px; letter-spacing:0; }}
.mt-kpi .d {{ font-size:.78rem; color: var(--ink-2); margin-top: 6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mt-kpi .d.good {{ color: var(--good); font-weight:500; }}
.mt-kpi .d.bad {{ color: var(--bad); font-weight:500; }}
.mt-kpi .d.warn {{ color: var(--warn); font-weight:500; }}
@media (max-width: 1100px) {{ .mt-kpis {{ grid-template-columns: repeat(3, minmax(0,1fr)); }} }}
@media (max-width: 640px) {{ .mt-kpis {{ grid-template-columns: repeat(2, minmax(0,1fr)); }} .mt-kpi .v {{ font-size: 1.4rem; }} }}

/* ---------- panels ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: var(--r) !important; border-color: var(--line) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,0)), var(--surface); box-shadow: var(--shadow);
  transition: border-color .25s var(--ease); }}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{ border-color: #2A3A58 !important; }}
.mt-ph {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; margin: -2px 0 10px 0; }}
.mt-ph .t {{ font-family: var(--f-head); font-weight: 600; font-size: 1rem; color: var(--ink); }}
.mt-ph .s {{ font-family: var(--f-mono); font-size: .64rem; letter-spacing:.08em; text-transform: uppercase; color: var(--muted); text-align:right; }}

/* ---------- constraint / spec table ---------- */
.mt-scroll {{ width:100%; overflow-x:auto; -webkit-overflow-scrolling: touch; }}
.mt-spec {{ width:100%; border-collapse: collapse; font-size: .86rem; border:none !important; }}
.mt-spec tr, .mt-spec tr:nth-child(even) {{ background: transparent !important; border: none !important; }}
.mt-spec tr:hover td {{ background: rgba(255,255,255,.025) !important; }}
.mt-spec th {{ font-family: var(--f-mono); font-size:.62rem; letter-spacing:.1em; text-transform: uppercase; color: var(--muted) !important; font-weight:500;
  text-align:left; padding: 0 8px 8px 0 !important; border:none !important; border-bottom: 1px solid var(--line) !important; background: transparent !important; }}
.mt-spec td {{ padding: 9px 8px 9px 0 !important; border:none !important; border-bottom: 1px solid var(--line-soft) !important; vertical-align: middle;
  color: var(--ink); background: transparent !important; transition: background .18s var(--ease); }}
.mt-spec td.n {{ color: var(--ink-2); }}
.mt-spec td.v {{ font-family: var(--f-mono); font-weight: 500; text-align:right; white-space:nowrap; font-variant-numeric: tabular-nums; color: var(--ink); }}
.mt-spec td.bar {{ width: 30%; min-width: 90px; padding-top: 11px !important; }}
.mt-spec td.bar .lt {{ font-family: var(--f-mono); font-size:.64rem; color: var(--muted); margin-top: 6px; white-space: nowrap; }}
.mt-spec td.st {{ text-align:right; white-space:nowrap; width:1%; }}
.mt-gauge {{ position:relative; height: 5px; background: var(--surface-3); border-radius: 999px; overflow: visible; }}
.mt-gauge .fill {{ position:absolute; left:0; top:0; bottom:0; border-radius:999px; background: linear-gradient(90deg, #0F7F64, var(--mint));
  box-shadow: 0 0 10px rgba(94,242,200,.35); transition: width .45s var(--ease); }}
.mt-gauge .fill.warn {{ background: linear-gradient(90deg, #8A6410, var(--warn)); box-shadow: 0 0 10px rgba(251,191,36,.3); }}
.mt-gauge .fill.bad {{ background: linear-gradient(90deg, #8E2E2E, var(--bad)); box-shadow: 0 0 10px rgba(248,113,113,.35); }}
.mt-gauge .lim {{ position:absolute; top:-4px; width: 2px; height: 13px; background: var(--ink); border-radius: 2px; }}
.st-chip {{ display:inline-flex; align-items:center; gap:5px; font-family: var(--f-mono); font-size:.62rem; letter-spacing:.07em; text-transform: uppercase;
  font-weight:600; padding: 3px 9px; border-radius: 999px; border: 1px solid transparent; }}
.st-chip.ok {{ background: var(--good-bg); color: var(--good); border-color: rgba(52,211,153,.25); }}
.st-chip.warn {{ background: var(--warn-bg); color: var(--warn); border-color: rgba(251,191,36,.25); }}
.st-chip.bad {{ background: var(--bad-bg); color: var(--bad); border-color: rgba(248,113,113,.28); }}
.st-chip.info {{ background: var(--surface-2); color: var(--ink-2); border-color: var(--line); }}

/* ---------- process flow diagram ---------- */
.mt-pfd {{ width:100%; background: radial-gradient(700px 260px at 50% 40%, rgba(86,204,242,.06), transparent 70%), var(--surface);
  border:1px solid var(--line); border-radius: var(--r); padding: 8px 6px 4px 6px; box-shadow: var(--shadow); }}
.mt-pfd svg {{ width:100%; height:auto; display:block; }}
.mt-pfd svg .unit {{ cursor: help; }}
.mt-pfd svg .unit .box {{ transition: stroke .2s var(--ease), filter .2s var(--ease); }}
.mt-pfd svg .unit:hover .box {{ stroke: {MINT}; filter: drop-shadow(0 0 8px rgba(94,242,200,.45)); }}
.mt-pfd svg .flow {{ stroke-dasharray: 7 6; animation: mt-flow 1.4s linear infinite; }}
@keyframes mt-flow {{ to {{ stroke-dashoffset: -26; }} }}
.mt-legend {{ display:flex; gap: 18px; flex-wrap: wrap; font-family: var(--f-mono); font-size: .64rem; letter-spacing:.07em;
  text-transform: uppercase; color: var(--muted); margin: 8px 4px 0 4px; }}
.mt-legend span {{ display:inline-flex; align-items:center; gap:7px; }}
.mt-legend i {{ width: 18px; height: 3px; display:inline-block; border-radius:3px; }}

/* ---------- empty / info states ---------- */
.mt-empty {{ border: 1px dashed #2A3A58; border-radius: var(--r); padding: 36px 20px; text-align:center;
  background: radial-gradient(400px 140px at 50% 0%, rgba(94,242,200,.06), transparent 70%), var(--surface); }}
.mt-empty .t {{ font-family: var(--f-head); font-weight:600; color: var(--ink); font-size: 1.05rem; }}
.mt-empty .s {{ color: var(--muted); font-size: .88rem; margin-top: 6px; }}
.mt-note {{ font-size: .8rem; color: var(--muted); margin-top: 8px; line-height: 1.55; }}
.mt-note b {{ color: var(--ink-2); }}
.mt-callout {{ border: 1px solid rgba(94,242,200,.22); background: rgba(94,242,200,.06); padding: 11px 15px; border-radius: var(--r-sm);
  font-size: .86rem; color: var(--ink-2); margin: 10px 0; }}
.mt-callout.blue {{ border-color: rgba(86,204,242,.25); background: rgba(86,204,242,.07); }}
.mt-callout.warn {{ border-color: rgba(251,191,36,.28); background: rgba(251,191,36,.07); }}
.mt-kv {{ display:grid; grid-template-columns: auto 1fr; gap: 8px 16px; font-size: .86rem; }}
.mt-kv dt {{ font-family: var(--f-mono); font-size: .64rem; letter-spacing:.09em; text-transform:uppercase; color: var(--muted); padding-top: 3px; }}
.mt-kv dd {{ margin:0; color: var(--ink); }}

/* ---------- sidebar = design console ---------- */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #0B1220 0%, var(--bg-1) 100%) !important; border-right: 1px solid var(--line); }}
[data-testid="stSidebar"][aria-expanded="true"] {{ min-width: 304px !important; }}
[data-testid="stSidebarUserContent"] {{ padding: 0 1.15rem 2rem 1.15rem !important; }}
.mt-console-head {{ margin: 0 0 14px 0; padding: 14px 14px 13px 14px; border-radius: var(--r); position: relative; overflow:hidden;
  background: radial-gradient(260px 120px at 100% 0%, rgba(167,139,250,.22), transparent 70%),
              radial-gradient(260px 120px at 0% 100%, rgba(94,242,200,.18), transparent 70%), var(--surface-2);
  border: 1px solid var(--line); }}
.mt-console-head .k {{ font-family: var(--f-mono); font-size: .62rem; letter-spacing:.12em; text-transform: uppercase; color: var(--mint); }}
.mt-console-head .t {{ font-family: var(--f-head); font-size: 1.08rem; font-weight: 600; margin-top: 3px; color: var(--ink); }}
.mt-console-head .s {{ font-size: .78rem; color: var(--ink-2); margin-top: 3px; }}
.mt-group {{ display:flex; align-items:center; gap:8px; margin: 18px 0 6px 0; font-family: var(--f-mono); font-size: .64rem; letter-spacing:.1em;
  text-transform: uppercase; color: var(--ink-2); font-weight: 500; }}
.mt-group::after {{ content:""; flex:1; height:1px; background: linear-gradient(90deg, var(--line), transparent); }}
.mt-group .n {{ color: var(--mint); }}
.mt-derived {{ display:flex; justify-content:space-between; font-family: var(--f-mono); font-size:.72rem; color: var(--muted); padding: 5px 10px;
  border-radius: var(--r-sm); background: rgba(255,255,255,.025); border: 1px solid var(--line-soft); margin: 2px 0 6px 0; }}
.mt-derived b {{ color: var(--ink); font-weight:500; }}
.mt-mod {{ display:inline-block; font-family: var(--f-mono); font-size:.58rem; letter-spacing:.07em; text-transform: uppercase; color: #FFB08F;
  border: 1px solid rgba(229,102,58,.5); background: rgba(229,102,58,.10); border-radius: 999px; padding: 0 7px; margin-left: 6px; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ font-size: .82rem !important; color: var(--ink-2) !important; font-weight: 500; }}
[data-testid="stSliderThumbValue"] {{ font-family: var(--f-mono) !important; font-size: .7rem !important; color: var(--mint) !important; }}
[data-testid="stSlider"] [role="slider"] {{ box-shadow: 0 0 0 4px rgba(94,242,200,.15), 0 0 14px rgba(94,242,200,.5) !important; transition: box-shadow .2s var(--ease); }}
[data-testid="stSlider"] [role="slider"]:hover {{ box-shadow: 0 0 0 6px rgba(94,242,200,.2), 0 0 18px rgba(94,242,200,.7) !important; }}

/* ---------- widgets ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stPopover"] button {{ border-radius: var(--r-sm) !important; font-weight: 500;
  border: 1px solid var(--line) !important; background: var(--surface-2) !important; color: var(--ink) !important;
  transition: border-color .2s var(--ease), box-shadow .2s var(--ease), transform .2s var(--ease); font-size: .86rem; }}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stPopover"] button:hover {{ border-color: rgba(94,242,200,.55) !important;
  box-shadow: 0 0 0 3px rgba(94,242,200,.08); }}
.stButton > button p, .stDownloadButton > button p {{ color: inherit !important; }}
[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  background: var(--grad) !important; border: none !important; color: #04121A !important; font-weight: 600 !important;
  box-shadow: 0 6px 22px -10px rgba(94,242,200,.8) !important; }}
[data-testid="stBaseButton-primary"] p {{ color: #04121A !important; font-weight: 600; }}
[data-testid="stBaseButton-primary"]:hover {{ transform: translateY(-1px); box-shadow: 0 10px 26px -10px rgba(94,242,200,.95) !important; filter: brightness(1.06); }}
[data-testid="stBaseButton-primary"]:disabled, .stButton > button:disabled {{ background: var(--surface-2) !important; color: var(--muted) !important;
  box-shadow: none !important; border: 1px solid var(--line) !important; cursor: not-allowed; transform:none; filter:none; }}
[data-testid="stBaseButton-primary"]:disabled p {{ color: var(--muted) !important; }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--line); border-radius: var(--r-sm); overflow: hidden; }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-testid="stTextInput"] input {{ border-radius: var(--r-sm) !important;
  background: var(--surface-2) !important; border-color: var(--line) !important; }}
[data-baseweb="select"] > div:hover {{ border-color: #2C3D5E !important; }}
[data-testid="stSegmentedControl"] button, [data-testid="stPills"] button {{ border-radius: 999px !important; transition: all .2s var(--ease); }}
[data-testid="stBaseButton-pillsActive"], [data-testid="stBaseButton-segmented_controlActive"] {{
  background: rgba(94,242,200,.12) !important; border-color: rgba(94,242,200,.5) !important; color: var(--mint) !important; }}
[data-testid="stBaseButton-pillsActive"] p, [data-testid="stBaseButton-segmented_controlActive"] p {{ color: var(--mint) !important; }}
[data-testid="stExpander"] details {{ border-radius: var(--r-sm) !important; border-color: var(--line) !important; background: rgba(14,21,37,.7); }}
[data-testid="stExpander"] summary:hover p {{ color: var(--mint); }}
[data-testid="stExpander"] summary p {{ font-weight: 600; color: var(--ink); font-size: .86rem; transition: color .2s var(--ease); }}
[data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid var(--line); }}
[data-testid="stTabs"] [data-baseweb="tab"] p {{ font-weight: 500; }}
[data-testid="stTabs"] [aria-selected="true"] p {{ color: var(--mint) !important; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background: var(--grad) !important; height: 2px; }}
[data-testid="stToast"] {{ border-radius: var(--r-sm); border: 1px solid rgba(94,242,200,.3); background: var(--surface-2) !important; }}
[data-testid="stDialog"] [role="dialog"] {{ border-radius: var(--r) !important; border: 1px solid var(--line); background: var(--surface) !important;
  box-shadow: 0 30px 80px -20px rgba(0,0,0,.9), 0 0 0 1px rgba(94,242,200,.08); }}
[data-testid="stImage"] img {{ border-radius: var(--r-sm); }}
[data-testid="stCaptionContainer"] p {{ color: var(--muted) !important; }}

.mt-foot {{ display:flex; justify-content:space-between; gap: 16px; flex-wrap: wrap; font-family: var(--f-mono); font-size:.62rem; letter-spacing:.08em;
  text-transform: uppercase; color: var(--muted); margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--line); }}

@media (prefers-reduced-motion: reduce) {{
  .mt-pfd svg .flow, .mt-dot, [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{ animation: none !important; }}
  .mt-kpi:hover, .st-key-nextsteps [data-testid="stPageLink"] a:hover {{ transform: none; }}
}}
@media (max-width: 760px) {{
  .block-container {{ padding: 0 .9rem 2rem .9rem !important; }}
  .mt-appbar {{ margin-top: 8px; }}
  .mt-brand {{ border-right: none; }}
  .mt-status:not(:first-child) {{ display:none; }}
  .mt-status span.txt {{ display:none; }}
  .mt-pagehead {{ flex-direction: column; align-items: flex-start; padding-top: 18px; }}
  .mt-title {{ font-size: 1.45rem; }}
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
    axis = dict(gridcolor="rgba(148,163,184,0.09)", zeroline=False, linecolor=LINE, ticks="outside", tickcolor=LINE, ticklen=4,
                tickfont=dict(family="IBM Plex Mono, Consolas, monospace", size=10.5, color=MUTED),
                title=dict(font=dict(family="Inter, sans-serif", size=11.5, color=MUTED), standoff=8))
    t.layout = go.Layout(
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=SERIES,
        margin=dict(l=8, r=12, t=36, b=8),
        title=dict(font=dict(family="Space Grotesk, Inter, sans-serif", size=14, color=INK), x=0, xanchor="left", y=0.98),
        xaxis=axis, yaxis={**axis, "linecolor": "rgba(0,0,0,0)"},
        hoverlabel=dict(bgcolor=SURFACE_3, bordercolor=MINT, font=dict(color=INK, size=12, family="Inter, sans-serif")),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11, family="Inter, sans-serif", color=INK_2)),
        bargap=0.3, hovermode="closest",
    )
    return t


pio.templates["methatwin"] = plotly_template()
pio.templates.default = "methatwin"
PLOT_CFG = {"displaylogo": False, "responsive": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
            "toImageButtonOptions": {"format": "png", "scale": 2}}
