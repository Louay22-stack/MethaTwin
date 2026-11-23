"""MethaTwin design system v4 "Signal": brand marks, global CSS and the Plotly template.

Direction: a dark, quiet, precise instrument. Warm graphite surfaces, one electric-amber signal for the brand,
the primary action, the current position and keyboard focus. Two fonts: Sora (display) and Manrope (text).
Depth comes from tone steps, not glow, gradients or blur. Every value comes from tokens.py; the component
rules below use CSS custom properties only.
"""
from __future__ import annotations

import base64
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

import tokens as K

ASSETS = Path(__file__).resolve().parent / "assets"
R = K.resolve

# Python-side colours (Plotly, inline SVG) resolved from semantic / component tokens
INK, INK_2, MUTED = R("text-primary"), R("text-secondary"), R("text-muted")
CANVAS, SURFACE, RAISED, SUNKEN = R("surface-canvas"), R("surface-card"), R("surface-raised"), R("surface-sunken")
LINE, CONTROL = R("border-subtle"), R("border-control")
ACCENT, ON_ACCENT = R("accent"), R("text-on-accent")
GOOD, WARN, BAD = R("status-ok-fg"), R("status-warn-fg"), R("status-bad-fg")
D1, D2, D3, D4, DMUTED = R("data-1"), R("data-2"), R("data-3"), R("data-4"), R("data-muted")
SERIES = [D1, D2, D3, D4]
# sequential ramp for maps (graphite -> amber), all steps distinguishable on the card surface
SEQ = ["#2A2620", "#4A3B1E", "#73561A", "#A27414", "#D3930F", "#FFB224", "#FFD98A"]
FONT_DISPLAY = "Sora, Manrope, Segoe UI, sans-serif"
FONT_BODY = "Manrope, Segoe UI, sans-serif"


# ------------------------------------------------------------------------------------------ brand marks ---
def mark_paths(color: str, small: bool = False) -> str:
    """The twin monogram: a solid stroke (the real plant) mirrored by a dotted blueprint stroke (its twin),
    meeting at one node. `small` thickens the dotted stroke so it survives below ~24 px."""
    dot_w, dot_gap, ghost = (4.6, 7.2, 2.0) if small else (3.0, 6.5, 1.4)
    return (f'<path d="M10 52V14l18 24" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M36 38l18-24v38" fill="none" stroke="{color}" stroke-width="{ghost}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity=".45"/>'
            f'<path d="M36 38l18-24v38" fill="none" stroke="{color}" stroke-width="{dot_w}" stroke-linecap="round" '
            f'stroke-linejoin="round" stroke-dasharray="0.1 {dot_gap}"/>'
            f'<circle cx="32" cy="40" r="5" fill="{color}"/>')


def mark_svg(color: str = ACCENT, small: bool = False, tile: str | None = None) -> str:
    if tile:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{tile}"/>'
                f'<g transform="translate(6 5) scale(.82)">{mark_paths(color, small)}</g></svg>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="6 10.5 52 45">{mark_paths(color, small)}</svg>'


def data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def wordmark(size: str = "1.25rem", small: bool = True) -> str:
    """HTML lockup: the amber M glyph replaces the M of MethaTwin (read as one word by screen readers)."""
    glyph = (f'<svg viewBox="6 10.5 52 45" aria-hidden="true" class="mt-wm-m">{mark_paths("currentColor", small)}</svg>')
    return (f'<span class="mt-wordmark" role="img" aria-label="MethaTwin" style="font-size:{size}">'
            f'{glyph}<span aria-hidden="true">ethaTwin</span></span>')


FAVICON = ASSETS / "app-icon.svg"

