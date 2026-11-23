"""MethaTwin - interface components (HTML/SVG through st.markdown), the custom icon set and shared status logic.

Every colour here is a CSS custom property from tokens.py, except inside the process-flow SVG, which uses
the resolved token values from theme.py.
"""
from __future__ import annotations

import html

import streamlit as st

import core
import state as S
import theme as T

# ---------------------------------------------------------------------------------------- icon set ---
# 24 px grid, 1.75 stroke, round caps and joins; drawn in currentColor
_I = {
    "feed": '<path d="M5 20c0-8 5-14 14-15-1 9-7 14-14 15z"/><path d="M5 20l8-8"/>',
    "digester": '<path d="M4 20V11a8 6 0 0 1 16 0v9z"/><path d="M4 16h16"/><circle cx="12" cy="4" r="1.5"/>',
    "scrub": '<rect x="8" y="3" width="8" height="18" rx="4"/><path d="M10 8h4M10 12h4M10 16h4"/>',
    "grid": '<path d="M3 12h12"/><path d="M15 8v8l6-4z"/><path d="M6 8v8"/>',
    "money": '<circle cx="12" cy="12" r="8"/><path d="M14.5 9a3 3 0 1 0 0 6M8 11h5M8 13.5h5"/>',
    "futures": '<path d="M4 18h16"/><path d="M4 18c3-9 5-12 8-12s5 3 8 12"/><path d="M12 6v12" stroke-dasharray="2 2"/>',
    "sliders": '<path d="M4 7h7M15 7h5M4 17h3M11 17h9"/><circle cx="13" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    "shield": '<path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "bookmark": '<path d="M6 3h12v18l-6-4-6 4z"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/><path d="M9 7h6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "ok": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
    "warn": '<path d="M12 3.5l9.5 16.5h-19z"/><path d="M12 10v4.5M12 17.5v.5"/>',
    "bad": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    "plant": '<path d="M3 20h18"/><path d="M5 20v-7a4 3 0 0 1 8 0v7"/><rect x="15" y="9" width="4" height="11" rx="2"/><path d="M13 15h2"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/>',
}


def icon(name: str, cls: str = "") -> str:
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false">{_I[name]}</svg>')


STATUS_WORD = {"ok": "Good", "warn": "Check", "bad": "Problem", "info": "Note"}


