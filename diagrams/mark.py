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


def open_d(seg):
    """Catmull-Rom through a run of points that does not close. The end tangents
    are clamped rather than wrapped, which smooth() cannot do: it treats the
    list as a ring, so on an open stroke the first and last segments would be
    aimed at the point at the other end of the line."""
    d = f"M{seg[0][0]:.2f},{seg[0][1]:.2f}"
    for i in range(len(seg) - 1):
        p0, p3 = seg[max(i - 1, 0)], seg[min(i + 2, len(seg) - 1)]
        p1, p2 = seg[i], seg[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += (f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f}"
              f" {p2[0]:.2f},{p2[1]:.2f}")
    return d


def arc(pts, i0, i1, sw=2.3):
    seg = [pts[i % len(pts)] for i in range(i0, i1 + 1)]
    return (f'<path d="{open_d(seg)}" fill="none" stroke="var(--accent)" '
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


# ------------------------------------------------------------- sector glyphs
# The home's three failure cards. These sit in the same register as the
# ingestion categories, not the relief: the relief is Contour, and these three
# pictures are the customer's own world before Contour is in it. Ink draws what
# they already have; the single accent marks the thing they cannot pin down.
#
# One gesture each, and a different *kind* of gesture — a ring around a figure,
# a filled node, a cap on one column — so they stay apart at 34px.

def sector_payments():
    """Provider events, ledgers, bank feeds: many strands, one figure they add
    up to. The strands stop short of the ring because the definition that would
    close the gap is the thing nobody has made durable."""
    # the strands finish parallel and a hair apart rather than meeting at a
    # point: three feeds that nearly agree, which is the actual complaint
    out = [f'<path d="M6,{y} C16,{y} 19,{e} 25.5,{e}" fill="none" '
           f'stroke="var(--ink)" stroke-width="1.8" stroke-linecap="round"/>'
           for y, e in ((9, 21.6), (39, 26.4))]
    out.append('<path d="M6,24 L27,24" fill="none" stroke="var(--ink)" '
               'stroke-width="1.8" stroke-linecap="round"/>')
    out.append('<circle cx="35.6" cy="24" r="5.4" fill="none" '
               'stroke="var(--accent)" stroke-width="2.2"/>')
    return "\n  ".join(out)


def sector_reliability():
    """The plant as a dependency graph rather than a list of tags. Four ink
    assets, and the accent one is the asset whose failure is coming."""
    nodes = [(11, 13), (11, 35), (25, 24), (39, 34)]
    out = [f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="var(--ink)" '
           f'stroke-width="1.5"/>'
           for a, b in [(nodes[0], nodes[2]), (nodes[1], nodes[2]),
                        (nodes[2], (39, 14)), (nodes[2], nodes[3])]]
    out += [f'<circle cx="{x}" cy="{y}" r="4" fill="var(--panel)" '
            f'stroke="var(--ink)" stroke-width="1.7"/>' for x, y in nodes]
    out.append('<circle cx="39" cy="14" r="4.6" fill="var(--accent)"/>')
    return "\n  ".join(out)


def sector_funds():
    """Positions, exposure, segments, revenue standing side by side, and the
    accent on the one figure the firm is being asked to defend."""
    out = [f'<path d="M{9 + i * 7.5:.1f},38 L{9 + i * 7.5:.1f},{38 - h}" '
           f'stroke="var(--ink)" stroke-width="3.4"/>'
           for i, h in enumerate((13, 25, 8, 20, 16))]
    out.append('<path d="M6,41.6 L42,41.6" stroke="var(--ink)" '
               'stroke-width="1.6" stroke-linecap="round"/>')
    out.append('<path d="M12.6,11.4 L20.4,11.4" stroke="var(--accent)" '
               'stroke-width="2.4" stroke-linecap="round"/>')
    return "\n  ".join(out)


SECTORS = [("sector-payments", sector_payments),
           ("sector-reliability", sector_reliability),
           ("sector-funds", sector_funds)]


# --------------------------------------------------------------- the reach pair
# "Start" opens with the same relief drawn twice: once with its centre missing,
# once with it filled. The contours are the systems the reader already runs, and
# the only difference between the two drawings is the thing we sell — which is
# the one place on the site where the mark is allowed to carry an argument
# rather than just sit there being the mark.
# the core is a quarter of the outer level, as it is in the mark: any smaller
# and the thing the whole figure is about reads as a speck
RR, RC, RD = [54, 43, 32, 21], 14, (-7.5, -8.5)


def _reach_contours():
    """The outer levels alone. core=False keeps the innermost stroked open like
    the rest, because the core is drawn separately in both states."""
    return relief(60, 60, RR, 3, drift=RD, sw=2.0, n=21, core=False)


def _reach_core():
    return smooth(level(60, 60, RR, 3, RC, RD, n=21))


def relief_open():
    return _reach_contours() + "\n  " + (
        f'<path d="{_reach_core()}" fill="none" stroke="var(--accent)" '
        f'stroke-width="2.1" stroke-dasharray="5 5" stroke-linecap="round"/>')


def relief_closed():
    return _reach_contours() + "\n  " + (
        f'<path d="{_reach_core()}" fill="var(--ink)"/>')


def reach_arrow():
    """A drawn line rather than a ruled one: one and a half slow waves, so the
    crossing reads as a hand moving between the two states instead of a UI
    chevron. The head is aimed along the final tangent, and pathLength
    normalises both strokes to 1 so the stylesheet can draw them on scroll with
    one stroke-dashoffset keyframe and no measuring."""
    n = 17
    pts = [(4 + 78 * i / (n - 1),
            12 - 3.5 * math.sin(math.tau * 1.5 * i / (n - 1)))
           for i in range(n)]
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    head = [(x1 + 8 * math.cos(a + t), y1 + 8 * math.sin(a + t))
            for t in (math.radians(148), math.radians(-148))]
    return "\n  ".join([
        f'<path d="{open_d(pts)}" pathLength="1" fill="none" '
        f'stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round"/>',
        f'<path d="M{head[0][0]:.2f},{head[0][1]:.2f} L{x1:.2f},{y1:.2f} '
        f'L{head[1][0]:.2f},{head[1][1]:.2f}" pathLength="1" fill="none" '
        f'stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'])


# ------------------------------------------------------------- the question
# "Bring us your expensive questions" asks the reader for the problem they are
# stuck on, so the section is marked by punctuation. This one stays entirely in
# ink: the marks are content, not annotation.

WAVER = 0.58     # units of deviation in a 68 box: a pen's drift, not a lurch


def query():
    """Question and exclamation points, waved perpendicular to the stroke rather
    than radially.

    Radial wobble at the contours' own setting was the first attempt and it read
    as crooked. A relief gets away with a 13% swing because five nested lines
    swing together and the eye takes the irregularity as landform; one line has
    no neighbours to corroborate it, so the same amplitude just looks badly
    drawn. Here the deviation runs along the length of the stroke — two slow
    harmonics, under a pixel at the size it is used — which is what a steady hand
    with a pen actually produces."""

    def waved(points, seed, amount=1.0):
        ph, m, out = phases(seed), len(points), []
        for i, (x, y) in enumerate(points):
            t = i / (m - 1)
            env = min(1.0, 3.0 * t, 3.0 * (1.0 - t))
            w = env * (0.62 * math.sin(math.tau * 1.4 * t + ph[0])
                       + 0.38 * math.sin(math.tau * 2.5 * t + ph[1]))
            ax, ay = points[max(i - 1, 0)]
            bx, by = points[min(i + 1, m - 1)]
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy) or 1.0
            out.append((x - dy / L * WAVER * amount * w,
                        y + dx / L * WAVER * amount * w))
        return out

    question = [
        (15.2, 31.4), (15.1, 27.4), (16.9, 23.4), (20.2, 20.4),
        (24.6, 19.0), (29.0, 19.7), (32.4, 22.2), (34.1, 25.8),
        (33.7, 29.4), (31.5, 32.1), (28.4, 34.2), (26.1, 36.8),
        (25.3, 40.7), (24.6, 44.2)
    ]
    exclaim = [(61.2, 38.7), (60.5, 44.1), (59.5, 49.7), (58.3, 55.1)]

    question_dot = ring(24.5, 52.0, 3.0, WOBBLE * 0.45, phases(11),
                        squash=1.0, n=9)
    exclaim_dot = ring(58.3, 64.3, 3.2, WOBBLE * 0.45, phases(19),
                       squash=1.0, n=9)
    return "\n  ".join([
        f'<path d="{open_d(waved(question, 11))}" fill="none" '
        f'stroke="var(--ink)" stroke-width="2.7" stroke-linecap="round" '
        f'stroke-linejoin="round"/>',
        f'<path d="{open_d(waved(exclaim, 19, 0.8))}" fill="none" '
        f'stroke="var(--ink)" stroke-width="3.1" stroke-linecap="round" '
        f'stroke-linejoin="round"/>',
        f'<path d="{smooth(question_dot)}" fill="var(--ink)"/>',
        f'<path d="{smooth(exclaim_dot)}" fill="var(--ink)"/>'])