# --------------------------------------------------------------------------------------------- CSS ---
_GLYPH_URI = data_uri(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="6 10.5 52 45">{mark_paths(ACCENT, True)}</svg>')

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap');
""" + K.css_vars() + """

/* ================================================================ base */
html, body, .stApp, button, input, textarea, select, label, p, li, td, th, .stMarkdown, [data-testid="stWidgetLabel"] {
  font-family: var(--font-body);
}
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {
  font-family: "Material Symbols Rounded" !important; letter-spacing: normal !important; text-transform: none !important;
}
.stApp { background: var(--page-bg) !important; color: var(--text-primary); }
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stToolbar"],
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; height: 0; min-height: 0; }
.block-container { padding: 0 var(--space-8) var(--space-12) !important; max-width: 1240px; }
h1, h2, h3, h4 { font-family: var(--font-display); color: var(--text-primary); letter-spacing: -0.02em; }
p, li { color: var(--text-secondary); font-size: var(--text-md); line-height: 1.6; }
strong, b { color: var(--text-primary); font-weight: var(--weight-semibold); }
a { color: var(--accent); }
::selection { background: var(--accent-subtle); color: var(--text-primary); }
.mt-num { font-variant-numeric: tabular-nums; }
:focus-visible, a:focus-visible, button:focus-visible, summary:focus-visible, [role="slider"]:focus-visible,
input:focus-visible, [tabindex]:focus-visible {
  outline: 3px solid var(--focus-ring) !important; outline-offset: 2px !important; border-radius: var(--radius-control);
}
@keyframes mt-rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.mt-rise { animation: mt-rise var(--motion-slow) var(--motion-ease) both; }
.sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }

/* ================================================================ wordmark */
.mt-wordmark { display: inline-flex; align-items: baseline; font-family: var(--font-display); font-weight: var(--weight-semibold);
  letter-spacing: -0.03em; color: var(--text-primary); white-space: nowrap; line-height: 1; }
.mt-wordmark .mt-wm-m { height: .72em; width: auto; margin-right: .03em; color: var(--accent); overflow: visible; }

/* ================================================================ top bar */
.st-key-topbar { position: sticky; top: 0; z-index: 990; background: var(--topbar-bg); border-bottom: 1px solid var(--topbar-border);
  margin: 0 calc(-1 * var(--space-8)) var(--space-2); padding: var(--space-3) var(--space-8) !important; gap: var(--space-4) !important;
  flex-wrap: nowrap !important; }
.st-key-brand { flex: 0 0 auto !important; width: auto !important; }
.st-key-brand [data-testid="stPageLink"] a { padding: 6px 8px !important; margin: 0 !important; border-radius: var(--radius-control); background: transparent !important; }
.st-key-brand [data-testid="stPageLink"] a p, .st-key-brand [data-testid="stPageLink"] a span {
  font-family: var(--font-display) !important; font-weight: var(--weight-semibold) !important; font-size: 1.3rem !important;
  letter-spacing: -0.03em; color: var(--text-primary) !important; line-height: 1; }
