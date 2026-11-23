"""Record the MethaTwin dashboard tour.

Drives the running Streamlit app with Playwright (headless Chromium, 1920x1080 CSS px at 1.5x density), captures every
painted frame through the Chrome DevTools screencast (2880x1620 JPEG), logs the cursor path (camera.py draws the
cursor at 60 fps), and logs a timeline of
actions and camera directions for camera.py.

    video/.venv/Scripts/python video/record.py            # app must be running on http://localhost:8501
Outputs: video/raw/frames/*.jpg, video/raw/frames.csv, video/timeline.json
"""
from __future__ import annotations

import asyncio
import base64
import json
import math
import shutil
import sys
import time
from pathlib import Path

from playwright.async_api import Locator, Page, async_playwright

URL = "http://localhost:8501"
W, H, DPR = 1920, 1080, 1.5
HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
FRAMES = RAW / "frames"
ACCENT = "#FFB224"          # tokens.py: accent = amber-400
SHADOW = "#0B0B0A"          # tokens.py: graphite-1000
WIDE = 1.3                  # wide shot: the app's centred content column fills the frame
TOPBAR = 84                 # sticky top bar height (CSS px) to keep clear when scrolling

# ----------------------------------------------------------------------------------------------- injected page code ---
INIT_JS = """
(() => {
  if (window.top !== window) return;
  const css = `
    [data-testid="stMain"]::-webkit-scrollbar, html::-webkit-scrollbar { width: 0 !important; height: 0 !important; }
    [data-testid="stMain"] { scrollbar-width: none !important; }
    [data-testid="stAppDeployButton"], [data-testid="stToolbar"], [data-testid="stStatusWidget"], #MainMenu, footer,
    [data-testid="stDecoration"] { display: none !important; }
    #__cur { display: none !important; position: fixed; left: 0; top: 0; width: 30px; height: 30px; z-index: 2147483647; pointer-events: none;
             transform: translate(-100px, -100px); will-change: transform; }
    #__cur svg { width: 30px; height: 30px; overflow: visible; filter: drop-shadow(0 3px 6px rgba(0,0,0,.55)); transition: transform .12s ease; transform-origin: 3px 2px; }
    #__cur.down svg { transform: scale(.82); }
    .__rip { position: fixed; z-index: 2147483646; pointer-events: none; width: 16px; height: 16px; margin: -8px 0 0 -8px; border-radius: 50%;
             border: 2px solid %ACCENT%; opacity: .9; animation: __rip .55s cubic-bezier(.2,.7,.3,1) forwards; }
    @keyframes __rip { to { transform: scale(3.4); opacity: 0; } }`;
  const svg = `<svg viewBox="0 0 30 30"><path d="M3 2 L3 24 L9 18.5 L13 27 L17 25.2 L13 16.8 L21 16.8 Z" fill="%ACCENT%" stroke="%SHADOW%" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
  const add = () => {
    if (!document.documentElement) return;
    if (!document.getElementById("__curcss")) { const s = document.createElement("style"); s.id = "__curcss"; s.textContent = css; document.documentElement.appendChild(s); }
    if (!document.getElementById("__cur")) { const c = document.createElement("div"); c.id = "__cur"; c.innerHTML = svg; document.documentElement.appendChild(c);
      c.style.transform = `translate(${window.__cx - 3}px, ${window.__cy - 2}px)`; }
  };
  window.__cx = -100; window.__cy = -100;
  window.__curSet = (x, y) => { window.__cx = x; window.__cy = y; add(); const c = document.getElementById("__cur");
    c.style.transform = `translate(${x - 3}px, ${y - 2}px)`; };
  window.__press = (down) => { const c = document.getElementById("__cur"); if (!c) return; c.classList.toggle("down", down);
    if (down) { const r = document.createElement("div"); r.className = "__rip"; r.style.left = window.__cx + "px"; r.style.top = window.__cy + "px";
      document.documentElement.appendChild(r); setTimeout(() => r.remove(), 700); } };
  window.__scroller = () => document.querySelector('[data-testid="stMain"]') || document.scrollingElement;
  window.__scrollTo = (target, ms) => new Promise(res => {
    const el = window.__scroller(), y0 = el.scrollTop, y1 = Math.max(0, Math.min(target, el.scrollHeight - el.clientHeight));
    const t0 = performance.now(), e = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const step = now => { const k = Math.min(1, (now - t0) / ms); el.scrollTop = y0 + (y1 - y0) * e(k); k < 1 ? requestAnimationFrame(step) : res(el.scrollTop); };
    requestAnimationFrame(step); });
  new MutationObserver(() => { window.__lastMut = performance.now(); }).observe(document, { subtree: true, childList: true, characterData: true });
  window.__lastMut = performance.now();
  document.addEventListener("DOMContentLoaded", add); setInterval(add, 400);
})();
""".replace("%ACCENT%", ACCENT).replace("%SHADOW%", SHADOW)


