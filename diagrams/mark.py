#!/usr/bin/env python3
"""Generate the Symbolic Engineering mark, module icons and home figure.

Contour geometry is generated rather than hand-authored, so the hand-drawn
quality is a parameter (WOBBLE) instead of a redraw, and ring count, drift and
squash stay editable. Run through ../diagrams/render.sh, which also inlines the
output into the pages.

The system rule: ink draws the thing, accent annotates it. Contours and the
filled core are --ink; --accent is only ever an annotation on top — an arrow, a
traced path, a label. That is why the mark is a single colour and the icons
differ from each other only by their one accent gesture.

Colours are emitted as var(--token) so every asset follows the page theme.
"""
import math, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img")

WOBBLE = 0.13          # pencil, not crayon: 0.07 reads as sloppy print, 0.22 as playful
WEIGHTS = [1.0, 0.86, 1.06, 0.92, 1.0, 0.88]      # pencil pressure per level


def phases(seed, k=3):
    """Deterministic harmonic phases, shared across a mark's levels so the
    relief reads as one landform rather than unrelated blobs."""
    return [((seed * (i + 7) * 2654435761) % 10000) / 10000 * math.tau
            for i in range(k)]


def ring(cx, cy, r, wobble, ph, squash=0.9, n=13):
    pts = []
    for i in range(n):
        a = math.tau * i / n
        d = (0.60 * math.sin(2 * a + ph[0])
             + 0.30 * math.sin(3 * a + ph[1])
             + 0.18 * math.sin(5 * a + ph[2]))
        rr = r * (1 + wobble * d)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * squash))
    return pts


def smooth(pts, open_end=False):
    """Catmull-Rom as cubic beziers. open_end drops the closing segment: a drawn
    line does not meet itself perfectly, and that detail plus per-level weight
    variation carries the pencil without a filter, a gradient or a raster."""
    n = len(pts)
    segs = n - 1 if open_end else n
    d = f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"
    for i in range(segs):
        p0, p1 = pts[(i - 1) % n], pts[i % n]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += (f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f}"
              f" {p2[0]:.2f},{p2[1]:.2f}")
    return d + ("" if open_end else " Z")


