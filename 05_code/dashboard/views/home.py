"""Start - the brand landing page: slogan, promise, the 3D "living core" and the ways in. No figures here."""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

import theme as T
import tokens as K
import ui

ui.md("""
<style>
.st-key-hero { position: relative; padding: var(--space-10) 0 var(--space-8) !important; margin-top: var(--space-4); isolation: isolate; }
/* no box: a soft pool of darkness with a faint amber glow behind the scene, fading into the page on every side */
.st-key-hero::before { content: ""; position: absolute; inset: -12% -8%; z-index: -1; pointer-events: none;
  background:
    radial-gradient(38% 46% at 74% 46%, color-mix(in srgb, var(--accent) 9%, transparent) 0%, transparent 70%),
    radial-gradient(60% 62% at 58% 48%, var(--hero-bg) 0%, color-mix(in srgb, var(--hero-bg) 55%, transparent) 45%, transparent 78%); }
.mh-slogan { font-family: var(--font-display); font-weight: var(--weight-semibold); font-size: var(--text-hero); line-height: 1.02;
  letter-spacing: -0.045em; color: var(--text-primary); margin: var(--space-4) 0 0 !important; padding: 0 !important; }
.mh-slogan .em { color: var(--accent); display: block; }
.mh-lede { font-size: var(--text-lg); color: var(--text-secondary); line-height: 1.6; max-width: 32rem; margin: var(--space-5) 0 var(--space-6); }
.mh-lede b { color: var(--text-primary); }
.mh-proof { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-5); margin-top: var(--space-6); font-size: var(--text-sm); color: var(--text-muted); }
.mh-proof span { display: inline-flex; align-items: center; gap: var(--space-2); }
.mh-proof svg { width: 18px; height: 18px; color: var(--accent); }
.mh-promise { display: grid; grid-template-columns: 1fr 2.2fr; gap: var(--space-10); margin: var(--space-16) 0 var(--space-4);
  padding-top: var(--space-10); border-top: 1px solid var(--border-subtle); }
.mh-promise .k { font-size: var(--text-xs); font-weight: var(--weight-bold); letter-spacing: .14em; text-transform: uppercase; color: var(--accent); }
.mh-promise p { font-family: var(--font-display); font-size: clamp(1.25rem, 2.2vw, 1.7rem); line-height: 1.45; color: var(--text-primary);
  letter-spacing: -0.02em; margin: 0; font-weight: var(--weight-medium); }
.mh-promise p span { color: var(--text-muted); }
.mh-three { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-3); }
.mh-q { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-card); padding: var(--space-6); }
.mh-q .ic { width: 44px; height: 44px; border-radius: var(--radius-md); display: grid; place-items: center; background: var(--accent-subtle); color: var(--accent); }
.mh-q .ic svg { width: 24px; height: 24px; }
.mh-q h3 { font-size: var(--text-lg); margin: var(--space-4) 0 var(--space-1); padding: 0; }
.mh-q p { font-size: var(--text-sm); margin: 0; }
.mh-steps { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; counter-reset: s; }
.mh-step { padding: var(--space-5) var(--space-5) var(--space-5) 0; border-top: 2px solid var(--border-subtle); position: relative; }
.mh-step::before { counter-increment: s; content: "0" counter(s); font-family: var(--font-display); font-weight: var(--weight-semibold);
  font-size: var(--text-sm); color: var(--accent); }
.mh-step::after { content: ""; position: absolute; left: 0; top: -2px; width: 40px; height: 2px; background: var(--accent); }
.mh-step b { display: block; font-family: var(--font-display); font-size: var(--text-md); margin-top: var(--space-2); }
.mh-step span { color: var(--text-secondary); font-size: var(--text-sm); }
@media (max-width: 900px) {
  .st-key-hero { padding: var(--space-6) 0 var(--space-4) !important; }
  .st-key-hero::before { inset: -4% -16px; }
  .mh-promise, .mh-three { grid-template-columns: 1fr; gap: var(--space-4); }
  .mh-steps { grid-template-columns: 1fr 1fr; }
}
</style>
""")

POSTER = (f'<svg viewBox="0 0 260 220" xmlns="http://www.w3.org/2000/svg"><g fill="none" stroke-width="2">'
          f'<path d="M60 108V66a60 18 0 0 1 120 0v42" stroke="{T.CONTROL}" fill="{K.resolve("graphite-800")}"/>'
          f'<path d="M20 110h220" stroke="{T.ACCENT}" stroke-opacity=".6"/>'
          f'<path d="M60 112v42a60 18 0 0 0 120 0v-42" stroke="{T.ACCENT}" stroke-dasharray="3 4" stroke-opacity=".7"/>'
          f'<path d="M80 112v36M100 112v40M120 112v42M140 112v40M160 112v36" stroke="{T.ACCENT}" stroke-opacity=".25"/></g>'
          + "".join(f'<circle cx="{75 + (i * 29) % 90}" cy="{122 + (i * 37) % 32}" r="1.8" fill="{T.ACCENT}" fill-opacity=".7"/>' for i in range(16))
          + "</svg>")