def ease(t: float) -> float:
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


class Director:
    """Cursor, actions, scrolling and the timeline log."""

    def __init__(self, page: Page):
        self.p = page
        self.x, self.y = W * 0.62, H * 0.62
        self.t0 = time.time()
        self.events: list[dict] = []
        self.cur: list[tuple] = []                       # cursor path (t, x, y) for camera.py
        self.presses: list[tuple] = []                   # (t, down)

    def press(self, down: bool) -> None:
        self.presses.append((self.t(), down))

    # ------------------------------------------------------------------------------------------------- timeline ---
    def t(self) -> float:
        return round(time.time() - self.t0, 3)

    def log(self, kind: str, **kw) -> None:
        self.events.append({"t": self.t(), "kind": kind, **kw})

    async def box(self, target) -> list[float]:
        if isinstance(target, (list, tuple)):
            if target and isinstance(target[0], (int, float)):
                return list(target)
            bs = [await self.box(x) for x in target]
            x0, y0 = min(b[0] for b in bs), min(b[1] for b in bs)
            x1, y1 = max(b[0] + b[2] for b in bs), max(b[1] + b[3] for b in bs)
            return [x0, y0, x1 - x0, y1 - y0]
        b = await target.bounding_box()
        if b is None:
            raise RuntimeError(f"no box for {target}")
        return [b["x"], b["y"], b["width"], b["height"]]

    async def cam(self, target=None, zoom: float | None = None, dur: float = 0.9, focus=None, hold: float = 0.0,
                  block: bool = True) -> None:
        """Camera direction. target None = the wide shot (content column at WIDE x). zoom None = fit the box."""
        if target is None:
            self.log("cam", box=[0, 0, W, H * 0.77], zoom=WIDE, dur=dur, focus=focus)
        else:
            b = await self.box(target)
            z = min(1.6, zoom or max(WIDE, min(1.6, W / (b[2] * 1.18), H / (b[3] * 1.25))))
            self.log("cam", box=[round(v, 1) for v in b], zoom=round(z, 3), dur=dur, focus=focus)
        if block:
            await self.wait(dur + hold)

    async def wait(self, s: float) -> None:
        await asyncio.sleep(s)

    # ------------------------------------------------------------------------------------------------- cursor -----
    async def move(self, x: float, y: float, ms: float | None = None, arc: float = 0.12) -> None:
        """Eased Bezier move; the real mouse follows so hovers fire along the way."""
        x0, y0 = self.x, self.y
        d = math.hypot(x - x0, y - y0)
        if d < 1:
            return
        ms = ms or max(320, min(700, 220 + d * 0.45))
        nx, ny = -(y - y0) / d, (x - x0) / d                    # perpendicular for a gentle arc
        cx, cy = (x0 + x) / 2 + nx * d * arc, (y0 + y) / 2 + ny * d * arc
        t_start = time.perf_counter()
        while True:
            k = min(1.0, (time.perf_counter() - t_start) * 1000 / ms)
            e = ease(k)
            px = (1 - e) ** 2 * x0 + 2 * (1 - e) * e * cx + e ** 2 * x
            py = (1 - e) ** 2 * y0 + 2 * (1 - e) * e * cy + e ** 2 * y
            self.cur.append((self.t(), round(px, 1), round(py, 1)))
            await self.p.mouse.move(px, py)
            if k >= 1:
                break
            await asyncio.sleep(0.008)
        self.x, self.y = x, y

    async def glide(self, pts: list[tuple[float, float]], ms: float) -> None:
        """Linear glide through points at constant speed (for sweeping across charts)."""
        segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
        total = sum(segs) or 1
        t_start = time.perf_counter()
        while True:
            k = min(1.0, (time.perf_counter() - t_start) * 1000 / ms)
            k = 0.5 - 0.5 * math.cos(math.pi * k)                # soft start and stop
            dist, i = k * total, 0
            while i < len(segs) - 1 and dist > segs[i]:
                dist -= segs[i]
                i += 1
            f = dist / segs[i] if segs[i] else 1
            px = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
            py = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
            self.cur.append((self.t(), round(px, 1), round(py, 1)))
            await self.p.mouse.move(px, py)
            if k >= 1:
                break
            await asyncio.sleep(0.008)
        self.x, self.y = pts[-1]

    async def center(self, loc: Locator, dx: float = 0.5, dy: float = 0.5) -> tuple[float, float]:
        b = await self.box(loc)
        return b[0] + b[2] * dx, b[1] + b[3] * dy

    async def hover(self, loc: Locator, dwell: float = 0.8, dx: float = 0.5, dy: float = 0.5) -> None:
        await self.move(*await self.center(loc, dx, dy))
        self.log("hover", box=await self.box(loc))
        await self.wait(dwell)

    async def click(self, loc: Locator, dx: float = 0.5, dy: float = 0.5, settle: float = 0.5) -> None:
        await self.move(*await self.center(loc, dx, dy))
        await self.wait(0.12)
        self.log("click", box=await self.box(loc))
        self.press(True)
        await self.p.mouse.down()
        await self.wait(0.09)
        await self.p.mouse.up()
        self.press(False)
        await self.wait(settle)

    async def drag(self, x0: float, y0: float, x1: float, y1: float, ms: float = 1200, path=None) -> None:
        await self.move(x0, y0)
        self.press(True)
        await self.p.mouse.down()
        await self.wait(0.12)
        self.log("drag", box=[min(x0, x1) - 40, min(y0, y1) - 40, abs(x1 - x0) + 80, abs(y1 - y0) + 80])
        await self.glide(path or [(x0, y0), (x1, y1)], ms)
        await self.wait(0.1)
        await self.p.mouse.up()
        self.press(False)

    async def type(self, text: str, cps: float = 9) -> None:
        for ch in text:
            await self.p.keyboard.type(ch)
            await self.wait(1 / cps)

    # ------------------------------------------------------------------------------------------------- page -------
    async def scroll_to(self, target, offset: float = TOPBAR + 24, ms: float = 1300) -> None:
        """Smoothly scroll stMain so the target's top sits just under the sticky bar (target: locator or absolute y)."""
        if isinstance(target, (int, float)):
            y = target
        else:
            b = await self.box(target)
            cur = await self.p.evaluate("window.__scroller().scrollTop")
            y = cur + b[1] - offset
        self.log("scroll", y=y)
        await self.p.evaluate("([y,ms]) => window.__scrollTo(y,ms)", [y, ms])
        await self.wait(0.15)

    async def scroll_by(self, dy: float, ms: float = 1300) -> None:
        cur = await self.p.evaluate("window.__scroller().scrollTop")
        await self.scroll_to(cur + dy, ms=ms)

    async def idle(self, quiet: float = 0.6, timeout: float = 25, extra: float = 0.25) -> None:
        """Wait until Streamlit has finished its rerun and the DOM has been quiet for `quiet` seconds."""
        t_end, t_in = time.time() + timeout, self.t()
        await self.wait(0.25)
        while time.time() < t_end:
            busy = await self.p.evaluate("""() => {
                const sw = document.querySelector('[data-testid="stStatusWidget"]');
                const running = !!(sw && /running|connecting/i.test(sw.textContent || ''));
                const spin = !!document.querySelector('[data-testid="stSpinner"], [data-testid="stSkeleton"]');
                const stale = [...document.querySelectorAll('[data-stale="true"]')].length > 0;
                return { running, spin, stale, since: performance.now() - window.__lastMut };
            }""")
            if not (busy["running"] or busy["spin"] or busy["stale"]) and busy["since"] > quiet * 1000:
                break
            await self.wait(0.1)
        if self.t() - t_in > 0.5:
            self.log("idle", t0=t_in, t1=self.t())
        await self.wait(extra)