def relief(cx, cy, radii, seed, drift=(-3.0, -3.4), sw=2.0, squash=0.9,
           n=13, core=True, colour="var(--ink)", wobble=WOBBLE):
    """Nested contours, inner levels drifting toward the peak so the mark has a
    direction instead of reading as a target. The innermost level is filled
    rather than stroked: it is the same curve every outer line is an offset of,
    so the mark states one shape and the levels propagate it."""
    ph, rmin = phases(seed), min(radii)
    out = []
    for k, r in enumerate(radii):
        t = 1 - r / max(radii)
        pts = ring(cx + drift[0] * t, cy + drift[1] * t, r, wobble, ph, squash, n)
        if core and r == rmin:
            out.append(f'<path d="{smooth(pts)}" fill="{colour}"/>')
            continue
        out.append(f'<path d="{smooth(pts, True)}" fill="none" stroke="{colour}" '
                   f'stroke-width="{sw * WEIGHTS[k % len(WEIGHTS)]:.2f}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
    return "\n  ".join(out)


def level(cx, cy, radii, seed, r, drift, squash=0.9, n=13):
    t = 1 - r / max(radii)
    return ring(cx + drift[0] * t, cy + drift[1] * t, r, WOBBLE,
                phases(seed), squash, n)


def arc(pts, i0, i1, sw=2.3):
    seg = [pts[i % len(pts)] for i in range(i0, i1 + 1)]
    d = f"M{seg[0][0]:.2f},{seg[0][1]:.2f}"
    for i in range(len(seg) - 1):
        p0, p3 = seg[max(i - 1, 0)], seg[min(i + 2, len(seg) - 1)]
        p1, p2 = seg[i], seg[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += (f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f}"
              f" {p2[0]:.2f},{p2[1]:.2f}")
    return (f'<path d="{d}" fill="none" stroke="var(--accent)" '
            f'stroke-width="{sw}" stroke-linecap="round"/>')


# ---------------------------------------------------------------- the mark
# Two cuts. Five levels mud below about 32px, and the mark has to hold at 17px
# in the header and 16px as a favicon.
BIG, SMALL = [30, 24, 18, 12.5, 7], [10.4, 7, 3.8]

# ---------------------------------------------------------------- module icons
# One shared base so the family is obvious and only the accent gesture differs.
# Each gesture is a different *kind* of mark — a line that stops, arcs that
# spread, a cut straight through, one thing off the lines — so they stay apart
# at 36px.
IB, ID = [29, 22, 15, 8.5], (-2.8, -3.2)


def ibase():
    return relief(34, 34, IB, 3, drift=ID, sw=1.9)


def ipts(r):
    return level(34, 34, IB, 3, r, ID)


ICONS = {
    "icon-model-context-layer": lambda: ibase() + "\n  " + (
        '<path d="M64,58 L43,42" stroke="var(--accent)" stroke-width="2.4" '
        'stroke-linecap="round"/>'),
    "icon-failure-propagation": lambda: "\n  ".join(
        [ibase(), arc(ipts(15), 8, 13), arc(ipts(22), 8, 14, 2.1),
         arc(ipts(29), 9, 14, 1.9)]),
    "icon-reliability-engineering": lambda: ibase() + "\n  " + (
        '<path d="M7,52 L61,20" stroke="var(--accent)" stroke-width="2.4" '
        'stroke-linecap="round"/>'
        '<path d="M5,48 L10,55.5" stroke="var(--accent)" stroke-width="2.2" '
        'stroke-linecap="round"/>'
        '<path d="M58,16.5 L63,24" stroke="var(--accent)" stroke-width="2.2" '
        'stroke-linecap="round"/>'),
    "icon-sensor-intelligence": lambda: "\n  ".join(
        [ibase()]
        + [f'<circle cx="{ipts(r)[i][0]:.1f}" cy="{ipts(r)[i][1]:.1f}" r="2.6" '
           f'fill="var(--muted)"/>' for r, i in ((29, 3), (22, 10), (15, 6))]
        + ['<circle cx="57" cy="13" r="5" fill="none" stroke="var(--accent)" '
           'stroke-width="2.2"/>',
           '<circle cx="57" cy="13" r="1.9" fill="var(--accent)"/>']),
}

# ------------------------------------------------------- ingestion categories
# Categories, not vendor logos: says the same thing, owns the artwork, carries
# no trademark question, and stays true when a connector is added.


def cat_warehouse():
    return "\n  ".join(
        f'<path d="M9,{20 + i*9:.0f} L24,{12.5 + i*9:.0f} L39,{20 + i*9:.0f} '
        f'L24,{27.5 + i*9:.0f} Z" fill="var(--panel)" stroke="var(--ink)" '
        f'stroke-width="1.6" stroke-linejoin="round"/>' for i in range(3))


def cat_stream():
    ph, out = phases(23), []
    for i in range(3):
        pts = [(6 + t * 3.6, 20 + i * 9 + 3.4 * math.sin(t / 2.6 + ph[i]))
               for t in range(11)]
        out.append('<path d="M' + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                   + '" fill="none" stroke="var(--ink)" stroke-width="1.9" '
                     'stroke-linecap="round"/>')
    out.append('<circle cx="40.5" cy="29" r="3.2" fill="var(--accent)"/>')
    return "\n  ".join(out)


def cat_historian():
    out = []
    for i in range(4):
        pts = [(7 + t * 3.4, 40 - i * 7 - 5.5
                * math.exp(-((t - 5.5) ** 2) / 9) * (1 + 0.2 * i))
               for t in range(11)]
        out.append('<path d="M' + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                   + '" fill="none" stroke="var(--ink)" stroke-width="1.7" '
                     'stroke-linecap="round"/>')
    return "\n  ".join(out)


def cat_records():
    out = [f'<rect x="{10 + i*2}" y="{14 + i*8}" width="28" height="7" '
           f'fill="var(--panel)" stroke="var(--ink)" stroke-width="1.7"/>'
           for i in range(3)]
    out.append('<path d="M14,44 L34,44" stroke="var(--accent)" '
               'stroke-width="2" stroke-linecap="round"/>')
    return "\n  ".join(out)


CATS = [("cat-warehouse", cat_warehouse), ("cat-stream", cat_stream),
        ("cat-historian", cat_historian), ("cat-records", cat_records)]
CAT_LABELS = ["Warehouse", "Event stream", "Historian", "Maintenance records"]


# ---------------------------------------------------------------- home figure

def hero():
    """Sources feed one relief; the filled core is the governed model. Accent
    leaves it exactly twice — once as the answer, once dashed on the way back
    through the operations that produced the figure (lineage) to the records
    those operations read (provenance). Two different guarantees, both named."""
    # 860 wide so the figure fills the 860px measure at its natural size. It used
    # to be 720, which left it short of the text and header; widening beats
    # scaling up, because scaling magnifies the figure's own labels too.
    W, H, cx, cy = 860, 350, 584, 176
    # n scales with the drawing so the deliberate gap where a drawn line fails
    # to meet itself stays a hairline instead of opening into a visible break
    # innermost level is tighter than the mark's proportion: filled ink at this
    # scale reads as a heavy blob otherwise
    out = [relief(cx, cy, [132, 106, 81, 56, 28], 3, drift=(-9, -10),
                  sw=2.2, n=29)]

    # Each source is named. Two typographic registers keep that from becoming
    # noise: the categories are sentence-case sans, because they are content;
    # the annotation layer below is mono uppercase. "What you already run" is
    # gone — with the four named, a label saying so was restating them.
    ENDS = [(477, 120), (462, 157), (462, 195), (477, 232)]
    for i, (name, fn) in enumerate(CATS):
        gy = 26 + i * 78
        out.append(f'<g transform="translate(16,{gy}) scale(0.86)">{fn()}</g>')
        y, (ex, ey) = gy + 26, ENDS[i]
        out.append(f'<text x="68" y="{y + 4}" font-size="11" '
                   f'fill="var(--muted)">{CAT_LABELS[i]}</text>')
        out.append(f'<path d="M176,{y:.0f} C280,{y:.0f} 380,{ey} {ex},{ey}" '
                   f'fill="none" stroke="var(--rule)" stroke-width="1.4"/>')

    out.append(f'<path d="M{cx + 12},{cy - 30} L790,74" stroke="var(--accent)" '
               f'stroke-width="2.2" stroke-linecap="round"/>')
    out.append('<circle cx="796" cy="70" r="5.4" fill="var(--accent)"/>')
    out.append(f'<path d="M{cx - 26},{cy + 14} C480,255 250,310 62,304" '
               f'fill="none" stroke="var(--accent)" stroke-width="2" '
               f'stroke-dasharray="5 5" stroke-linecap="round"/>')
    # the trace lands on a record rather than trailing off
    out.append('<circle cx="62" cy="304" r="4.4" fill="var(--accent)"/>')

    # Both annotations sit below the line they annotate, clear of the feeders.
    lbl = ('font:500 10px ui-monospace,SFMono-Regular,Menlo,monospace;'
           'letter-spacing:.1em;text-transform:uppercase')
    for x, y, fill, txt in [
            (516, 332, "var(--muted)", "One governed model"),
            (700, 46, "var(--accent)", "Answer"),
            (420, 272, "var(--accent)", "Lineage"),
            (118, 326, "var(--accent)", "Provenance")]:
        out.append(f'<text x="{x}" y="{y}" style="{lbl}" fill="{fill}">'
                   f'{txt}</text>')
    return "\n  ".join(out), W, H


# ---------------------------------------------------------------- emit

def write(name, body, w, h, attrs="", title=None):
    t = f'\n  <title>{title}</title>' if title else ''
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
           f'fill="none"{attrs}>{t}\n  {body}\n</svg>\n')
    path = os.path.join(OUT, f"{name}.svg")
    with open(path, "w") as f:
        f.write(svg)
    return len(svg)