def md(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


# ------------------------------------------------------------------------------------ explained terms ---
TERMS = {
    "LCOE": "Levelised cost: what one MWh of gas costs to make, counting both building and running the plant.",
    "levelised cost": "What one MWh of gas costs to make, counting both building and running the plant.",
    "NPV": "Net present value: all money in minus all money out over 15 years, in today's euros. Above zero means the plant pays.",
    "HRT": "Hydraulic retention time: how many days the feed stays in the tank. Longer means a bigger tank.",
    "retention time": "How many days the feed stays in the tank. Longer means a bigger tank and calmer microbes.",
    "VFA": "Volatile fatty acids: when they build up, the microbes are overloaded and the tank can turn sour.",
    "CIVE": "Cover crops grown between two main crops, harvested as silage for energy.",
    "k_dis": "Disintegration rate: how fast the solid feed falls apart so the microbes can eat it.",
    "K_I,NH3": "Ammonia tolerance of the microbes. A lower value means they are more easily poisoned by ammonia.",
    "P(stable)": "The chance, estimated by a classifier, that the digester runs steadily.",
    "CAPEX": "The money needed to build the plant.",
    "OPEX": "The yearly cost of running the plant: feed, electricity, staff, maintenance.",
    "Nm³/h": "Normal cubic metres per hour: gas volume measured at 0 °C and 1 atm.",
    "HHV": "Higher heating value: the energy in one cubic metre of gas. The grid sets a minimum and maximum.",
    "methane slip": "Methane lost with the removed CO₂ instead of reaching the grid.",
    "flash pressure": "Pressure of a vessel that releases methane caught in the wash water and sends it back.",
    "surrogate": "A fast machine-learning copy of the slow full simulation, valid inside the ranges it was trained on.",
    "Monte Carlo": "Replaying the plant thousands of times with randomly drawn prices and biology to see the spread of outcomes.",
    "P10": "1 in 10 futures comes out below this value.",
    "P90": "9 in 10 futures come out below this value.",
    "CRE": "The French energy regulator, whose 2024 survey of real plants anchors the cost model.",
    "ADM1": "The international standard model of the biology inside a digester.",
    "DWSIM": "An open-source chemical process simulator, used here for the gas-cleaning unit.",
    "R²": "How closely the fast model matches the full simulation; 1.0 is a perfect match.",
    "tariff": "The guaranteed price paid for each MWh of gas injected into the grid.",
    "water scrubber": "A tall column where water under pressure dissolves CO₂ out of the biogas, leaving methane.",
}


def term(word: str, tip: str | None = None) -> str:
    """Inline explained term: dotted underline; explanation on hover, keyboard focus and tap."""
    t = html.escape(tip or TERMS.get(word, ""))
    return f'<span class="mt-term" tabindex="0">{word}<span class="tip" role="tooltip">{t}</span></span>'


# ------------------------------------------------------------------------------------------ layout ---
def page_head(ic: str, eyebrow: str, title: str, lede: str) -> None:
    md(f'<header class="mt-head mt-rise"><div class="mt-eyebrow">{icon(ic)}{eyebrow}</div>'
       f'<h1 class="mt-title">{title}</h1><p class="mt-lede">{lede}</p></header>')


def section(title: str, sub: str = "") -> None:
    md(f'<h2 class="mt-sec">{title}</h2>' + (f'<p class="mt-sec-sub">{sub}</p>' if sub else ""))


def panel_head(title: str, sub: str = "") -> None:
    md(f'<div class="mt-ph"><span class="t">{title}</span><span class="s">{sub}</span></div>')


def verdict(kind: str, kicker: str, title: str, msg: str = "") -> None:
    ic = {"ok": "ok", "warn": "warn", "bad": "bad", "info": "info"}[kind]
    md(f'<section class="mt-verdict {kind} mt-rise" role="status" aria-live="polite"><div class="ic">{icon(ic)}</div>'
       f'<div><div class="k">{kicker}</div><div class="t">{title}</div>'
       + (f'<div class="m">{msg}</div>' if msg else "") + '</div></section>')


def pill(kind: str, text: str) -> str:
    return f'<span class="mt-pill {kind}">{icon(kind)}<span class="tx">{html.escape(text)}</span></span>'


def answers(items: list[tuple[str, str, str, str, str]]) -> None:
    """items: (icon, label, kind, word, description)"""
    md('<div class="mt-answers">' + "".join(
        f'<div class="mt-answer"><div class="top"><span class="l">{icon(ic)}{lab}</span>{pill(k, w)}</div>'
        f'<div class="d">{d}</div></div>' for ic, lab, k, w, d in items) + "</div>")


def kpis(items: list[dict]) -> None:
    """items: {label, value, unit, delta, cls}"""
    cells = "".join(
        f'<div class="mt-kpi"><div class="l">{k["label"]}</div><div class="v">{k["value"]}<small>{k.get("unit", "")}</small></div>'
        f'<div class="d {k.get("cls", "")}">{k.get("delta", "&nbsp;")}</div></div>' for k in items)
    md(f'<div class="mt-kpis" style="--n:{len(items)}">{cells}</div>')


def gauge(value: float, lo: float, hi: float, limit: float | None, kind: str) -> str:
    w = max(0.0, min(1.0, (value - lo) / (hi - lo))) * 100
    lim = "" if limit is None else f'<div class="lim" style="left:calc({max(0, min(1, (limit - lo) / (hi - lo))) * 100:.1f}% - 1px)"></div>'
    return f'<div class="mt-gauge" aria-hidden="true"><div class="fill {kind}" style="width:{w:.1f}%"></div>{lim}</div>'


def spec_table(rows: list[dict]) -> None:
    """rows: {name, value, limit, gauge(optional html), status(optional html)}"""
    h = ('<table class="mt-spec"><tr><th scope="col">What</th><th scope="col" style="text-align:right">Value</th>'
         '<th scope="col">Limit</th><th scope="col" style="text-align:right">Status</th></tr>')
    for r in rows:
        lim = f'<div class="lt">{r["limit"]}</div>' if r.get("limit") else ""
        h += (f'<tr><td class="n">{r["name"]}</td><td class="v">{r["value"]}</td>'
              f'<td class="bar">{r.get("gauge", "")}{lim}</td><td class="st">{r.get("status", "")}</td></tr>')
    md('<div class="mt-scroll">' + h + "</table></div>")


def empty(title: str, sub: str, ic: str = "spark") -> None:
    md(f'<div class="mt-empty">{icon(ic)}<div class="t">{title}</div><div class="s">{sub}</div></div>')


def callout(text: str, kind: str = "") -> None:
    md(f'<div class="mt-callout {kind}">{text}</div>')


def note(text: str) -> None:
    md(f'<div class="mt-note">{text}</div>')


# ------------------------------------------------------------------------------------ status logic ---
def status(R: dict) -> dict:
    """Plain-language reading of one evaluation against the study thresholds in core.py (no new numbers)."""
    stable = R["p_stable"] >= 0.5 and R["pH"] >= core.STAB["pH_min"] and R["VFA_gCOD_L"] <= core.STAB["VFA_max"]
    co2_ok = R["BM_CO2_pct"] <= core.SPEC["CO2_max"]
    hhv_ok = core.SPEC["HHV"][0] <= R["HHV"] <= core.SPEC["HHV"][1]
    o2_ok = R["BM_O2_ppm"] <= core.SPEC["O2_exempt"]
    spec = co2_ok and hhv_ok and o2_ok
    ps = R["p_stable"]
    bio = ("ok", "Healthy", "The microbes are comfortable.") if ps >= 0.9 else \
        ("warn", "At risk", "Acids or ammonia could upset the microbes.") if stable else \
        ("bad", "Unstable", "The tank is likely to turn sour.")
    gas = ("ok", "Grid-ready", "The cleaned gas meets the network rules.") if spec else \
        ("bad", "Off-spec", "The cleaned gas misses the network rules.")
    if R["p_upg_valid"] < 0.5 and gas[0] == "ok":
        gas = ("warn", "Uncertain", "These gas-cleaning settings are outside the zone the model knows well.")
    money = ("ok", "Pays", "Gas sales cover all the costs.") if R["NPV_EUR"] >= 0 else \
        ("warn", "Does not pay", "The costs are higher than the gas sales.")
    if not stable or not spec:
        overall = ("bad", "Needs changes")
    elif R["NPV_EUR"] < 0 or R["p_upg_valid"] < 0.5:
        overall = ("warn", "Works, but check")
    else:
        overall = ("ok", "Works and pays")
    return {"stable": stable, "co2_ok": co2_ok, "hhv_ok": hhv_ok, "o2_ok": o2_ok, "spec": spec,
            "bio": bio, "gas": gas, "money": money, "overall": overall}


# ------------------------------------------------------------------------------------- save dialog ---
@st.dialog("Save this design")
def save_dialog() -> None:
    st.caption("Keeps the current design, microbe and market settings so you can compare and reload them on the "
               "Designs page. Saved designs last for this browser session.")
    default = f"My design {len(st.session_state.scenarios) + 1}"
    name = st.text_input("Name", value=default, max_chars=40)
    if name in st.session_state.scenarios:
        st.warning("A design with this name exists; saving will replace it.")
    c1, c2 = st.columns(2)
    if c1.button("Save", type="primary", width="stretch", disabled=not name.strip()):
        S.save_scenario(name.strip())
        st.session_state["_toast"] = f"Saved “{name.strip()}”"
        st.rerun()
    if c2.button("Cancel", width="stretch"):
        st.rerun()


# --------------------------------------------------------------------------- process flow diagram ---
def pfd(x: dict, r: dict, stat: dict) -> None:
    """Live process flow diagram with stream values from the current evaluation, followed by a text
    summary of each unit (so nothing depends on hover). stat: {'digester'|'upgrading'|'grid': ok|warn|bad}"""
    col = {"ok": T.GOOD, "warn": T.WARN, "bad": T.BAD}
    word = {"ok": "OK", "warn": "MARGIN", "bad": "VIOLATED"}
    feed = x["feed_t_d"]
    shares = [("Cattle slurry", 1 - x["maize_share"] - x["cive_share"], T.D3),
              ("CIVE silage", x["cive_share"], T.D2), ("Maize silage", x["maize_share"], T.D1)]
    co2_removed = r["biogas_dry_Nm3_h"] * (1 - r["y_CH4_dry"]) - r["biomethane_Nm3_h"] * r["BM_CO2_pct"] / 100
    head, body = T.FONT_DISPLAY, T.FONT_BODY

    def t(xp, yp, s, size=14, fill=T.INK, weight=500, fam=None, anchor="start", ls=0):
        return (f'<text x="{xp}" y="{yp}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
                f'font-family="{fam or body}" text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>')

    def tag(xp, yp, s, fill=T.MUTED):
        return t(xp, yp, s, 12, fill, 700, body, ls=1.2)

    def badge(xp, yp, k):
        w = 14 + 8.2 * len(word[k])
        return (f'<rect x="{xp - w}" y="{yp - 13}" width="{w}" height="20" rx="10" fill="{T.RAISED}" stroke="{col[k]}"/>'
                + t(xp - w / 2, yp + 1, word[k], 11, col[k], 800, body, "middle", 0.8))

    s = ['<svg viewBox="0 0 1200 350" xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="Process flow diagram: feed, digester, compression, water scrubber, grid injection and CO2 off-gas">',
         f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{T.INK_2}"/></marker></defs>']
    # feed
    s.append(f'<rect x="20" y="66" width="210" height="184" fill="{T.SURFACE}" stroke="{T.LINE}" rx="14"/>')
    s.append(tag(36, 92, "FEED"))
    s.append(t(36, 122, f"{feed:.0f}", 26, T.INK, 600, head) + t(36 + 16 * len(f"{feed:.0f}") + 6, 122, "t/day", 13, T.MUTED, 600))
    yy = 150
    for name, sh, c in shares:
        s.append(t(36, yy, name, 13, T.INK_2) + t(214, yy, f"{100 * sh:.0f} %", 13, T.INK, 700, body, "end"))
        s.append(f'<rect x="36" y="{yy + 6}" width="178" height="6" fill="{T.RAISED}" rx="3"/>'
                 f'<rect x="36" y="{yy + 6}" width="{178 * max(sh, 0):.1f}" height="6" fill="{c}" rx="3"/>')
        yy += 32
    s.append(f'<line class="flow" x1="230" y1="158" x2="284" y2="158" stroke="{T.INK_2}" stroke-width="2" marker-end="url(#ar)"/>')
    # digester
    k = stat["digester"]
    s.append(f'<path d="M290 112 Q 392 50 494 112 L494 266 L290 266 Z" fill="{T.SURFACE}" stroke="{col[k]}" stroke-width="2"/>')
    s.append(tag(306, 130, "DIGESTER"))
    s.append(badge(482, 128, k))
    s.append(t(306, 160, f'{x["feed_t_d"] * x["hrt_d"]:,.0f}', 22, T.INK, 600, head) + t(388, 160, "m³", 13, T.MUTED, 600))
    yy = 184
    for a, b in (("Retention", f'{x["hrt_d"]:.0f} d'), ("pH", f'{r["pH"]:.2f}'), ("VFA", f'{r["VFA_gCOD_L"]:.1f} g/L'),
                 ("Free NH₃", f'{r["free_NH3_mgN_L"]:.0f} mg/L')):
        s.append(t(306, yy, a, 13, T.MUTED, 600) + t(480, yy, b, 13, T.INK, 700, body, "end"))
        yy += 19
    s.append(f'<line x1="392" y1="266" x2="392" y2="306" stroke="{T.INK_2}" stroke-width="1.5" marker-end="url(#ar)"/>')
    s.append(tag(402, 312, "DIGESTATE TO STORAGE"))
    # biogas
    s.append(f'<line class="flow" x1="494" y1="150" x2="598" y2="150" stroke="{T.D1}" stroke-width="3" marker-end="url(#ar)"/>')
    s.append(tag(504, 134, "RAW BIOGAS", T.D1))
    s.append(t(504, 176, f'{r["biogas_dry_Nm3_h"]:.0f} Nm³/h', 13, T.INK, 700))
    s.append(t(504, 194, f'{100 * r["y_CH4_dry"]:.1f} % CH₄', 13, T.INK_2, 600))
    # compression
    s.append(f'<circle cx="628" cy="150" r="27" fill="{T.SURFACE}" stroke="{T.LINE}" stroke-width="1.5"/>')
    s.append(f'<path d="M610 136 L648 142 L648 158 L610 164 Z" fill="none" stroke="{T.INK_2}" stroke-width="1.5"/>')
    s.append(tag(598, 200, "COMPRESSOR"))
    s.append(t(628, 112, f'{r["P_el_upg_kW"]:.0f} kW', 13, T.INK, 700, body, "middle"))
    s.append(f'<line class="flow" x1="655" y1="150" x2="706" y2="150" stroke="{T.D1}" stroke-width="3" marker-end="url(#ar)"/>')
    # scrubber
    k = stat["upgrading"]
    s.append(f'<rect x="712" y="58" width="76" height="226" rx="30" fill="{T.SURFACE}" stroke="{col[k]}" stroke-width="2"/>')
    for i in range(9):
        yv = 88 + i * 20
        s.append(f'<line x1="722" y1="{yv}" x2="778" y2="{yv}" stroke="{T.LINE}" stroke-width="1" stroke-dasharray="3 3"/>')
    s.append(badge(790, 312, k))
    s.append(tag(700, 334, "WATER SCRUBBER"))
    s.append(f'<line class="flow" x1="848" y1="98" x2="792" y2="98" stroke="{T.D2}" stroke-width="2" marker-end="url(#ar)"/>')
    s.append(t(800, 120, "WATER IN", 12, T.D2, 700, ls=1.2))
    s.append(t(800, 216, f'{x["water_per_kNm3"]:.0f} m³/kNm³ water', 13, T.INK, 700))
    s.append(t(800, 235, f'flash {x["p_flash_bar"]:.2f} bar', 13, T.INK_2, 600))
    s.append(t(800, 254, f'slip {r["CH4_slip_pct"]:.2f} %', 13, T.INK_2, 600))
    # grid
    k = stat["grid"]
    s.append(f'<line class="flow" x1="750" y1="58" x2="750" y2="34" stroke="{T.D1}" stroke-width="3"/>'
             f'<line class="flow" x1="750" y1="34" x2="936" y2="34" stroke="{T.D1}" stroke-width="3"/>'
             f'<line class="flow" x1="936" y1="34" x2="936" y2="62" stroke="{T.D1}" stroke-width="3" marker-end="url(#ar)"/>')
    s.append(tag(800, 24, "BIOMETHANE", T.D1))
    s.append(f'<rect x="872" y="66" width="308" height="140" fill="{T.SURFACE}" stroke="{col[k]}" stroke-width="2" rx="14"/>')
    s.append(tag(888, 92, "GRID INJECTION"))
    s.append(badge(1166, 90, k))
    s.append(t(888, 132, f'{r["bm_net_Nm3_h"]:.0f}', 32, T.INK, 600, head)
             + t(888 + 20 * len(f'{r["bm_net_Nm3_h"]:.0f}') + 6, 132, "Nm³/h net", 13, T.MUTED, 600))
    s.append(t(888, 154, f'{r["energy_MWh_yr"] / 1000:.1f} GWh/yr · {r["HHV"]:.2f} kWh/Nm³', 13, T.INK_2, 600))
    xx = 888
    for a, b, ok in (("CO₂", f'{r["BM_CO2_pct"]:.2f} %', r["BM_CO2_pct"] <= 2.5), ("O₂", f'{r["BM_O2_ppm"]:,.0f} ppm', r["BM_O2_ppm"] <= 100),
                     ("In spec", f'{100 * r["p_spec"]:.0f} %', r["p_spec"] >= 0.9)):
        s.append(t(xx, 178, a, 12, T.MUTED, 700, ls=0.6))
        s.append(t(xx, 196, b, 13, T.GOOD if ok else T.WARN, 700))
        xx += 100
    # off-gas
    s.append(f'<line class="flow" x1="788" y1="272" x2="936" y2="272" stroke="{T.D4}" stroke-width="2" marker-end="url(#ar)"/>')
    s.append(f'<rect x="942" y="240" width="238" height="66" fill="{T.SURFACE}" stroke="{T.LINE}" rx="14"/>')
    s.append(tag(958, 262, "CO₂ OFF-GAS", T.D4))
    s.append(t(958, 290, f'≈ {co2_removed:.0f} Nm³/h CO₂ removed', 13, T.INK, 700))
    s.append("</svg>")
    md(f'<div class="mt-pfd">{"".join(s)}</div>')
    md(f'<div class="mt-legend"><span><i style="background:{T.D1}"></i>Gas</span><span><i style="background:{T.D2}"></i>Process water</span>'
       f'<span><i style="background:{T.D4}"></i>CO₂ off-gas</span><span>Unit badges: OK / MARGIN / VIOLATED</span></div>')
    units = [
        ("Digester", stat["digester"], f'A warm (39 °C) mixed tank of {x["feed_t_d"] * x["hrt_d"]:,.0f} m³ where microbes make biogas. '
         f'It is called stable when pH stays at or above 6.8 and {term("VFA")} at or below 8 g/L.'),
        ("Water scrubber", stat["upgrading"], f'Two compressors bring the gas to 9 bar; a 10-stage {term("water scrubber")} dissolves the CO₂. '
         f'A flash at {x["p_flash_bar"]:.2f} bar recovers caught methane. {term("Methane slip", TERMS["methane slip"])}: '
         f'{r["CH4_slip_pct"]:.2f} %.'),
        ("Grid injection", stat["grid"], "Grid rules (GRDF): CO₂ below 2.5 %, heating value 10.7–12.8 kWh/Nm³, O₂ below 100 ppm "
         "(an exemption allows up to 0.75 %). Net flow is after 3.5 % used for heating."),
    ]
    md('<div class="mt-units">' + "".join(
        f'<div class="mt-unit"><div class="h"><b>{n}</b>{pill(k, STATUS_WORD[k])}</div>{d}</div>' for n, k, d in units) + "</div>")