SUBS = {"SUNKEN": T.SUNKEN, "CARD": T.SURFACE, "RAISED": T.RAISED, "LINE": T.LINE, "CONTROL": T.CONTROL, "INK": T.INK,
        "INK2": T.INK_2, "MUTED": T.MUTED, "ACCENT": T.ACCENT, "ON": T.ON_ACCENT, "METAL": K.resolve("graphite-700"),
        "GREEN": T.GOOD, "ROSE": T.D4, "POSTER": POSTER}
scene = (T.ASSETS / "core3d.html").read_text(encoding="utf-8")
for k, v in SUBS.items():
    scene = scene.replace(f"%%{k}%%", v)

with st.container(key="hero"):
    left, right = st.columns([1, 1.2], gap="large", vertical_alignment="center")
    with left:
        ui.md(f"""
<div class="mt-eyebrow">{ui.icon("plant")}Digital twin of a farm biomethane plant</div>
<h1 class="mh-slogan">See your plant work<span class="em">before it exists.</span></h1>
<p class="mh-lede">MethaTwin is a faithful copy of a biomethane plant that you can try ideas on. Change the feed, the tank or
the price of power and get <b>a plain answer in seconds</b>: is the biology healthy, is the gas fit for the grid, does it pay?</p>
""")
        with st.container(horizontal=True, gap="small"):
            with st.container(key="cta", width="content"):
                st.page_link("views/cockpit.py", label="Open your plant")
            with st.container(key="cta2", width="content"):
                st.page_link("views/docs.py", label="How it works")
        ui.md(f'<div class="mh-proof"><span>{ui.icon("shield")}Checked against a benchmark, a lab and the market</span>'
              f'<span>{ui.icon("book")}Public data only</span></div>')
    with right:
        components.html(scene, height=580)

ui.md("""
<section class="mh-promise">
  <div class="k">Our promise</div>
  <p>A biomethane plant is decided once and runs for twenty years. <span>MethaTwin gives farmers, investors and engineers a
  faithful copy of that plant to try ideas on, and answers in plain words whether the microbes stay healthy, whether the gas
  is fit for the grid and whether the plant pays, with every answer traceable to tested science and public data.</span></p>
</section>
""")

ui.section("Three questions, three plain answers", "Every design you try is judged the same way.")
ui.md(f"""
<div class="mh-three">
  <div class="mh-q"><div class="ic">{ui.icon("digester")}</div><h3>Is the biology healthy?</h3>
    <p>Microbes in a warm tank turn slurry and silage into gas. Push them too hard and the tank turns sour; the twin warns you first.</p></div>
  <div class="mh-q"><div class="ic">{ui.icon("scrub")}</div><h3>Is the gas grid-ready?</h3>
    <p>The raw gas is washed with water under pressure until it is almost pure methane. The twin checks it against the network rules.</p></div>
  <div class="mh-q"><div class="ic">{ui.icon("money")}</div><h3>Does the plant pay?</h3>
    <p>Building and running a plant costs money; the gas sold earns it back. The twin weighs both over fifteen years, and against thousands of possible futures.</p></div>
</div>
""")

ui.section("From field to grid", "What the twin follows, step by step.")
ui.md("""
<div class="mh-steps">
  <div class="mh-step"><b>Feed</b><span>Cattle slurry, cover-crop silage and a little maize arrive from the farm.</span></div>
  <div class="mh-step"><b>Digester</b><span>Microbes break the feed down over weeks and release biogas.</span></div>
  <div class="mh-step"><b>Gas cleaning</b><span>Water under pressure removes the CO₂; methane stays in the gas.</span></div>
  <div class="mh-step"><b>Grid</b><span>Clean biomethane flows into the network and heats homes.</span></div>
</div>
""")

ui.section("Where to go next", "Move one setting and watch the rest, replay 2,000 futures, or see every check.")
with st.container(key="doors"):
    c1, c2, c3 = st.columns(3)
    c1.page_link("views/explorer.py", label="Try changes", icon=":material/tune:", width="stretch")
    c2.page_link("views/risk.py", label="What could go wrong", icon=":material/casino:", width="stretch")
    c3.page_link("views/validation.py", label="Why trust it", icon=":material/verified:", width="stretch")
