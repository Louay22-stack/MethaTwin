"""MethaTwin design tokens (v4 "Signal"): primitive -> semantic -> component.

Rules
* Primitives hold raw values only. Nothing outside this file uses them directly.
* Semantic tokens give a purpose to a primitive ("text-muted", "status-ok-fg").
* Component tokens bind a semantic token to one component ("verdict-ok-border").
* theme.py emits all three layers as CSS custom properties; component CSS uses var(--...) only.
* Python code that cannot use CSS (Plotly, inline SVG) calls resolve("semantic-or-component-name").

Contrast (WCAG 2.x, on graphite-950 / 900 / 850): text-primary 16.3 / 15.2 / 13.7, text-secondary 10.9 / 10.1 / 9.1,
text-muted 6.7 / 6.2 / 5.6, accent 10.4 / 9.6 / 8.7, status ok 10.1, warn 8.3, bad 6.8; data series all >= 7:1;
text-on-accent on accent 10.4. border-control 3.2:1 on graphite-900 (non-text UI component).
"""
from __future__ import annotations

import json
import re

# ------------------------------------------------------------------------------------------- primitive ---
PRIMITIVE: dict[str, str] = {
    # warm graphite ramp
    "graphite-1000": "#0B0B0A", "graphite-950": "#121212", "graphite-900": "#1B1A18", "graphite-850": "#25231F",
    "graphite-800": "#2E2B26", "graphite-700": "#3A3731", "graphite-600": "#6E685D", "graphite-500": "#A09A8E",
    "graphite-300": "#CBC5B8", "graphite-100": "#F3EFE6",
    # signal amber
    "amber-300": "#FFC95C", "amber-400": "#FFB224", "amber-500": "#E89A0C", "amber-900": "#33270F",
    # status hues
    "green-400": "#5DD39E", "green-950": "#173126", "green-800": "#2E5A45",
    "orange-400": "#FF8F5A", "orange-950": "#3A2217", "orange-800": "#6B3A22",
    "red-400": "#FF6B7A", "red-950": "#3A1A1F", "red-800": "#6E2A33",
    # data hues
    "sky-400": "#74B9FF", "sage-400": "#9AD38B", "rose-400": "#F48FB1",
    # space (4-pt)
    "space-1": "4px", "space-2": "8px", "space-3": "12px", "space-4": "16px", "space-5": "20px", "space-6": "24px",
    "space-8": "32px", "space-10": "40px", "space-12": "48px", "space-16": "64px", "space-20": "80px",
    # radius
    "radius-sm": "8px", "radius-md": "12px", "radius-lg": "16px", "radius-xl": "24px", "radius-pill": "999px",
    # type
    "font-sora": "'Sora', 'Manrope', 'Segoe UI', system-ui, sans-serif",
    "font-manrope": "'Manrope', 'Segoe UI', system-ui, sans-serif",
    "size-12": "0.75rem", "size-14": "0.875rem", "size-16": "1rem", "size-18": "1.125rem", "size-22": "1.375rem",
    "size-28": "1.75rem", "size-36": "2.25rem", "size-hero": "clamp(2.4rem, 5.6vw, 4.4rem)",
    "weight-regular": "400", "weight-medium": "500", "weight-semibold": "600", "weight-bold": "700",
    # motion
    "duration-120": "120ms", "duration-200": "200ms", "duration-320": "320ms", "duration-600": "600ms",
    "ease-out": "cubic-bezier(.2,.8,.2,1)",
}

# ------------------------------------------------------------------------------------------- semantic ---
SEMANTIC: dict[str, str] = {
    "surface-sunken": "graphite-1000", "surface-canvas": "graphite-950", "surface-card": "graphite-900",
    "surface-raised": "graphite-850", "surface-hover": "graphite-800",
    "border-subtle": "graphite-700", "border-control": "graphite-600",
    "text-primary": "graphite-100", "text-secondary": "graphite-300", "text-muted": "graphite-500",
    "text-on-accent": "graphite-950",
    "accent": "amber-400", "accent-hover": "amber-300", "accent-pressed": "amber-500", "accent-subtle": "amber-900",
    "focus-ring": "amber-400",
    "status-ok-fg": "green-400", "status-ok-bg": "green-950", "status-ok-border": "green-800",
    "status-warn-fg": "orange-400", "status-warn-bg": "orange-950", "status-warn-border": "orange-800",
    "status-bad-fg": "red-400", "status-bad-bg": "red-950", "status-bad-border": "red-800",
    "status-info-fg": "graphite-300", "status-info-bg": "graphite-850", "status-info-border": "graphite-700",
    "data-1": "amber-400", "data-2": "sky-400", "data-3": "sage-400", "data-4": "rose-400", "data-muted": "graphite-600",
    "font-display": "font-sora", "font-body": "font-manrope",
    "text-xs": "size-12", "text-sm": "size-14", "text-md": "size-16", "text-lg": "size-18", "text-xl": "size-22",
    "text-2xl": "size-28", "text-3xl": "size-36", "text-hero": "size-hero",
    "gap-xs": "space-1", "gap-sm": "space-2", "gap-md": "space-4", "gap-lg": "space-6", "gap-xl": "space-10",
    "gap-section": "space-16",
    "radius-control": "radius-sm", "radius-card": "radius-lg", "radius-panel": "radius-xl", "radius-round": "radius-pill",
    "motion-fast": "duration-120", "motion-base": "duration-200", "motion-slow": "duration-320",
    "motion-scene": "duration-600", "motion-ease": "ease-out",
}

