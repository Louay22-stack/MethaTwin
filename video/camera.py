"""Virtual camera pass: turns the raw 4K capture + timeline into the final LinkedIn videos.

    video/.venv/Scripts/python video/camera.py [--stills 2.5,30,61,96] [--preview]

* Resamples the variable-rate screencast to a constant 60 fps (latest frame at or before each tick).
* Camera: every "cam" event in timeline.json eases (cubic in-out) from the current framing to the new one over its
  duration; the framing is interpolated as a rectangle, so zoom and pan move together and never leave the page.
* 16:9 (1920x1080) inside a thin rounded frame on graphite; 4:5 (1080x1350) follows the action (camera centre when
  zoomed, last action point otherwise, smoothed).
* H.264 yuv420p CRF 18, no audio. --preview renders every 4th second at low cost for checking.
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
FPS = 60
BG = (10, 11, 11)                     # graphite-1000 #0B0B0A in BGR
EDGE = (38, 43, 46)                   # graphite-800 #2E2B26 in BGR
ACCENT = (36, 178, 255)               # amber-400 #FFB224 in BGR
INK = (10, 11, 11)                    # cursor outline
ARROW = np.array([(0, 0), (0, 22), (6, 16.5), (10, 25), (14, 23.2), (10, 14.8), (18, 14.8)], np.float32)   # tip at (0,0), CSS px


class Cursor:
    """The amber arrow, drawn per output frame from the logged path (so it moves at a true 60 fps), with a click ripple."""

    def __init__(self, tl):
        c = tl.get("cursor") or []
        self.t = np.array([r[0] for r in c] or [0.0])
        self.x = np.array([r[1] for r in c] or [tl.get("start_cursor", [0, 0])[0]])
        self.y = np.array([r[2] for r in c] or [tl.get("start_cursor", [0, 0])[1]])
        x0, y0 = tl.get("start_cursor", [self.x[0], self.y[0]])
        self.t, self.x, self.y = np.r_[-1.0, self.t], np.r_[x0, self.x], np.r_[y0, self.y]
        self.press = tl.get("presses") or []
        self.downs = [t for t, d in self.press if d]

    def at(self, t):
        return float(np.interp(t, self.t, self.x)), float(np.interp(t, self.t, self.y))

    def is_down(self, t):
        st = False
        for tt, d in self.press:
            if tt > t:
                break
            st = d
        return st

    def draw(self, img: np.ndarray, t: float, rect, ow: int, oh: int) -> None:
        """Draw onto a content image of size (oh, ow) that shows page `rect` (CSS px)."""
        x, y = self.at(t)
        s = ow / rect[2]
        px, py = (x - rect[0]) * s, (y - rect[1]) * s
        if not (-40 < px < ow + 40 and -40 < py < oh + 40):
            return
        for td in self.downs:                            # ripple, 0.55 s
            k = (t - td) / 0.55
            if 0 <= k <= 1:
                rx, ry = self.at(td)
                cx, cy = (rx - rect[0]) * s, (ry - rect[1]) * s
                r = (8 + 22 * (1 - (1 - k) ** 3)) * s
                ov = img.copy()
                cv2.circle(ov, (int(cx * 4), int(cy * 4)), int(r * 4), ACCENT, max(1, int(2.2 * s)), cv2.LINE_AA, shift=2)
                a = 0.9 * (1 - k)
                cv2.addWeighted(ov, a, img, 1 - a, 0, img)
        sc = 1.15 * s * (0.84 if self.is_down(t) else 1.0)
        pts = ARROW * sc + (px, py)
        sh = img.copy()
        cv2.fillPoly(sh, [np.round((pts + (1.5 * s, 3 * s)) * 16).astype(np.int32)], (0, 0, 0), cv2.LINE_AA, shift=4)
        cv2.addWeighted(sh, 0.35, img, 0.65, 0, img)
        poly = [np.round(pts * 16).astype(np.int32)]
        cv2.fillPoly(img, poly, ACCENT, cv2.LINE_AA, shift=4)
        cv2.polylines(img, poly, True, INK, max(1, int(round(1.5 * s))), cv2.LINE_AA, shift=4)


def ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


# ------------------------------------------------------------------------------------------------------- camera ---
class Camera:
    def __init__(self, events: list[dict], W: int, H: int):
        self.W, self.H = W, H
        self.keys = []                                   # (t_start, dur, rect_from, rect_to)
        cur = (0.0, 0.0, float(W), float(H))
        for e in events:
            if e["kind"] != "cam":
                continue
            to = self.rect(e["box"], e["zoom"])
            self.keys.append((e["t"], max(e["dur"], 1e-3), None, to))
        # resolve the "from" rect of each move as the camera position when that move starts
        out = []
        for t0, dur, _, to in self.keys:
            frm = self._at(out, t0, cur)
            out.append((t0, dur, frm, to))
        self.keys = out
        # focus points for the vertical crop: every action and camera box
        self.focus = sorted((e["t"], e["box"][0] + e["box"][2] / 2, e["box"][1] + e["box"][3] / 2)
                            for e in events if "box" in e and e["kind"] in ("click", "hover", "drag", "cam") and e["box"][2] < W * 0.99)

    def rect(self, box, z) -> tuple:
        W, H = self.W, self.H
        w, h = W / z, H / z
        cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
        x0 = min(max(cx - w / 2, 0), W - w)
        y0 = min(max(cy - h / 2, 0), H - h)
        return (x0, y0, w, h)

    @staticmethod
    def _at(keys, t, default):
        r = default
        for t0, dur, frm, to in keys:
            if t < t0:
                break
            k = ease((t - t0) / dur)
            r = tuple(a + (b - a) * k for a, b in zip(frm, to))
        return r

    def at(self, t: float) -> tuple:
        return self._at(self.keys, t, (0.0, 0.0, float(self.W), float(self.H)))


class Follow:
    """Critically damped follow of the latest focus point (for the 4:5 crop when the 16:9 camera is wide)."""

    def __init__(self, focus, W, H):
        self.f, self.W, self.H = focus, W, H
        self.x, self.y, self.t = W / 2, H / 2, 0.0

    def at(self, t):
        i = bisect.bisect_right([f[0] for f in self.f], t) - 1
        tx, ty = (self.f[i][1], self.f[i][2]) if i >= 0 else (self.W / 2, self.H / 2)
        a = 1 - math.exp(-(t - self.t) / 0.45)
        self.x += (tx - self.x) * a
        self.y += (ty - self.y) * a
        self.t = t
        return self.x, self.y


# ------------------------------------------------------------------------------------------------------ framing ---
def rounded_mask(w: int, h: int, r: int) -> np.ndarray:
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)):
        cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return m


class Frame:
    """A content area inset in a dark canvas with rounded corners, a hairline edge and a soft shadow."""

    def __init__(self, ow: int, oh: int, inset: int, radius: int):
        self.ow, self.oh, self.inset = ow, oh, inset
        self.cw, self.ch = ow - 2 * inset, oh - 2 * inset
        m = rounded_mask(self.cw, self.ch, radius)
        canvas = np.full((oh, ow, 3), BG, np.float32)
        sh = np.zeros((oh, ow), np.float32)
        sh[inset + 10: inset + 10 + self.ch, inset: inset + self.cw] = m / 255.0
        sh = cv2.GaussianBlur(sh, (0, 0), 22) * 0.55
        canvas *= (1 - sh[..., None])
        edge = np.zeros((oh, ow), np.uint8)
        edge[inset - 1: inset - 1 + self.ch + 2, inset - 1: inset - 1 + self.cw + 2] = rounded_mask(self.cw + 2, self.ch + 2, radius + 1)
        e = edge.astype(np.float32)[..., None] / 255
        self.canvas = canvas * (1 - e) + np.array(EDGE, np.float32) * e
        self.alpha = (np.zeros((oh, ow), np.float32))
        self.alpha[inset: inset + self.ch, inset: inset + self.cw] = m / 255.0
        self.alpha = self.alpha[..., None]

    def compose(self, content: np.ndarray) -> np.ndarray:
        full = np.zeros((self.oh, self.ow, 3), np.float32)
        full[self.inset: self.inset + self.ch, self.inset: self.inset + self.cw] = content
        return (self.canvas * (1 - self.alpha) + full * self.alpha).astype(np.uint8)


COLUMN = (373, 0, 1174, 1080)          # the app's centred content column at 1920 px (CSS px)
APP_BG = (18, 18, 18)                 # graphite-950 #121212: pads the 4:5 frame above and below wide shots


def crop(img: np.ndarray, rect, dpr: float, ow: int, oh: int) -> np.ndarray:
    """Render page rect (CSS px, may extend past the page: padded with the app background) to ow x oh."""
    x, y, w, h = (v * dpr for v in rect)
    s = ow / w
    if s < 1:                                            # area-downscale first so small text stays clean
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        x, y, w, h, k = x * s, y * s, w * s, h * s, 1.0
    else:
        k = s
    M = np.float32([[k, 0, -x * k], [0, k, -y * k]])
    return cv2.warpAffine(img, M, (ow, oh), flags=cv2.INTER_CUBIC if k > 1 else cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=APP_BG)


class TimeWarp:
    """Replaces every logged Streamlit wait (rerun, page switch, Monte Carlo) with a short crossfade between the last
    settled frame before it and the first settled frame after it, so no loading state ever reaches the screen."""
    PRE, OUT = 0.2, 0.35                                 # take the 'before' frame PRE s before the wait; fade length

    def __init__(self, events, t_end):
        segs, cur = [], 0.0
        for e in sorted((e for e in events if e["kind"] == "idle"), key=lambda e: e["t0"]):
            a, b = max(e["t0"] - self.PRE, cur), e["t1"]
            if b - a > 0.15:
                segs.append((cur, a, None)); segs.append((a, b, "fade")); cur = b
        segs.append((cur, t_end, None))
        self.map, o = [], 0.0                            # (out_start, out_len, src_start, src_end, kind)
        for a, b, kind in segs:
            n = self.OUT if kind else (b - a)
            self.map.append((o, n, a, b, kind)); o += n
        self.out_end = o

    def src(self, tau):
        """-> (source time for camera and cursor, (t_a, t_b, k) crossfade or None)."""
        for o, n, a, b, kind in reversed(self.map):
            if tau >= o:
                k = min(1.0, (tau - o) / n) if n else 1.0
                if kind == "fade":
                    return a + (b - a) * k, (a, b, ease(k))
                return min(b, a + (tau - o)), None
        return 0.0, None


def encoder(path: Path, w: int, h: int) -> subprocess.Popen:
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
           "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", str(path)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default="", help="comma-separated times (s) to export as PNG from the 16:9 video")
    ap.add_argument("--preview", action="store_true", help="dump a JPEG every 2 s of output to video/frames_check instead of encoding")
    a = ap.parse_args()

    tl = json.loads((HERE / "timeline.json").read_text())
    W, H = tl["viewport"]
    dpr = tl["dpr"]
    ev = tl["events"]
    t_end = next(e["t"] for e in ev if e["kind"] == "end")
    rows = [line.split(",") for line in (RAW / "frames.csv").read_text().splitlines()[1:]]
    ft = [float(r[1]) for r in rows]

    cam = Camera(ev, W, H)
    cursor = Cursor(tl)
    wide = tl.get("wide", 1.0)
    fol = Follow(cam.focus, W, H)
    f169 = Frame(1920, 1080, 28, 14)
    f45 = Frame(1080, 1350, 22, 14)
    stills = sorted(float(s) for s in a.stills.split(",") if s.strip())

    out_dir = HERE / "frames_check"
    if a.preview:
        out_dir.mkdir(exist_ok=True)
        for f in out_dir.glob("*.jpg"):
            f.unlink()
    enc = None if a.preview else (encoder(HERE / "methatwin_16x9.mp4", 1920, 1080), encoder(HERE / "methatwin_4x5.mp4", 1080, 1350))

    warp = TimeWarp(ev, t_end)
    n_out = int(warp.out_end * FPS)
    cache: dict[int, np.ndarray] = {}

    def load(i: int) -> np.ndarray:
        if i not in cache:
            if len(cache) > 6:
                cache.pop(next(iter(cache)))
            cache[i] = cv2.imread(str(RAW / "frames" / f"{i:06d}.jpg"), cv2.IMREAD_COLOR)
        return cache[i]
    print(f"source {t_end:.1f} s -> output {warp.out_end:.1f} s")
    fade_in, fade_out = 0.5, 0.9
    for k in range(n_out):
        tau = k / FPS
        t, fade = warp.src(tau)
        if a.preview and (k % (2 * FPS)) and not any(abs(tau - s) < 0.5 / FPS for s in stills):
            fol.at(t)
            continue
        if fade:
            ia, ib = (max(0, bisect.bisect_right(ft, x) - 1) for x in fade[:2])
            img_a, img_b = load(ia), load(ib)
            cache_img = cv2.addWeighted(img_a, 1 - fade[2], img_b, fade[2], 0) if ia != ib else img_a
        else:
            cache_img = load(max(0, bisect.bisect_right(ft, t) - 1))
        r = cam.at(t)
        c169 = crop(cache_img, r, dpr, f169.cw, f169.ch)
        cursor.draw(c169, t, r, f169.cw, f169.ch)
        a169 = f169.compose(c169.astype(np.float32))

        # 4:5 — wide shots show the whole content column (padded above and below with the app background);
        # zoomed shots crop tightly around the camera target
        z = W / r[2]
        fol.at(t)
        blend = min(1.0, max(0.0, (z - wide) / 0.25))
        w_wide, w_zoom = COLUMN[2] + 70, min(COLUMN[2] + 70, r[2] * 0.72)
        w45 = (1 - blend) * w_wide + blend * w_zoom
        h45 = w45 * f45.ch / f45.cw
        cx = (1 - blend) * (COLUMN[0] + COLUMN[2] / 2) + blend * (r[0] + r[2] / 2)
        cy = (1 - blend) * (H / 2) + blend * (r[1] + r[3] / 2)
        x0 = min(max(cx - w45 / 2, 0), W - w45)
        y0 = cy - h45 / 2 if h45 >= H else min(max(cy - h45 / 2, 0), H - h45)
        c45 = crop(cache_img, (x0, y0, w45, h45), dpr, f45.cw, f45.ch)
        cursor.draw(c45, t, (x0, y0, w45, h45), f45.cw, f45.ch)
        a45 = f45.compose(c45.astype(np.float32))

        g = min(1.0, tau / fade_in, (warp.out_end - tau) / fade_out)
        if g < 1:
            a169 = (a169 * max(g, 0)).astype(np.uint8)
            a45 = (a45 * max(g, 0)).astype(np.uint8)
        if a.preview:
            cv2.imwrite(str(out_dir / f"t{tau:05.1f}.jpg"), a169, [cv2.IMWRITE_JPEG_QUALITY, 85])
            cv2.imwrite(str(out_dir / f"t{tau:05.1f}_45.jpg"), cv2.resize(a45, (540, 675)), [cv2.IMWRITE_JPEG_QUALITY, 80])
        else:
            enc[0].stdin.write(a169.tobytes())
            enc[1].stdin.write(a45.tobytes())
        for s in stills:
            if abs(tau - s) < 0.5 / FPS:
                cv2.imwrite(str(HERE / f"still_{s:05.1f}s.png"), a169)
        if k % (10 * FPS) == 0:
            print(f"  {tau:6.1f} / {warp.out_end:.1f} s", flush=True)
    if enc:
        for e in enc:
            e.stdin.close()
            e.wait()
    print(f"done: {n_out / FPS:.1f} s at {FPS} fps")


if __name__ == "__main__":
    main()
