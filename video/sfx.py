"""Sound pass: a synthesized mouse click on every cursor press and release, muxed into the rendered videos.

    video/.venv/Scripts/python video/sfx.py

The click is generated here (no sample files): a short filtered-noise transient plus a damped plastic 'body'
resonance. The press is a little louder and lower than the release. Times come from timeline.json and are mapped
through camera.py's TimeWarp, so they land on the exact output frame. The picture is not re-encoded
(the video stream is copied); the silent originals are kept as *_silent.mp4.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

from camera import TimeWarp

HERE = Path(__file__).resolve().parent
SR = 48000
rng = np.random.default_rng(7)


def click(press: bool) -> np.ndarray:
    n = int(SR * 0.06)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = np.diff(noise, prepend=0)                   # tilt towards the highs: a crisp tick
    tick = noise * np.exp(-t / (0.0016 if press else 0.0012))
    f1, f2 = (2300, 4100) if press else (2900, 5200)    # plastic shell resonances
    body = (np.sin(2 * np.pi * f1 * t) * np.exp(-t / 0.010) * 0.55
            + np.sin(2 * np.pi * f2 * t) * np.exp(-t / 0.005) * 0.30)
    thump = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.006) * (0.35 if press else 0.15)
    x = tick * 0.6 + body + thump
    x *= np.minimum(1, t / 0.0003)                       # no DC click at the start
    x /= np.abs(x).max()
    return x * (0.42 if press else 0.26)                 # peaks about -7.5 / -11.7 dBFS


def out_time(warp: TimeWarp, t: float) -> float:
    for o, n, a, b, kind in warp.map:
        if a <= t <= b:
            return o + (t - a) / (b - a) * n if b > a else o
    return t


def main() -> None:
    tl = json.loads((HERE / "timeline.json").read_text())
    ev = tl["events"]
    t_end = next(e["t"] for e in ev if e["kind"] == "end")
    warp = TimeWarp(ev, t_end)
    n = int(SR * (warp.out_end + 0.5))
    track = np.zeros((n, 2))
    sounds = {True: click(True), False: click(False)}
    placed = []
    for t, down in tl["presses"]:
        s = sounds[down]
        i = int(out_time(warp, t) * SR)
        if 0 <= i < n - len(s):
            pan = 0.5 + 0.12 * rng.uniform(-1, 1)        # a hint of stereo width
            track[i:i + len(s), 0] += s * (1 - pan) * 2 * 0.9
            track[i:i + len(s), 1] += s * pan * 2 * 0.9
            placed.append(round(i / SR, 2))
    track = np.clip(track, -0.98, 0.98)
    wav = HERE / "raw" / "clicks.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes((track * 32767).astype("<i2").tobytes())

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    for name in ("methatwin_16x9", "methatwin_4x5"):
        src, silent = HERE / f"{name}.mp4", HERE / f"{name}_silent.mp4"
        if not silent.exists():
            shutil.copy2(src, silent)
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(src)],
                       check=True)
    print(f"{len(placed)} click sounds at", placed)


if __name__ == "__main__":
    main()