# ------------------------------------------------------------------------------------------------------- helpers ---
def expander(page: Page, title: str) -> Locator:
    return page.locator('[data-testid="stExpander"] summary').filter(has_text=title).first


def nav(page: Page, key: str) -> Locator:
    return page.locator(f'.st-key-nl_{key} a').first


def slider(page: Page, label: str) -> Locator:
    return page.locator('[data-testid="stSlider"]').filter(has_text=label).first


async def slide(d: Director, label: str, value: float, ms: float = 1500) -> None:
    """Drag a Streamlit slider thumb to `value`, then nudge with the arrow keys to land exactly."""
    s = slider(d.p, label)
    th = s.locator('[role="slider"]')
    lo, hi = float(await th.get_attribute("aria-valuemin")), float(await th.get_attribute("aria-valuemax"))
    tb = await d.box(th)
    track = await d.box(th.locator(".."))
    x0, y = tb[0] + tb[2] / 2, tb[1] + tb[3] / 2
    x1 = track[0] + (value - lo) / (hi - lo) * track[2]
    await d.drag(x0, y, x1, y, ms=ms)
    for _ in range(40):                                   # land on the exact value
        now = float(await th.get_attribute("aria-valuenow"))
        if abs(now - value) < 0.51:
            break
        await th.press("ArrowRight" if now < value else "ArrowLeft")
        await d.wait(0.03)


