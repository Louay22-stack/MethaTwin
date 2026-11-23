# MethaTwin: LinkedIn screen video

A 45.7 s, text-free tour of the dashboard. A camera zooms in on the details as they happen, an amber cursor drives the app, and the only sound is a mouse click on every press.

| File | What it is |
|---|---|
| `methatwin_16x9.mp4` | 1920×1080, 60 fps, H.264 (yuv420p, CRF 18), AAC stereo with the click sounds |
| `methatwin_4x5.mp4` | 1080×1350 version for the LinkedIn mobile feed (same cut; wide shots show the whole content column) |
| `*_silent.mp4` | The same two videos with no audio track |
| `still_*.png` | Four 1920×1080 frames for the post thumbnail |
| `record.py` | Drives the app and captures the raw footage + `timeline.json` |
| `camera.py` | Camera pass: zooms, cursor, crossfades over loading waits, encoding |
| `sfx.py` | Sound pass: synthesized mouse clicks on every press and release, muxed in without re-encoding the picture |
| `timeline.json` | Every action, camera move and wait of the last recording, plus the cursor path |

## Shot list (16:9 output time)

| Time | Section | What happens |
|---|---|---|
| 0.0–8.6 s | Start | Push-in on the slogan, then the 3D living mirror; Biology, Gas and Money light up the twin; "Open your plant" |
| 8.6–22.0 s | Your plant | Verdict and three answers; retention time dragged to 45 days, the verdict turns red ("Needs changes", biology unstable); back to 90 days, green again |
| 22.0–31.6 s | Try changes | The biggest lever, then the two-setting map; the cursor sweeps it and the tooltip follows |
| 31.6–37.5 s | What could go wrong | "Replay the futures": 2,000 futures, zoom on "It pays in about 1 of 10 futures" |
| 37.5–41.7 s | Why trust it | "12 of 16 checks pass fully", with the benchmark, hand-check and market-match answers |
| 41.7–45.7 s | Close | Back to the start; slow pull-back from the 3D twin |

## How it is made

1. **Capture.** Headless Chromium at 1920×1080 CSS px and 1.5× density, captured through the Chrome DevTools screencast as 2880×1620 JPEGs. That's about 60 fps while the page moves, and nothing while it is still. Each frame is time-stamped. The extra resolution keeps zooms up to 1.6× sharp. Streamlit's toolbar, status widget and scrollbars are hidden.
2. **Timeline.** Every click, hover, drag, scroll, camera direction and Streamlit wait is logged with its time and the target element's box. The cursor path is logged at about 100 Hz.
3. **Camera.** Each camera move eases (cubic in-out) from the current framing to the next. The framing is interpolated as a rectangle, so zoom and pan move together and stay on the page. The wide shot frames the app's centered content column at 1.3×.
4. **Cursor.** The amber arrow and its click ripple are drawn in post from the logged path, so they move at a true 60 fps.
5. **No loading on screen.** Every logged wait (rerun, page switch, Monte Carlo) becomes a 0.35 s crossfade from the last settled frame to the next one.
6. **Encoding.** Both formats come from one pass, with ffmpeg (bundled by `imageio-ffmpeg`) and libx264.
7. **Clicks.** `sfx.py` generates the click in code: a filtered-noise tick and a damped plastic resonance, with the release softer and higher than the press. It places one at every logged press and release, mapped through the same time warp, so each sound lands on its click ripple (onsets within 10 ms; peak −8.4 dBFS). The video stream is copied, not re-encoded.

## Re-run

```powershell
python -m venv video/.venv
video/.venv/Scripts/python -m pip install playwright opencv-python numpy imageio-ffmpeg
video/.venv/Scripts/python -m playwright install chromium
```

Start the app (`streamlit run 05_code/dashboard/app.py --server.headless true --server.port 8501`), then:

```powershell
video/.venv/Scripts/python video/record.py
```

```powershell
video/.venv/Scripts/python video/camera.py --preview
```

```powershell
video/.venv/Scripts/python video/camera.py
```

```powershell
video/.venv/Scripts/python video/sfx.py
```

- `record.py` takes about 1.5 min. It warms the app's caches first, then records about 58 s of raw footage into `video/raw/` (git-ignored).
- `camera.py --preview` writes a frame every 2 s to `video/frames_check/` for a quick look.
- `camera.py` with no flags renders both MP4s (about 10 min).
- `sfx.py` adds the clicks (a few seconds) and keeps the silent versions as `*_silent.mp4`.

To change the story, edit `tour()` in `record.py`. Each `d.cam(target, zoom, dur, hold)` is a camera direction; `d.cam(None)` is the wide shot.

## Notes

- The tour uses the default design, "Verified optimum · 200 Nm³/h". The risk verdict ("about 1 of 10 futures") is the model's real result under the uncertain prices and biology. It was not tuned for the video.
- At 1920 px, once the design is changed, the current-design chip in the top bar grows and pushes "Trust" and "How it works" out of the scrolling nav rail. The recorder scrolls the rail before clicking; the app itself could give the rail more room.