.st-key-brand [data-testid="stPageLink"] a p::first-letter { color: transparent; }
.st-key-brand [data-testid="stPageLink"] a { position: relative; }
.st-key-brand [data-testid="stPageLink"] a::before { content: ""; position: absolute; left: 8px; top: 50%; width: 1.05rem; height: .92rem;
  transform: translateY(-58%); background: url(\"""" + _GLYPH_URI + """\") no-repeat left center / contain; pointer-events: none; }
/* navigation rail */
.st-key-navrail { justify-content: safe center; gap: var(--space-1) !important; flex-wrap: nowrap !important;
  overflow-x: auto; scrollbar-width: none; }
.st-key-navrail::-webkit-scrollbar { display: none; }
.st-key-navrail > div { flex: 0 0 auto !important; width: auto !important; }
.st-key-navrail [data-testid="stPageLink"] a { border-radius: var(--radius-round) !important; padding: 8px 14px !important; margin: 0 !important;
  min-height: 40px; background: transparent !important; transition: background var(--motion-base) var(--motion-ease); }
.st-key-navrail [data-testid="stPageLink"] a p, .st-key-navrail [data-testid="stPageLink"] a span {
  font-size: var(--text-sm) !important; font-weight: var(--weight-semibold); color: var(--nav-item-fg) !important; white-space: nowrap; }
.st-key-navrail [data-testid="stPageLink"] a:hover { background: var(--nav-item-hover-bg) !important; }
.st-key-navrail [data-testid="stPageLink"] a:hover p { color: var(--text-primary) !important; }
.st-key-navrail [data-testid="stPageLink"] a[aria-current="page"] { background: var(--nav-item-active-bg) !important; }
.st-key-navrail [data-testid="stPageLink"] a[aria-current="page"] p,
.st-key-navrail [data-testid="stPageLink"] a[aria-current="page"] span { color: var(--nav-item-active-fg) !important; }
.st-key-navmenu { display: none !important; flex: 0 0 auto !important; width: auto !important; }
.st-key-navmenu button { min-height: 44px; }
/* current-design chip */
.st-key-chip { flex: 0 0 auto !important; width: auto !important; gap: var(--space-1) !important; align-items: center;
  background: var(--chip-bg); border: 1px solid var(--chip-border); border-radius: var(--radius-round); padding: 2px 4px 2px 12px !important; }
.mt-chip { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); color: var(--chip-fg); white-space: nowrap; }
.mt-chip b { color: var(--text-primary); font-weight: var(--weight-semibold); }
.mt-chip .mod { font-size: var(--text-xs); color: var(--status-warn-fg); border: 1px solid var(--status-warn-border); border-radius: var(--radius-round); padding: 0 8px; }
.st-key-chip [data-testid="stPageLink"] a { border-radius: var(--radius-round) !important; padding: 6px 12px !important; margin: 0 !important;
  background: var(--surface-raised) !important; min-height: 36px; }
.st-key-chip [data-testid="stPageLink"] a p { font-size: var(--text-sm) !important; font-weight: var(--weight-semibold); color: var(--accent) !important; }

/* ================================================================ page head */
.mt-head { padding: var(--space-10) 0 var(--space-6); max-width: 820px; }
.mt-eyebrow { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); font-weight: var(--weight-bold);
  letter-spacing: .14em; text-transform: uppercase; color: var(--accent); }
.mt-eyebrow svg { width: 16px; height: 16px; }
.mt-title { font-family: var(--font-display); font-weight: var(--weight-semibold); font-size: clamp(1.8rem, 3.4vw, 2.6rem);
  line-height: 1.12; letter-spacing: -0.03em; color: var(--text-primary); margin-top: var(--space-3); }
.mt-lede { font-size: var(--text-lg); color: var(--text-secondary); line-height: 1.6; margin-top: var(--space-3); }

/* ================================================================ verdict */
.mt-verdict { display: flex; gap: var(--space-4); align-items: flex-start; background: var(--verdict-bg); border: 1px solid var(--verdict-ok-border);
  border-radius: var(--radius-card); padding: var(--space-5) var(--space-6); }
.mt-verdict.warn { border-color: var(--verdict-warn-border); } .mt-verdict.bad { border-color: var(--verdict-bad-border); }
.mt-verdict.info { border-color: var(--border-control); }
.mt-verdict .ic { flex: none; width: 44px; height: 44px; border-radius: var(--radius-md); display: grid; place-items: center;
  background: var(--status-ok-bg); color: var(--status-ok-fg); }
.mt-verdict.warn .ic { background: var(--status-warn-bg); color: var(--status-warn-fg); }
.mt-verdict.bad .ic { background: var(--status-bad-bg); color: var(--status-bad-fg); }
.mt-verdict.info .ic { background: var(--accent-subtle); color: var(--accent); }
.mt-verdict .ic svg { width: 24px; height: 24px; }
.mt-verdict .k { font-size: var(--text-xs); font-weight: var(--weight-bold); letter-spacing: .12em; text-transform: uppercase; color: var(--status-ok-fg); }
.mt-verdict.warn .k { color: var(--status-warn-fg); } .mt-verdict.bad .k { color: var(--status-bad-fg); } .mt-verdict.info .k { color: var(--accent); }
.mt-verdict .t { font-family: var(--verdict-title-font); font-size: var(--text-xl); font-weight: var(--weight-semibold); color: var(--text-primary);
  letter-spacing: -0.02em; margin-top: 2px; line-height: 1.25; }
.mt-verdict .m { color: var(--text-secondary); margin-top: var(--space-1); font-size: var(--text-md); line-height: 1.55; }