async def go(d: Director, key: str | None) -> None:
    """Change page from the top bar (it scrolls away on long pages, so glide back to the top first)."""
    top = await d.p.evaluate("window.__scroller().scrollTop")
    if top > 4:
        await d.move(W * 0.5, H * 0.55, ms=500)
        await d.scroll_to(0, ms=min(1600, 700 + top * 0.25))
        await d.wait(0.3)
    link = nav(d.p, key) if key else d.p.locator(".st-key-brand a").first
    if key:                                              # the rail scrolls sideways when the design chip is wide
        await link.evaluate("a => a.scrollIntoView({block: 'nearest', inline: 'nearest', behavior: 'smooth'})")
        await d.wait(0.35)
    await d.click(link, settle=0.2)


# ---------------------------------------------------------------------------------------------------------- tour ---
async def tour(d: Director) -> None:
    """About 50 s: hook -> try an idea -> instant verdict -> explore -> stress-test -> trust -> back to the twin."""
    p = d.p
    ex_body = lambda title: p.locator('[data-testid="stExpander"]').filter(has_text=title).locator('[data-testid="stExpanderDetails"]').first

    # 1 · Start (0-8 s): slogan, the 3D living mirror, Biology / Gas / Money ---------------------------------------------
    slogan, lede = p.locator(".mh-slogan"), p.locator(".mh-lede")
    await d.cam([slogan, p.locator(".mt-eyebrow").first], zoom=1.6, dur=0.01, hold=0.7)
    await d.cam([slogan, lede], zoom=1.35, dur=1.0)
    scene = p.locator("iframe").first
    sb = await d.box(scene)
    await d.cam(scene, zoom=1.4, dur=0.9)
    fr = p.frame_locator("iframe").first
    for k, hold in (("bio", 1.0), ("gas", 1.0), ("money", 1.3)):
        await d.click(fr.locator(f'button[data-k="{k}"]'), settle=hold)
    await d.cam(None, dur=0.7, block=False)
    await d.click(p.locator(".st-key-cta a"), settle=0.1)
    await d.idle(quiet=0.6)

    # 2 · Your plant (8-24 s): verdict; too short a retention time turns it red; back to green; the process diagram -----
    verdict, answers, settings = p.locator(".mt-verdict").first, p.locator(".mt-answers").first, p.locator(".st-key-settings")
    await d.cam([verdict, answers], dur=0.8, hold=0.9)
    await d.cam(settings, zoom=1.5, dur=0.8)
    await slide(d, "Retention time", 45, ms=1100)
    await d.idle(quiet=0.5)
    await d.cam([verdict, answers], dur=0.8, hold=1.3)
    await d.cam(settings, zoom=1.5, dur=0.7)
    await slide(d, "Retention time", 90, ms=900)
    await d.idle(quiet=0.5)
    await d.cam([verdict, answers], dur=0.8, hold=0.9)
    await d.cam(None, dur=0.6, block=False)

    # 3 · Try changes (24-31 s): the two-setting map -------------------------------------------------------------------
    await go(d, "explore")
    await d.idle(quiet=0.6)
    ex = expander(p, "Two settings at once")
    await d.click(ex, dx=0.2, settle=0.1)
    await d.idle(quiet=0.6)
    hm = ex_body("Two settings at once").locator(".js-plotly-plot").first
    await d.scroll_to(hm, offset=60, ms=800)
    hb = await d.box(hm)
    await d.cam(hm, dur=0.8)
    await d.glide([(hb[0] + hb[2] * 0.2, hb[1] + hb[3] * 0.72), (hb[0] + hb[2] * 0.48, hb[1] + hb[3] * 0.38),
                   (hb[0] + hb[2] * 0.78, hb[1] + hb[3] * 0.55)], 2000)
    await d.wait(0.3)
    await d.cam(None, dur=0.7)

    # 4 · What could go wrong (31-40 s): replay 2,000 futures ---------------------------------------------------------
    await go(d, "risks")
    await d.idle(quiet=0.5)
    await d.click(p.get_by_role("button", name="Replay the futures"), settle=0.1)
    await d.wait(0.4)
    await d.idle(quiet=0.6)
    await d.cam(p.locator(".mt-verdict").first, dur=0.8, hold=1.7)
    await d.cam(None, dur=0.6, block=False)

    # 5 · Why trust it (40-45 s) ---------------------------------------------------------------------------------------
    await go(d, "trust")
    await d.idle(quiet=0.5)
    await d.cam([p.locator(".mt-verdict").first, p.locator(".mt-answers").first], dur=0.8, hold=1.4)
    await d.cam(None, dur=0.6)

    # 6 · Back to the twin (45-50 s) -----------------------------------------------------------------------------------
    await go(d, None)
    t_in = d.t()
    await p.frame_locator("iframe").first.locator('button[data-k="bio"]').wait_for(timeout=30000)
    await d.wait(1.4)                                     # three.js builds the scene and the poster fades out
    d.log("idle", t0=t_in, t1=d.t())
    await d.move(W * 0.36, H * 0.93, ms=600)
    await d.cam(p.locator("iframe").first, zoom=1.5, dur=0.01, hold=0.2)
    await d.cam(None, dur=2.0, hold=0.7)