# ------------------------------------------------------------- Linear B tablet

def linear_tablet():
    """A tablet as an image of decipherment, not archaeology decoration. The
    signs are deliberately schematic: what matters is that the marks become
    legible when they are tied to place, quantity and ordinary records."""
    ph = phases(31)

    def waved(points, seed, amount=1.0):
        p, n, out = phases(seed), len(points), []
        for i, (x, y) in enumerate(points):
            t = i / max(n - 1, 1)
            w = (0.55 * math.sin(math.tau * 1.3 * t + p[0])
                 + 0.45 * math.sin(math.tau * 2.2 * t + p[1]))
            ax, ay = points[max(i - 1, 0)]
            bx, by = points[min(i + 1, n - 1)]
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy) or 1.0
            out.append((x - dy / L * WOBBLE * 3.8 * amount * w,
                        y + dx / L * WOBBLE * 3.8 * amount * w))
        return out

    outline = []
    for i in range(28):
        a = math.tau * i / 28
        # Superellipse-like tablet with a chipped upper-left corner.
        c, s = math.cos(a), math.sin(a)
        x = 180 + math.copysign(abs(c) ** 0.58, c) * 148
        y = 130 + math.copysign(abs(s) ** 0.62, s) * 94
        chip = max(0, 1 - math.hypot(x - 55, y - 46) / 46)
        wob = 1 + WOBBLE * (0.45 * math.sin(3 * a + ph[0])
                            + 0.25 * math.sin(7 * a + ph[1]))
        outline.append((180 + (x - 180) * wob + 18 * chip,
                        130 + (y - 130) * wob + 8 * chip))

    out = [
        f'<path d="{smooth(outline)}" fill="var(--panel)" '
        f'stroke="var(--ink)" stroke-width="2.2" stroke-linejoin="round"/>'
    ]

    rows = [
        [(74, 70, 0), (110, 68, 3), (148, 70, 1), (188, 68, 5),
         (230, 70, 2), (268, 69, 4)],
        [(86, 104, 2), (126, 102, 5), (170, 104, 4), (210, 102, 0),
         (252, 104, 3)],
        [(76, 138, 5), (116, 137, 1), (160, 139, 0), (203, 137, 2),
         (246, 139, 5), (286, 138, 4)],
        [(91, 173, 3), (136, 171, 4), (180, 173, 1), (222, 171, 0),
         (264, 173, 2)]
    ]

    def add_path(points, seed, sw=2.0, colour="var(--ink)"):
        out.append(f'<path d="{open_d(waved(points, seed))}" fill="none" '
                   f'stroke="{colour}" stroke-width="{sw}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')

    def glyph(x, y, kind, seed):
        s = 1.0
        if kind == 0:
            add_path([(x, y - 12*s), (x - 3*s, y), (x - 5*s, y + 13*s)],
                     seed)
            add_path([(x - 12*s, y - 2*s), (x, y - 7*s), (x + 12*s, y - 2*s)],
                     seed + 1, 1.7)
        elif kind == 1:
            add_path([(x - 12*s, y - 9*s), (x - 2*s, y - 14*s),
                      (x + 10*s, y - 7*s), (x + 8*s, y + 5*s),
                      (x - 6*s, y + 10*s), (x - 12*s, y + 1*s)],
                     seed)
        elif kind == 2:
            add_path([(x - 11*s, y - 11*s), (x + 8*s, y + 10*s)], seed)
            add_path([(x + 10*s, y - 9*s), (x - 7*s, y + 12*s)], seed + 1)
        elif kind == 3:
            add_path([(x, y - 13*s), (x, y + 13*s)], seed)
            add_path([(x, y - 3*s), (x - 12*s, y - 10*s)], seed + 1, 1.7)
            add_path([(x, y + 3*s), (x + 13*s, y - 4*s)], seed + 2, 1.7)
        elif kind == 4:
            add_path([(x - 12*s, y - 8*s), (x + 11*s, y - 8*s),
                      (x + 6*s, y + 10*s), (x - 8*s, y + 10*s),
                      (x - 12*s, y - 8*s)], seed)
        else:
            for k in range(3):
                add_path([(x - 9*s + k * 8*s, y - 12*s),
                          (x - 12*s + k * 8*s, y + 12*s)],
                         seed + k, 1.7)

    for ridx, row in enumerate(rows):
        ybase = row[0][1]
        add_path([(62, ybase + 22), (294, ybase + 22)], 71 + ridx, 0.9,
                 "var(--rule)")
        for cidx, (x, y, kind) in enumerate(row):
            glyph(x, y, kind, 100 + ridx * 13 + cidx)

    # The accent is the act of decipherment: a suspected group of signs is tied
    # to ordinary geography rather than left as isolated marks.
    out.append('<ellipse cx="112" cy="68" rx="42" ry="22" fill="none" '
               'stroke="var(--accent)" stroke-width="2" '
               'stroke-dasharray="5 5"/>')
    add_path([(154, 66), (198, 48), (246, 44), (286, 58)], 211, 2.0,
             "var(--accent)")
    out.append('<circle cx="292" cy="60" r="5.2" fill="var(--accent)"/>')

    return "\n  ".join(out)


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
    for name, fn in SECTORS:
        n += write(name, fn(), 48, 48, ' aria-hidden="true"')
    n += write("relief-open", relief_open(), 120, 120, ' role="img"',
               "The same contours with nothing at the centre")
    n += write("relief-closed", relief_closed(), 120, 120, ' role="img"',
               "The same contours resolved into one filled centre")
    n += write("reach-arrow", reach_arrow(), 90, 24, ' aria-hidden="true"')
    n += write("query", query(), 68, 68, ' aria-hidden="true"')
    n += write("linear-tablet", linear_tablet(), 360, 260, ' role="img"',
               "A clay tablet whose signs become legible when connected to "
               "ordinary places and records")
    body, w, h = hero()
    n += write("hero", body, w, h, ' style="max-width:860px" role="img"',
               "Your source systems resolved into one governed model, with an "
               "answer traced back through its lineage to the records it came "
               "from")
    print(f"  marks + icons + hero      "
          f"{2 + len(ICONS) + len(CATS) + len(SECTORS) + 6} files,"
          f" {n} bytes")


if __name__ == "__main__":
    main()
