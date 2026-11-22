"""MethaTwin - reusable interface components (HTML/SVG rendered through st.markdown)."""
from __future__ import annotations

import html

import streamlit as st

import core
import theme as T

ICON = {"ok": "✓", "warn": "!", "bad": "✕", "info": "•"}


def md(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


def chip(kind: str, text: str) -> str:
    return f'<span class="st-chip {kind}">{ICON[kind]} {html.escape(text)}</span>'


def page_head(crumb: str, title: str, lede: str, meta: str = "") -> None:
    md(f'<div class="mt-pagehead"><div><div class="mt-crumb">MethaTwin / <b>{crumb}</b></div>'
       f'<div class="mt-title">{title}</div><div class="mt-lede">{lede}</div></div>'
       f'<div class="mt-head-meta">{meta}</div></div>')


def section(idx: str, title: str, sub: str = "") -> None:
    md(f'<div class="mt-sec"><span class="idx">{idx}</span><span class="t">{title}</span><span class="s">{sub}</span></div>')


def panel_head(title: str, sub: str = "") -> None:
    md(f'<div class="mt-ph"><span class="t">{title}</span><span class="s">{sub}</span></div>')


def verdict(kind: str, tag: str, msg: str) -> None:
    md(f'<div class="mt-verdict {kind}"><div class="flag"></div><div class="body">'
       f'<span class="tag">{ICON[kind]} {tag}</span><span class="msg">{msg}</span></div></div>')


def kpis(items: list[dict]) -> None:
    """items: {label, value, unit, delta, cls, color}"""
    cells = ""
    for k in items:
        sw = f'<i style="background:{k["color"]}"></i>' if k.get("color") else ""
        cc = f' style="--c:{k["color"]}"' if k.get("color") else ""
        cells += (f'<div class="mt-kpi"{cc} title="{html.escape(k.get("tip", ""))}"><div class="l">{sw}{k["label"]}</div>'
                  f'<div class="v">{k["value"]}<small>{k.get("unit", "")}</small></div>'
                  f'<div class="d {k.get("cls", "")}">{k.get("delta", "&nbsp;")}</div></div>')
    md(f'<div class="mt-kpis" style="--n:{len(items)}">{cells}</div>')


def gauge(value: float, lo: float, hi: float, limit: float | None, kind: str) -> str:
    w = max(0.0, min(1.0, (value - lo) / (hi - lo))) * 100
    lim = "" if limit is None else f'<div class="lim" style="left:calc({max(0, min(1, (limit - lo) / (hi - lo))) * 100:.1f}% - 1px)"></div>'
    return f'<div class="mt-gauge"><div class="fill {kind}" style="width:{w:.1f}%"></div>{lim}</div>'


def spec_table(rows: list[dict]) -> None:
    """rows: {name, value, limit, kind, status, gauge(optional html), tip}"""
    h = ('<table class="mt-spec"><tr><th>Parameter</th><th style="text-align:right">Value</th><th>Limit</th>'
         '<th style="text-align:right">Status</th></tr>')
    for r in rows:
        g = r.get("gauge", "")
        lim = f'<div class="lt">{r["limit"]}</div>' if r.get("limit") else ""
        h += (f'<tr title="{html.escape(r.get("tip", ""))}"><td class="n">{r["name"]}</td><td class="v">{r["value"]}</td>'
              f'<td class="bar">{g}{lim}</td><td class="st">{r["status"]}</td></tr>')
    md('<div class="mt-scroll">' + h + "</table></div>")


def empty(title: str, sub: str) -> None:
    md(f'<div class="mt-empty"><div class="t">{title}</div><div class="s">{sub}</div></div>')


def callout(text: str, kind: str = "") -> None:
    md(f'<div class="mt-callout {kind}">{text}</div>')


# -------------------------------------------------------------- process flow diagram ---
def pfd(x: dict, r: dict, status: dict) -> None:
    """Live process flow diagram of the plant with stream values from the current evaluation.
    status: {'digester': ok|warn|bad, 'upgrading': ..., 'grid': ...}"""
    col = {"ok": T.GOOD, "warn": T.WARN, "bad": T.BAD}
    feed = x["feed_t_d"]
    shares = [("Cattle slurry", 1 - x["maize_share"] - x["cive_share"], T.VIOLET),
              ("CIVE silage", x["cive_share"], T.TEAL), ("Maize silage", x["maize_share"], T.CORAL)]
    co2_removed = r["biogas_dry_Nm3_h"] * (1 - r["y_CH4_dry"]) - r["biomethane_Nm3_h"] * r["BM_CO2_pct"] / 100
    mono = "IBM Plex Mono, Consolas, monospace"
    head = "Space Grotesk, Inter, sans-serif"

    def t(xp, yp, s, size=11, fill=T.INK, weight=400, fam=None, anchor="start", ls=0):
        return (f'<text x="{xp}" y="{yp}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
                f'font-family="{fam or "Inter, sans-serif"}" text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>')

    def tag(xp, yp, s):
        return t(xp, yp, s, 9.5, T.MUTED, 500, mono, ls=0.8)

    def dot(xp, yp, k):
        return f'<circle cx="{xp}" cy="{yp}" r="5" fill="{col[k]}"/><circle cx="{xp}" cy="{yp}" r="8.5" fill="none" stroke="{col[k]}" stroke-opacity=".3"/>'

    s = ['<svg viewBox="0 0 1200 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Process flow diagram">',
         f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{T.INK_2}"/></marker>'
         f'<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0 L0 0 0 20" fill="none" stroke="{T.LINE_SOFT}" stroke-width="0.6"/></pattern></defs>',
         '<rect x="0" y="0" width="1200" height="340" fill="url(#grid)"/>']

    # --- feed
    s.append(f'<g class="unit"><title>Feedstock blend: {feed:.0f} t/day fresh matter. Maize is capped at 15 % by décret 2016-929.</title>')
    s.append(f'<rect class="box" x="20" y="70" width="200" height="170" fill="{T.SURFACE_2}" stroke="{T.LINE}" rx="10"/>')
    s.append(tag(34, 92, "FEED · FS-100"))
    s.append(t(34, 116, f"{feed:.0f}", 22, T.INK, 600, head) + t(34 + 14 * len(f"{feed:.0f}"), 116, " t/day", 11, T.MUTED, 500, mono))
    yy = 140
    for name, sh, c in shares:
        s.append(t(34, yy, name, 10.5, T.INK_2))
        s.append(t(206, yy, f"{100 * sh:.0f} %", 10.5, T.INK, 600, mono, "end"))
        s.append(f'<rect x="34" y="{yy + 5}" width="172" height="5" fill="{T.LINE_SOFT}" rx="2"/>'
                 f'<rect x="34" y="{yy + 5}" width="{172 * max(sh, 0):.1f}" height="5" fill="{c}" rx="2"/>')
        yy += 30
    s.append("</g>")
    s.append(f'<line class="flow" x1="220" y1="155" x2="282" y2="155" stroke="{T.INK_2}" stroke-width="2" marker-end="url(#ar)"/>')

    # --- digester (tank with dome)
    k = status["digester"]
    s.append(f'<g class="unit"><title>R-101 mesophilic CSTR digester (ADM1 surrogate). Volume {x["feed_t_d"] * x["hrt_d"]:,.0f} m³, '
             f'HRT {x["hrt_d"]:.0f} d, 39 °C. Stable if pH ≥ 6.8 and VFA ≤ 8 g COD/L.</title>')
    s.append(f'<path class="box" d="M290 110 Q 390 52 490 110 L490 262 L290 262 Z" fill="{T.SURFACE_2}" stroke="{col[k]}" stroke-width="1.6"/>')
    s.append(f'<path d="M290 236 L490 236 L490 262 L290 262 Z" fill="{T.MINT_SOFT}"/>')
    s.append(tag(304, 128, "R-101 · DIGESTER"))
    s.append(dot(472, 124, k))
    s.append(t(304, 154, f'{x["feed_t_d"] * x["hrt_d"]:,.0f}', 20, T.INK, 600, head) + t(372, 154, "m³", 10.5, T.MUTED, 500, mono))
    rows = [("HRT", f'{x["hrt_d"]:.0f} d'), ("pH", f'{r["pH"]:.2f}'), ("VFA", f'{r["VFA_gCOD_L"]:.1f} g/L'),
            ("Free NH₃", f'{r["free_NH3_mgN_L"]:.0f} mg/L')]
    yy = 176
    for a, b in rows:
        s.append(t(304, yy, a, 10.5, T.MUTED, 500, mono) + t(476, yy, b, 10.5, T.INK, 600, mono, "end"))
        yy += 16
    s.append(t(390, 254, "39 °C · CSTR", 9.5, T.PETROL_600, 500, mono, "middle", 0.6))
    s.append("</g>")
    # digestate
    s.append(f'<line x1="390" y1="262" x2="390" y2="300" stroke="{T.INK_2}" stroke-width="1.5" marker-end="url(#ar)"/>')
    s.append(tag(400, 300, "DIGESTATE → STORAGE"))

    # --- biogas stream
    s.append(f'<line class="flow" x1="490" y1="150" x2="596" y2="150" stroke="{T.TEAL}" stroke-width="3" marker-end="url(#ar)"/>')
    s.append(tag(500, 136, "RAW BIOGAS"))
    s.append(t(500, 172, f'{r["biogas_dry_Nm3_h"]:.0f} Nm³/h', 11, T.INK, 600, mono))
    s.append(t(500, 187, f'{100 * r["y_CH4_dry"]:.1f} % CH₄', 10.5, T.INK_2, 500, mono))

    # --- compression
    s.append(f'<g class="unit"><title>K-101/K-102 two-stage intercooled compression to 9 bar. Scrubber electricity {r["P_el_upg_kW"]:.0f} kW.</title>')
    s.append(f'<circle class="box" cx="626" cy="150" r="26" fill="{T.SURFACE_2}" stroke="{T.LINE}" stroke-width="1.4"/>')
    s.append(f'<path d="M608 136 L646 142 L646 158 L608 164 Z" fill="none" stroke="{T.INK_2}" stroke-width="1.4"/>')
    s.append(tag(600, 196, "K-101/102"))
    s.append(t(626, 112, f'⚡ {r["P_el_upg_kW"]:.0f} kW', 10.5, T.INK, 600, mono, "middle"))
    s.append("</g>")
    s.append(f'<line class="flow" x1="652" y1="150" x2="706" y2="150" stroke="{T.TEAL}" stroke-width="3" marker-end="url(#ar)"/>')

    # --- absorber column
    k = status["upgrading"]
    s.append(f'<g class="unit"><title>T-201 high-pressure water scrubber (DWSIM surrogate), 10 equilibrium stages at 9 bar, '
             f'flash F-201 at {x["p_flash_bar"]:.2f} bar recycled to compression. Methane slip {r["CH4_slip_pct"]:.2f} %.</title>')
    s.append(f'<rect class="box" x="712" y="56" width="74" height="228" rx="30" fill="{T.SURFACE_2}" stroke="{col[k]}" stroke-width="1.6"/>')
    for i in range(9):
        yv = 86 + i * 20
        s.append(f'<line x1="720" y1="{yv}" x2="778" y2="{yv}" stroke="{T.LINE}" stroke-width="1" stroke-dasharray="3 3"/>')
    s.append(dot(749, 72, k))
    s.append(tag(700, 304, "T-201 · SCRUBBER"))
    s.append(f'<line class="flow" x1="846" y1="96" x2="790" y2="96" stroke="{T.BLUE}" stroke-width="2" marker-end="url(#ar)"/>')
    s.append(t(796, 116, "WATER IN", 9, T.BLUE, 600, mono, ls=0.6))
    s.append(t(800, 214, "WATER", 9.5, T.BLUE, 600, mono, ls=0.8))
    s.append(t(800, 230, f'{x["water_per_kNm3"]:.0f} m³/kNm³', 10.5, T.INK, 600, mono))
    s.append(t(800, 246, f'flash {x["p_flash_bar"]:.2f} bar', 10.5, T.INK_2, 500, mono))
    s.append(t(800, 262, f'slip {r["CH4_slip_pct"]:.2f} %', 10.5, T.INK_2, 500, mono))
    s.append("</g>")

    # --- biomethane to grid
    k = status["grid"]
    s.append(f'<line class="flow" x1="749" y1="56" x2="749" y2="34" stroke="{T.TEAL}" stroke-width="3"/>'
             f'<line class="flow" x1="749" y1="34" x2="934" y2="34" stroke="{T.TEAL}" stroke-width="3"/>'
             f'<line class="flow" x1="934" y1="34" x2="934" y2="62" stroke="{T.TEAL}" stroke-width="3" marker-end="url(#ar)"/>')
    s.append(tag(800, 26, "BIOMETHANE · 9 BAR"))
    s.append(f'<g class="unit"><title>Grid injection (GRDF specification): CO₂ &lt; 2.5 %, HHV 10.7–12.8 kWh/Nm³, '
             f'O₂ &lt; 100 ppm (exemption up to 0.75 %). Net flow after 3.5 % heat self-use.</title>')
    s.append(f'<rect class="box" x="870" y="66" width="310" height="136" fill="{T.SURFACE_2}" stroke="{col[k]}" stroke-width="1.6" rx="10"/>')
    s.append(f'<rect x="870" y="66" width="310" height="26" fill="{T.SURFACE_3}" rx="10"/><rect x="870" y="80" width="310" height="12" fill="{T.SURFACE_3}"/>')
    s.append(t(884, 83, "GRID INJECTION · GRDF", 9.5, T.MINT, 600, mono, ls=0.9))
    s.append(dot(1162, 79, k))
    s.append(t(884, 126, f'{r["bm_net_Nm3_h"]:.0f}', 30, T.INK, 600, head) + t(884 + 18 * len(f'{r["bm_net_Nm3_h"]:.0f}') + 4, 126, "Nm³/h net", 11, T.MUTED, 500, mono))
    s.append(t(884, 146, f'{r["energy_MWh_yr"] / 1000:.1f} GWh/yr · {r["HHV"]:.2f} kWh/Nm³ HHV', 10.5, T.INK_2, 500, mono))
    q = [("CO₂", f'{r["BM_CO2_pct"]:.2f} %', r["BM_CO2_pct"] <= 2.5), ("O₂", f'{r["BM_O2_ppm"]:,.0f} ppm', r["BM_O2_ppm"] <= 100),
         ("P(spec)", f'{100 * r["p_spec"]:.0f} %', r["p_spec"] >= 0.9)]
    xx = 884
    for a, b, ok in q:
        s.append(t(xx, 172, a, 9.5, T.MUTED, 500, mono, ls=0.6))
        s.append(t(xx, 189, b, 11, T.GOOD if ok else T.WARN, 600, mono))
        xx += 100
    s.append("</g>")

    # --- off-gas
    s.append(f'<line class="flow" x1="786" y1="270" x2="934" y2="270" stroke="{T.CORAL}" stroke-width="2" marker-end="url(#ar)"/>')
    s.append(f'<g class="unit"><title>Off-gas from the flash and stripper. Value is a balance on the surrogate outputs (raw CO₂ minus CO₂ in product); '
             f'in the full design a 1.05 bar flash recovers ~65 % of it as a 99 % biogenic CO₂ stream.</title>')
    s.append(f'<rect class="box" x="940" y="240" width="240" height="64" fill="{T.SURFACE_2}" stroke="{T.LINE}" rx="10"/>')
    s.append(tag(954, 260, "CO₂ OFF-GAS / CAPTURE"))
    s.append(t(954, 287, f'≈ {co2_removed:.0f} Nm³/h CO₂ removed', 11.5, T.INK, 600, mono))
    s.append("</g>")
    s.append("</svg>")
    md(f'<div class="mt-pfd">{"".join(s)}</div>')
    md(f'<div class="mt-legend"><span><i style="background:{T.TEAL}"></i>Gas</span><span><i style="background:{T.BLUE}"></i>Process water</span>'
       f'<span><i style="background:{T.CORAL}"></i>CO₂ off-gas</span><span>● Unit status: '
       f'<b style="color:{T.GOOD}">ok</b> / <b style="color:{T.WARN}">margin</b> / <b style="color:{T.BAD}">violated</b></span>'
       '<span>Hover a unit for details</span></div>')