async def main(warm: bool = True) -> None:
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir(parents=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist",
                                                 "--enable-webgl", "--hide-scrollbars", f"--force-device-scale-factor={DPR}"])
        if warm:                                          # warm the server-side caches so no spinner lingers on camera
            wctx = await browser.new_context(viewport={"width": W, "height": H})
            wp = await wctx.new_page()
            for path in ("", "plant", "explore", "risks", "designs", "trust", "how-it-works"):
                await wp.goto(f"{URL}/{path}")
                await wp.wait_for_timeout(6000 if not path else 3500)
            await wctx.close()

        ctx = await browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=DPR)
        await ctx.add_init_script(INIT_JS)
        page = await ctx.new_page()
        await page.goto(URL)
        await page.wait_for_selector(".mh-slogan", timeout=120000)
        fl = page.frame_locator("iframe").first
        await fl.locator('button[data-k="bio"]').wait_for(timeout=60000)
        await page.wait_for_timeout(3500)                 # let three.js settle and the poster fade out

        d = Director(page)
        await page.mouse.move(d.x, d.y)

        cdp = await ctx.new_cdp_session(page)
        index: list[tuple[int, float]] = []

        async def on_frame(ev):
            i = len(index)
            (FRAMES / f"{i:06d}.jpg").write_bytes(base64.b64decode(ev["data"]))
            index.append((i, ev["metadata"]["timestamp"]))
            try:
                await cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
            except Exception:
                pass

        cdp.on("Page.screencastFrame", lambda ev: asyncio.ensure_future(on_frame(ev)))
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": W * DPR, "maxHeight": H * DPR,
                                                 "everyNthFrame": 1})
        await asyncio.sleep(0.5)
        d.t0 = time.time()
        d.log("start")
        try:
            await tour(d)
        finally:
            d.log("end")
            await asyncio.sleep(0.3)
            await cdp.send("Page.stopScreencast")
            await asyncio.sleep(0.5)
            (RAW / "frames.csv").write_text("i,t\n" + "\n".join(f"{i},{t - d.t0:.4f}" for i, t in index))
            (HERE / "timeline.json").write_text(json.dumps({"viewport": [W, H], "dpr": DPR, "events": d.events,
                                                          "cursor": [(round(t - 0, 3), x, y) for t, x, y in d.cur],
                                                          "start_cursor": [W * 0.62, H * 0.62], "presses": d.presses, "wide": WIDE}, indent=0))
            dur = d.events[-1]["t"]
            print(f"recorded {len(index)} frames over {dur:.1f} s ({len(index) / max(dur, 1e-9):.1f} fps average)")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(warm="--no-warm" not in sys.argv))