/* ================================================================ three answers / status pills */
.mt-answers { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-3); margin-top: var(--space-3); }
.mt-answer { background: var(--answer-bg); border: 1px solid var(--answer-border); border-radius: var(--radius-card); padding: var(--space-4) var(--space-5); }
.mt-answer .top { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
.mt-answer .l { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.mt-answer .l svg { width: 20px; height: 20px; color: var(--text-muted); }
.mt-answer .d { color: var(--text-secondary); font-size: var(--text-sm); margin-top: var(--space-3); line-height: 1.5; }
.mt-pill { display: inline-flex; align-items: center; gap: 6px; font-size: var(--text-sm); font-weight: var(--weight-bold); white-space: nowrap;
  padding: 3px 10px 3px 8px; border-radius: var(--radius-round); border: 1px solid var(--status-ok-border); background: var(--status-ok-bg); color: var(--status-ok-fg); }
.mt-pill svg { width: 15px; height: 15px; }
.mt-pill.warn { border-color: var(--status-warn-border); background: var(--status-warn-bg); color: var(--status-warn-fg); }
.mt-pill.bad { border-color: var(--status-bad-border); background: var(--status-bad-bg); color: var(--status-bad-fg); }
.mt-pill.info { border-color: var(--status-info-border); background: var(--status-info-bg); color: var(--status-info-fg); }
@media (max-width: 860px) { .mt-answers { grid-template-columns: 1fr; } }

/* ================================================================ reveal (expander) */
[data-testid="stExpander"] details { background: var(--reveal-bg) !important; border: 1px solid var(--reveal-border) !important;
  border-radius: var(--radius-card) !important; transition: border-color var(--motion-base) var(--motion-ease); margin-bottom: var(--space-2); }
[data-testid="stExpander"] details:hover { border-color: var(--reveal-hover-border) !important; }
[data-testid="stExpander"] summary { padding: var(--space-4) var(--space-5) !important; min-height: 56px; }
[data-testid="stExpander"] summary p { font-family: var(--font-display); font-size: var(--text-md) !important; font-weight: var(--weight-semibold);
  color: var(--text-primary) !important; letter-spacing: -0.01em; }
[data-testid="stExpander"] summary p em { font-family: var(--font-body); font-style: normal; font-weight: var(--weight-medium);
  color: var(--text-muted); font-size: var(--text-sm); margin-left: var(--space-2); letter-spacing: 0; }
[data-testid="stExpander"] summary svg { color: var(--accent); }
[data-testid="stExpander"] details[open] > summary { border-bottom: 1px solid var(--border-subtle); }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] { padding: var(--space-5) !important; animation: mt-rise var(--motion-base) var(--motion-ease) both; }

/* ================================================================ cards (bordered containers) */
div[data-testid="stVerticalBlockBorderWrapper"], .stVerticalBlock[data-testid="stVerticalBlock"].st-emotion-cache-bordered {
  border-radius: var(--card-radius) !important; border-color: var(--card-border) !important; background: var(--card-bg); }
.mt-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--card-radius); padding: var(--space-5) var(--space-6); }
.mt-ph { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); margin: 0 0 var(--space-3); flex-wrap: wrap; }
.mt-ph .t { font-family: var(--font-display); font-weight: var(--weight-semibold); font-size: var(--text-md); color: var(--text-primary); }
.mt-ph .s { font-size: var(--text-sm); color: var(--text-muted); }
.mt-sec { font-family: var(--font-display); font-weight: var(--weight-semibold); font-size: var(--text-xl); color: var(--text-primary);
  letter-spacing: -0.02em; margin: var(--space-10) 0 var(--space-1); }
.mt-sec-sub { color: var(--text-muted); font-size: var(--text-sm); margin-bottom: var(--space-4); }

/* ================================================================ settings panel */
.st-key-settings { background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-card);
  padding: var(--space-5) !important; }
