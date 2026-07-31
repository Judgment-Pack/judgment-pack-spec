#!/usr/bin/env python3
"""Deterministic hand-drawn SVG primitives.

The site ships static, JavaScript-free SVGs. These helpers produce the wobbly,
ink-on-paper look of the README diagram without a drawing library and without a
webfont: the *shapes* are hand-drawn (jittered paths, doubled strokes, open
corners) while the labels stay in the site's own sans stack.

Randomness is a seeded LCG so a rebuild produces byte-identical output.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

INK = "#152426"
MUTED = "#566466"
PAPER = "#ffffff"


class Pen:
    """A seeded pseudo-random pen. Same seed, same wobble, every run."""

    def __init__(self, seed: int = 7) -> None:
        self._state = seed & 0xFFFFFFFF

    def _next(self) -> float:
        # Numerical Recipes LCG; deterministic across Python versions.
        self._state = (1664525 * self._state + 1013904223) & 0xFFFFFFFF
        return self._state / 0xFFFFFFFF

    def jitter(self, amount: float) -> float:
        return (self._next() - 0.5) * 2.0 * amount


def _fmt(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _pt(x: float, y: float) -> str:
    return f"{_fmt(x)},{_fmt(y)}"


def rough_line(pen: Pen, x1: float, y1: float, x2: float, y2: float, wobble: float = 1.6) -> str:
    """One stroke drawn as a quadratic curve bowed slightly off true."""
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    # Bow perpendicular to the run, so the wobble reads as an unsteady hand
    # rather than as a misplaced endpoint.
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length
    bow = pen.jitter(wobble)
    cx, cy = mx + nx * bow, my + ny * bow
    return (
        f"M{_pt(x1 + pen.jitter(wobble * 0.4), y1 + pen.jitter(wobble * 0.4))} "
        f"Q{_pt(cx, cy)} {_pt(x2 + pen.jitter(wobble * 0.4), y2 + pen.jitter(wobble * 0.4))}"
    )


def rough_rect(
    pen: Pen,
    x: float,
    y: float,
    w: float,
    h: float,
    wobble: float = 3.0,
    passes: int = 2,
) -> str:
    """A box sketched in `passes` overlapping strokes per side."""
    segments = []
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    for _ in range(passes):
        for index in range(4):
            ax, ay = corners[index]
            bx, by = corners[(index + 1) % 4]
            segments.append(rough_line(pen, ax, ay, bx, by, wobble))
    return " ".join(segments)


def rough_region(
    pen: Pen,
    x: float,
    y: float,
    w: float,
    h: float,
    wobble: float = 3.0,
) -> str:
    """One continuous closed outline of the same box, for a pale fill.

    The stroked version is several disjoint subpaths, which fills into a mess —
    a wash needs a single closed loop of its own.
    """
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    parts = [f"M{_pt(x + pen.jitter(wobble * 0.4), y + pen.jitter(wobble * 0.4))}"]
    for index in range(4):
        ax, ay = corners[index]
        bx, by = corners[(index + 1) % 4]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        length = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / length, (bx - ax) / length
        bow = pen.jitter(wobble)
        parts.append(
            f"Q{_pt(mx + nx * bow, my + ny * bow)} "
            f"{_pt(bx + pen.jitter(wobble * 0.4), by + pen.jitter(wobble * 0.4))}"
        )
    return " ".join(parts) + " Z"


def rough_arrow(
    pen: Pen,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    wobble: float = 1.4,
    head: float = 9.0,
) -> str:
    """A shaft plus two hand-drawn barbs — no marker, so it scales cleanly."""
    shaft = rough_line(pen, x1, y1, x2, y2, wobble)
    angle = math.atan2(y2 - y1, x2 - x1)
    barbs = []
    for spread in (2.6, -2.6):
        bx = x2 + head * math.cos(angle + spread)
        by = y2 + head * math.sin(angle + spread)
        barbs.append(rough_line(pen, x2, y2, bx, by, wobble * 0.5))
    return shaft + " " + " ".join(barbs)


def underline(pen: Pen, x: float, y: float, w: float) -> str:
    """The scribbled emphasis rule under a heading."""
    return rough_line(pen, x, y, x + w, y, 1.2) + " " + rough_line(pen, x, y + 1.5, x + w, y + 1.5, 1.2)


@dataclass(frozen=True)
class Text:
    x: float
    y: float
    value: str
    size: float = 13
    weight: str = "400"
    anchor: str = "middle"
    fill: str = INK

    def render(self) -> str:
        return (
            f'<text x="{_fmt(self.x)}" y="{_fmt(self.y)}" text-anchor="{self.anchor}" '
            f'font-size="{_fmt(self.size)}" font-weight="{self.weight}" fill="{self.fill}">'
            f"{escape(self.value)}</text>"
        )


def escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def document(
    *,
    width: float,
    height: float,
    slug: str,
    title: str,
    desc: str,
    body: str,
) -> str:
    """Wrap drawn content in the accessible, self-describing envelope the site uses."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_fmt(width)} {_fmt(height)}" '
        f'role="img" aria-labelledby="{slug}-t {slug}-d" '
        'font-family="Inter, ui-sans-serif, system-ui, -apple-system, \'Segoe UI\', sans-serif">\n'
        f"  <title id=\"{slug}-t\">{escape(title)}</title>\n"
        f"  <desc id=\"{slug}-d\">{escape(desc)}</desc>\n"
        f"{body}\n"
        "</svg>\n"
    )


def ink(path: str, width: float = 1.9, color: str = INK, opacity: float = 1.0) -> str:
    return (
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{_fmt(width)}" '
        f'stroke-linecap="round" stroke-linejoin="round" opacity="{_fmt(opacity)}"/>'
    )


def wash(path: str, color: str) -> str:
    """A pale fill behind a sketched box, for the one or two boxes that matter."""
    return f'<path d="{path}" fill="{color}" stroke="none" opacity="0.55"/>'