# ------------------------------------------------------------------------------------------ component ---
COMPONENT: dict[str, str] = {
    "page-bg": "surface-canvas",
    "topbar-bg": "surface-canvas", "topbar-border": "border-subtle",
    "nav-item-fg": "text-secondary", "nav-item-hover-bg": "surface-raised", "nav-item-active-fg": "text-on-accent",
    "nav-item-active-bg": "accent",
    "chip-bg": "surface-card", "chip-border": "border-subtle", "chip-fg": "text-secondary",
    "card-bg": "surface-card", "card-border": "border-subtle", "card-radius": "radius-card",
    "card-hover-border": "border-control",
    "verdict-bg": "surface-card", "verdict-title-font": "font-display",
    "verdict-ok-border": "status-ok-border", "verdict-warn-border": "status-warn-border", "verdict-bad-border": "status-bad-border",
    "answer-bg": "surface-card", "answer-border": "border-subtle",
    "reveal-bg": "surface-card", "reveal-border": "border-subtle", "reveal-hover-border": "border-control",
    "reveal-open-bg": "surface-card",
    "button-primary-bg": "accent", "button-primary-fg": "text-on-accent", "button-primary-hover-bg": "accent-hover",
    "button-secondary-bg": "surface-raised", "button-secondary-fg": "text-primary", "button-secondary-border": "border-control",
    "input-bg": "surface-raised", "input-border": "border-control", "input-fg": "text-primary",
    "slider-track": "border-subtle", "slider-fill": "accent", "slider-thumb": "accent",
    "tooltip-bg": "surface-raised", "tooltip-fg": "text-primary", "tooltip-border": "border-control",
    "term-underline": "accent",
    "hero-bg": "surface-sunken",
    "chart-grid": "surface-hover", "chart-axis": "border-subtle", "chart-tick": "text-muted", "chart-title": "text-primary",
    "chart-bg": "surface-card", "chart-current": "accent", "chart-reference": "text-primary",
}

LAYERS = (PRIMITIVE, SEMANTIC, COMPONENT)


def resolve(name: str) -> str:
    """Raw value of any token, following semantic and component references down to the primitive."""
    for _ in range(4):
        if name in COMPONENT:
            name = COMPONENT[name]
        elif name in SEMANTIC:
            name = SEMANTIC[name]
        elif name in PRIMITIVE:
            return PRIMITIVE[name]
        else:
            raise KeyError(name)
    raise RecursionError(name)


def css_vars() -> str:
    """All three layers as CSS custom properties; upper layers reference lower ones with var()."""
    out = [f"  --{k}: {v};" for k, v in PRIMITIVE.items()]
    out += [f"  --{k}: var(--{v});" for k, v in SEMANTIC.items()]
    out += [f"  --{k}: var(--{v});" for k, v in COMPONENT.items()]
    return ":root {\n" + "\n".join(out) + "\n}"


def rgba(name: str, alpha: float) -> str:
    h = resolve(name).lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def to_dtcg() -> dict:
    """W3C Design Tokens (DTCG) export, used for design-system/methatwin/tokens.json."""
    def typ(v: str) -> str:
        if v.startswith("#"):
            return "color"
        if re.fullmatch(r"[\d.]+(px|rem|ms)", v):
            return "duration" if v.endswith("ms") else "dimension"
        return "fontFamily" if "'" in v else "other"
    return {"primitive": {k: {"$value": v, "$type": typ(v)} for k, v in PRIMITIVE.items()},
            "semantic": {k: {"$value": "{primitive." + v + "}"} for k, v in SEMANTIC.items()},
            "component": {k: {"$value": "{semantic." + v + "}" if v in SEMANTIC else "{primitive." + v + "}"}
                          for k, v in COMPONENT.items()}}


if __name__ == "__main__":
    print(json.dumps(to_dtcg(), indent=2))