.mt-settings-head .t { font-family: var(--font-display); font-weight: var(--weight-semibold); font-size: var(--text-lg); color: var(--text-primary); }
.mt-settings-head .s { color: var(--text-muted); font-size: var(--text-sm); margin-top: 2px; }
.mt-derived { display: flex; justify-content: space-between; gap: var(--space-3); font-size: var(--text-sm); color: var(--text-muted);
  padding: var(--space-2) var(--space-3); border-radius: var(--radius-control); background: var(--surface-raised); margin: 0 0 var(--space-3); }
.mt-derived b { color: var(--text-primary); font-variant-numeric: tabular-nums; }

/* ================================================================ widgets */
[data-testid="stWidgetLabel"] p { font-size: var(--text-sm) !important; color: var(--text-secondary) !important; font-weight: var(--weight-semibold); }
.stButton > button, .stDownloadButton > button, [data-testid="stPopover"] > div > button, [data-testid="stPopoverButton"] {
  border-radius: var(--radius-round) !important; min-height: 44px; font-weight: var(--weight-semibold);
  border: 1px solid var(--button-secondary-border) !important; background: var(--button-secondary-bg) !important; color: var(--button-secondary-fg) !important;
  transition: background var(--motion-base) var(--motion-ease), border-color var(--motion-base) var(--motion-ease); }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stPopoverButton"]:hover {
  border-color: var(--accent) !important; background: var(--surface-hover) !important; }
.stButton > button p, .stDownloadButton > button p { color: inherit !important; font-weight: var(--weight-semibold); }
.stButton > button[data-testid="stBaseButton-primary"], .stDownloadButton > button[data-testid="stBaseButton-primary"] { background: var(--button-primary-bg) !important; border-color: var(--button-primary-bg) !important; color: var(--button-primary-fg) !important; }
.stButton > button[data-testid="stBaseButton-primary"] p, .stDownloadButton > button[data-testid="stBaseButton-primary"] p { color: var(--button-primary-fg) !important; }
.stButton > button[data-testid="stBaseButton-primary"]:hover, .stDownloadButton > button[data-testid="stBaseButton-primary"]:hover { background: var(--button-primary-hover-bg) !important; border-color: var(--button-primary-hover-bg) !important; }
.stButton > button[data-testid="stBaseButton-primary"]:active { background: var(--accent-pressed) !important; }
.stButton > button:disabled, .stDownloadButton > button:disabled, [data-testid="stBaseButton-primary"]:disabled {
  background: var(--surface-raised) !important; color: var(--text-muted) !important; border-color: var(--border-subtle) !important; cursor: not-allowed; }
[data-testid="stBaseButton-primary"]:disabled p { color: var(--text-muted) !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-testid="stTextInput"] input {
  background: var(--input-bg) !important; border-color: var(--input-border) !important; border-radius: var(--radius-control) !important; min-height: 44px; }
[data-testid="stSlider"] [role="slider"] { background: var(--slider-thumb) !important; box-shadow: 0 0 0 4px var(--accent-subtle) !important; }
[data-testid="stSliderThumbValue"] { font-family: var(--font-body) !important; font-variant-numeric: tabular-nums; font-weight: var(--weight-bold);
  font-size: var(--text-sm) !important; color: var(--accent) !important; }
[data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] { font-size: var(--text-xs) !important; color: var(--text-muted) !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: var(--space-1); border-bottom: 1px solid var(--border-subtle); flex-wrap: wrap; }
[data-testid="stTabs"] [data-baseweb="tab"] { min-height: 44px; padding: 0 var(--space-3); }
[data-testid="stTabs"] [data-baseweb="tab"] p { font-weight: var(--weight-semibold); font-size: var(--text-sm); color: var(--text-muted); }
[data-testid="stTabs"] [aria-selected="true"] p { color: var(--text-primary) !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 3px; }
[data-testid="stSegmentedControl"] button, [data-testid="stPills"] button { border-radius: var(--radius-round) !important; min-height: 40px; }
[data-testid="stBaseButton-pillsActive"], [data-testid="stBaseButton-segmented_controlActive"] {
  background: var(--accent-subtle) !important; border-color: var(--accent) !important; color: var(--accent) !important; }
