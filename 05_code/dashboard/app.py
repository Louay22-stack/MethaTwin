"""
MethaTwin - interactive digital twin of an agricultural biomethane plant (application entry point).

Architecture
  app.py        application shell: page config, top bar (brand, navigation, current-design chip), footer
  state.py      shared session state, reference designs, scenarios, cached evaluations
  core.py       model layer: ML surrogates of the ADM1 + DWSIM chain and the CRE-anchored TEA
  tokens.py     design tokens: primitive -> semantic -> component
  theme.py      brand marks, global CSS built from the tokens, Plotly template
  ui.py         interface components, icon set, plain-language status logic, process flow diagram
  views/*.py    one file per page

Run from the project root:
    streamlit run 05_code/dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import theme as T  # noqa: E402

st.set_page_config(page_title="MethaTwin · See your plant work before it exists", page_icon=str(T.FAVICON),
                   layout="wide", initial_sidebar_state="collapsed")
st.markdown(T.CSS, unsafe_allow_html=True)

import state as S  # noqa: E402
import ui  # noqa: E402

try:
    S.sur()
except FileNotFoundError as e:                       # error state: models missing
    ui.md(f'<div class="mt-head">{T.wordmark("1.6rem")}</div>')
    ui.verdict("bad", "Cannot start", "The trained models were not found.", str(e))
    st.code("python 05_code/step6b_surrogate.py", language="powershell")
    st.stop()

S.init()

# ------------------------------------------------------------------ pages ---
V = HERE / "views"
HOME = st.Page(str(V / "home.py"), title="Start", default=True)
PLANT = st.Page(str(V / "cockpit.py"), title="Your plant", url_path="plant")
PAGES = [HOME, PLANT,
         st.Page(str(V / "explorer.py"), title="Try changes", url_path="explore"),
         st.Page(str(V / "risk.py"), title="What could go wrong", url_path="risks"),
         st.Page(str(V / "library.py"), title="Designs", url_path="designs"),
         st.Page(str(V / "validation.py"), title="Why trust it", url_path="trust"),
         st.Page(str(V / "docs.py"), title="How it works", url_path="how-it-works")]
pg = st.navigation(PAGES, position="hidden")
SHORT = {"What could go wrong": "Risks", "Why trust it": "Trust"}   # compact labels for the rail

if msg := st.session_state.pop("_toast", None):
    st.toast(msg, icon=":material/check_circle:")

# ------------------------------------------------------------------ top bar ---
on_home = pg.title == "Start"
with st.container(key="topbar", horizontal=True, vertical_alignment="center"):
    with st.container(key="brand", width="content"):
        st.page_link(HOME, label="MethaTwin")
    with st.container(key="navrail", horizontal=True, vertical_alignment="center", width="stretch"):
        for p in PAGES[1:]:
            with st.container(key=f"nl_{p.url_path.replace('-', '_')}", width="content"):
                st.page_link(p, label=SHORT.get(p.title, p.title))
    # Streamlit does not expose the current page on the link, so the active item is styled from here
    cur = (pg.url_path or "home").replace("-", "_")
    ui.md(f'<style>.st-key-nl_{cur} [data-testid="stPageLink"] a {{ background: var(--nav-item-active-bg) !important; }}'
          f'.st-key-nl_{cur} [data-testid="stPageLink"] a p {{ color: var(--nav-item-active-fg) !important; }}</style>')
    with st.container(key="navmenu", width="content"):
        with st.popover("Menu", icon=":material/menu:"):
            for p in PAGES:
                st.page_link(p, label=p.title)
    if not on_home:
        k, word = ui.status(S.evaluate())["overall"]
        ref = S.matches_reference()
        name = st.session_state.preset.replace("Verified optimum", "Optimum").split(" (")[0]
        mod = "" if ref else '<span class="mod">changed</span>'
        with st.container(key="chip", horizontal=True, vertical_alignment="center", width="content"):
            ui.md(f'<span class="mt-chip" title="Current design">{ui.pill(k, word)}'
                  f'<span class="nm">from <b>{name}</b></span>{mod}</span>')
            if pg.title != "Your plant":
                st.page_link(PLANT, label="Change")

pg.run()

ui.md(f'<div class="mt-foot" role="contentinfo"><span>{T.wordmark("1rem")}&nbsp;&nbsp;See your plant work before it exists.</span>'
      '<span>Model predictions from public data, not investment advice.</span></div>')