def favicon():
    """The <link rel="icon"> line, built from the same three-level cut as the
    header so there is one source for every instance of the mark.

    A data URI cannot resolve custom properties, and the mark is ink — which
    disappears against dark browser chrome. So the colours are literal and an
    embedded media query swaps them for dark.

    The light colours are presentation attributes, not CSS. Safari's support for
    styles inside an SVG favicon is unreliable, and with the light rules in the
    stylesheet a browser that ignored it drew the contours with no stroke at all
    — leaving only the filled core, which looks like a different icon rather than
    a degraded one. As attributes they always render, and the media query still
    wins where it is honoured.

    Single-quoted throughout, because this sits inside an href="…"."""
    body = relief(12, 12, SMALL, 3, drift=(-1.1, -1.2), sw=1.7)
    body = (body.replace('"', "'")
                .replace("fill='none' stroke='var(--ink)'",
                         "class='s' fill='none' stroke='%2314110F'")
                .replace("fill='var(--ink)'", "class='k' fill='%2314110F'")
                .replace("\n  ", ""))
    style = ("@media(prefers-color-scheme:dark){"
             ".s{stroke:%23EDEAE4}.k{fill:%23EDEAE4}}")
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
           f"<style>{style}</style>{body}</svg>")
    return f'<link rel="icon" href="data:image/svg+xml,{svg}">\n'


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    with open(os.path.join(OUT, "favicon.html"), "w") as f:
        f.write(favicon())
    # The header mark carries its own size; everything else is sized by CSS.
    n += write("mark-sm", relief(12, 12, SMALL, 3, drift=(-1.1, -1.2), sw=1.7),
               24, 24, ' width="17" height="17" aria-hidden="true"')
    n += write("mark-lg", relief(34, 34, BIG, 3), 68, 68,
               ' aria-hidden="true"', "Symbolic Engineering")
    for name, fn in ICONS.items():
        n += write(name, fn(), 68, 68, ' aria-hidden="true"')
    for name, fn in CATS:
        n += write(name, fn(), 48, 58, ' aria-hidden="true"')
    body, w, h = hero()
    n += write("hero", body, w, h, ' style="max-width:860px" role="img"',
               "Your source systems resolved into one governed model, with an "
               "answer traced back through its lineage to the records it came "
               "from")
    print(f"  marks + icons + hero      {2 + len(ICONS) + len(CATS) + 1} files,"
          f" {n} bytes")


if __name__ == "__main__":
    main()