[data-testid="stBaseButton-pillsActive"] p, [data-testid="stBaseButton-segmented_controlActive"] p { color: var(--accent) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border-subtle); border-radius: var(--radius-md); overflow: hidden; }
[data-testid="stToast"] { border-radius: var(--radius-md); border: 1px solid var(--border-control); background: var(--surface-raised) !important; }
[data-testid="stDialog"] [role="dialog"] { border-radius: var(--radius-panel) !important; border: 1px solid var(--border-subtle); background: var(--surface-card) !important; }
[data-testid="stImage"] img { border-radius: var(--radius-md); }
[data-testid="stCaptionContainer"] p { color: var(--text-muted) !important; font-size: var(--text-sm) !important; }
[data-testid="stTooltipIcon"] svg { color: var(--text-muted); }

/* ================================================================ link cards (page doors) */
.st-key-doors [data-testid="stPageLink"] a, [class*="st-key-door"] [data-testid="stPageLink"] a {
  border: 1px solid var(--card-border); border-radius: var(--radius-card) !important; background: var(--card-bg) !important;
  padding: var(--space-4) var(--space-5) !important; min-height: 56px; transition: border-color var(--motion-base) var(--motion-ease), background var(--motion-base) var(--motion-ease); }
.st-key-doors [data-testid="stPageLink"] a:hover, [class*="st-key-door"] [data-testid="stPageLink"] a:hover { border-color: var(--accent); background: var(--surface-raised) !important; }
.st-key-doors [data-testid="stPageLink"] a p, [class*="st-key-door"] [data-testid="stPageLink"] a p { font-weight: var(--weight-semibold); color: var(--text-primary) !important; font-size: var(--text-md); }
.st-key-cta [data-testid="stPageLink"] a { background: var(--button-primary-bg) !important; border-radius: var(--radius-round) !important;
  padding: 10px 22px !important; min-height: 48px; justify-content: center; transition: background var(--motion-base) var(--motion-ease); }
.st-key-cta [data-testid="stPageLink"] a:hover { background: var(--button-primary-hover-bg) !important; }
.st-key-cta [data-testid="stPageLink"] a p { color: var(--button-primary-fg) !important; font-weight: var(--weight-bold); font-size: var(--text-md); }
.st-key-cta2 [data-testid="stPageLink"] a { border: 1px solid var(--button-secondary-border); border-radius: var(--radius-round) !important;
  padding: 10px 22px !important; min-height: 48px; justify-content: center; background: transparent !important; }
.st-key-cta2 [data-testid="stPageLink"] a:hover { border-color: var(--accent); }
.st-key-cta2 [data-testid="stPageLink"] a p { color: var(--text-primary) !important; font-weight: var(--weight-semibold); font-size: var(--text-md); }

/* ================================================================ explained terms */
.mt-term { position: relative; border-bottom: 1.5px dotted var(--term-underline); cursor: help; color: inherit; outline-offset: 2px; }
.mt-term .tip { position: absolute; left: 50%; bottom: calc(100% + 8px); transform: translateX(-50%); width: max-content; max-width: min(300px, 80vw);
  background: var(--tooltip-bg); color: var(--tooltip-fg); border: 1px solid var(--tooltip-border); border-radius: var(--radius-control);
  padding: var(--space-2) var(--space-3); font-size: var(--text-sm); font-weight: var(--weight-medium); line-height: 1.45; z-index: 50;
  opacity: 0; visibility: hidden; pointer-events: none; transition: opacity var(--motion-fast) var(--motion-ease); text-align: left; white-space: normal; }
.mt-term:hover .tip, .mt-term:focus .tip, .mt-term:focus-within .tip { opacity: 1; visibility: visible; }

/* ================================================================ data bits */
.mt-kpis { display: grid; grid-template-columns: repeat(var(--n, 5), minmax(0, 1fr)); gap: var(--space-3); }
.mt-kpi { background: var(--surface-raised); border-radius: var(--radius-md); padding: var(--space-4); min-width: 0; }
.mt-kpi .l { font-size: var(--text-sm); color: var(--text-muted); font-weight: var(--weight-semibold); }
.mt-kpi .v { font-family: var(--font-display); font-size: var(--text-2xl); font-weight: var(--weight-semibold); color: var(--text-primary);
  letter-spacing: -0.03em; margin-top: var(--space-2); font-variant-numeric: tabular-nums; white-space: nowrap; line-height: 1.1; }
.mt-kpi .v small { font-family: var(--font-body); font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--text-muted); margin-left: 6px; letter-spacing: 0; }
.mt-kpi .d { font-size: var(--text-sm); color: var(--text-secondary); margin-top: var(--space-1); }
.mt-kpi .d.good { color: var(--status-ok-fg); } .mt-kpi .d.bad { color: var(--status-bad-fg); } .mt-kpi .d.warn { color: var(--status-warn-fg); }
@media (max-width: 1000px) { .mt-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.mt-scroll { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.mt-spec { width: 100%; border-collapse: collapse; font-size: var(--text-sm); border: none !important; }
.mt-spec tr, .mt-spec tr:nth-child(even) { background: transparent !important; border: none !important; }
.mt-spec th { font-size: var(--text-xs); font-weight: var(--weight-bold); letter-spacing: .1em; text-transform: uppercase; color: var(--text-muted) !important;
  text-align: left; padding: 0 var(--space-2) var(--space-2) 0 !important; border: none !important; border-bottom: 1px solid var(--border-subtle) !important; background: transparent !important; }
.mt-spec td { padding: var(--space-3) var(--space-2) var(--space-3) 0 !important; border: none !important; border-bottom: 1px solid var(--border-subtle) !important;
  vertical-align: middle; color: var(--text-primary); background: transparent !important; }
.mt-spec td.n { color: var(--text-secondary); min-width: 110px; }
.mt-spec td.v { font-weight: var(--weight-bold); text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.mt-spec td.bar { width: 28%; min-width: 90px; }
.mt-spec td.bar .lt { font-size: var(--text-xs); color: var(--text-muted); margin-top: 6px; white-space: nowrap; }
.mt-spec td.st { text-align: right; white-space: nowrap; width: 1%; }
.mt-gauge { position: relative; height: 6px; background: var(--surface-hover); border-radius: var(--radius-round); }
.mt-gauge .fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: var(--radius-round); background: var(--status-ok-fg); }
.mt-gauge .fill.warn { background: var(--status-warn-fg); } .mt-gauge .fill.bad { background: var(--status-bad-fg); }
.mt-gauge .lim { position: absolute; top: -4px; width: 2px; height: 14px; background: var(--text-primary); border-radius: 2px; }
.mt-legend { display: flex; gap: var(--space-4); flex-wrap: wrap; font-size: var(--text-sm); color: var(--text-muted); margin: var(--space-2) 0 0; }
.mt-legend span { display: inline-flex; align-items: center; gap: var(--space-2); }
.mt-legend i { width: 16px; height: 4px; display: inline-block; border-radius: 4px; }
.mt-note { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-2); line-height: 1.55; }
.mt-note b { color: var(--text-secondary); }
.mt-callout { border: 1px solid var(--border-control); background: var(--surface-raised); padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md); font-size: var(--text-sm); color: var(--text-secondary); margin: var(--space-3) 0; line-height: 1.55; }
.mt-callout.warn { border-color: var(--status-warn-border); background: var(--status-warn-bg); }
.mt-callout.accent { border-color: var(--accent-subtle); }
.mt-empty { border: 1px dashed var(--border-control); border-radius: var(--radius-card); padding: var(--space-10) var(--space-5); text-align: center; background: var(--surface-card); }
.mt-empty svg { width: 32px; height: 32px; color: var(--accent); }
.mt-empty .t { font-family: var(--font-display); font-weight: var(--weight-semibold); color: var(--text-primary); font-size: var(--text-lg); margin-top: var(--space-2); }
.mt-empty .s { color: var(--text-muted); font-size: var(--text-sm); margin-top: var(--space-1); }
.mt-kv { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2) var(--space-4); font-size: var(--text-sm); margin: 0; }
.mt-kv dt { color: var(--text-muted); font-weight: var(--weight-semibold); }
.mt-kv dd { margin: 0; color: var(--text-primary); }

/* ================================================================ process flow diagram */
.mt-pfd { width: 100%; background: var(--surface-sunken); border: 1px solid var(--border-subtle); border-radius: var(--radius-card); padding: var(--space-2); }
.mt-pfd svg { width: 100%; height: auto; display: block; }
.mt-pfd svg .flow { stroke-dasharray: 8 6; animation: mt-flow 1.6s linear infinite; }
@keyframes mt-flow { to { stroke-dashoffset: -28; } }
.mt-units { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-3); margin-top: var(--space-3); }
.mt-unit { background: var(--surface-raised); border-radius: var(--radius-md); padding: var(--space-3) var(--space-4); font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.5; }
.mt-unit .h { display: flex; justify-content: space-between; align-items: center; gap: var(--space-2); margin-bottom: var(--space-1); }
.mt-unit .h b { font-family: var(--font-display); font-size: var(--text-sm); }

/* ================================================================ footer */
.mt-foot { display: flex; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; font-size: var(--text-sm); color: var(--text-muted);
  margin-top: var(--space-16); padding-top: var(--space-5); border-top: 1px solid var(--border-subtle); }
.mt-foot .mt-wordmark { font-size: 1rem; }

/* ================================================================ motion + responsive */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
  .mt-pfd svg .flow { animation: none !important; }
}
@media (max-width: 1560px) { .mt-chip .nm { display: none; } }
@media (max-width: 1080px) {
  .st-key-navrail { display: none !important; }
  .st-key-navmenu { display: flex !important; }
  .st-key-topbar { justify-content: space-between; }
}
@media (max-width: 640px) {
  .block-container { padding: 0 var(--space-4) var(--space-10) !important; }
  .st-key-topbar { margin: 0 calc(-1 * var(--space-4)) var(--space-2); padding: var(--space-2) var(--space-4) !important; gap: var(--space-2) !important; }
  .mt-chip .nm, .mt-chip .mod, .st-key-chip [data-testid="stPageLink"] { display: none !important; }
  .st-key-chip { padding: 2px !important; }
  .st-key-chip .mt-pill { padding: 6px; }
  .st-key-chip .mt-pill .tx { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .st-key-chip { padding-left: 10px !important; }
  .mt-head { padding-top: var(--space-6); }
  .mt-verdict { padding: var(--space-4); gap: var(--space-3); }
  .mt-verdict .ic { width: 36px; height: 36px; }
  .mt-pfd { overflow-x: auto; } .mt-pfd svg { min-width: 760px; }
  .mt-kpis { grid-template-columns: 1fr 1fr; }
}
</style>
"""


# ------------------------------------------------------------------------------------- Plotly template ---
def plotly_template() -> go.layout.Template:
    t = go.layout.Template()
    axis = dict(gridcolor=R("chart-grid"), zeroline=False, linecolor=R("chart-axis"), ticks="outside", tickcolor=R("chart-axis"), ticklen=4,
                tickfont=dict(family=FONT_BODY, size=12, color=R("chart-tick")),
                title=dict(font=dict(family=FONT_BODY, size=13, color=R("chart-tick")), standoff=10))
    t.layout = go.Layout(
        font=dict(family=FONT_BODY, size=13, color=INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=SERIES,
        margin=dict(l=8, r=12, t=40, b=8),
        title=dict(font=dict(family=FONT_DISPLAY, size=15, color=R("chart-title")), x=0, xanchor="left", y=0.98),
        xaxis=axis, yaxis={**axis, "linecolor": "rgba(0,0,0,0)"},
        hoverlabel=dict(bgcolor=RAISED, bordercolor=CONTROL, font=dict(color=INK, size=13, family=FONT_BODY)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12, family=FONT_BODY, color=INK_2)),
        bargap=0.3, hovermode="closest",
    )
    return t


pio.templates["methatwin"] = plotly_template()
pio.templates.default = "methatwin"
PLOT_CFG = {"displaylogo": False, "responsive": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
            "toImageButtonOptions": {"format": "png", "scale": 2}}
