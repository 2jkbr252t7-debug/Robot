"""
Shared CAD helpers for NOVA (build123d).  Run with /opt/venv/cad/bin/python.

Every subassembly module (head.py, neck.py, torso.py, arms.py, base.py, internals.py) exposes

    def build() -> list[PartRec]

where each PartRec holds a build123d Solid/Compound positioned in FINAL ASSEMBLY coordinates
(see nova/spec.py for the coordinate system) plus metadata used by the renderer.
"""
from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field

from build123d import (
    Axis, BuildLine, BuildPart, BuildSketch, Box, Compound, Cylinder, Face, Location, Mode, Plane,
    Polyline, Pos, Rot, Sketch, Solid, Spline, Vector, Wire, export_gltf, export_step, export_stl, fillet,
    loft, make_face, offset, Edge, RectangleRounded, Circle, Ellipse, extrude, revolve, Sphere, scale,
    mirror, split, Keep, SlotOverall, Rectangle,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from nova import spec  # noqa: E402

OUT = os.path.join(ROOT, "build")          # generated (git-ignored) CAD exports


@dataclass
class PartRec:
    id: str                    # part number, e.g. "H01" or "A01-R"
    name: str                  # Slovak name, e.g. "Hlavný obal hlavy"
    shape: object              # build123d Shape in assembly coordinates
    mat: str                   # key of spec.MATERIALS
    sub: str                   # subassembly: base | torso | neck | head | arm_R | arm_L | internal
    joint: str = ""            # kinematic group that moves with a joint: J1 (all above base), J2 (pan), J3 (tilt), J4, J5
    explode: tuple = (0.0, 0.0, 0.0)   # suggested explode offset (mm) for exploded views
    internal: bool = False     # True = hidden inside (electronics, brackets) – shown only in sections/x-ray
    note: str = ""             # short functional note (Slovak)


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def superellipse_pts(a: float, b: float, n: float, count: int = 96):
    """Closed list of points of |x/a|^n + |y/b|^n = 1 (first point not repeated)."""
    pts = []
    for i in range(count):
        t = 2 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(c) ** (2.0 / n), c)
        y = b * math.copysign(abs(s) ** (2.0 / n), s)
        pts.append((x, y))
    return pts


def superellipse_wire(a: float, b: float, n: float, z: float = 0.0, count: int = 64) -> Wire:
    """Closed periodic B-spline wire of a superellipse at height z (in an XY plane)."""
    pts = [Vector(x, y, z) for x, y in superellipse_pts(a, b, n, count)]
    edge = Edge.make_spline(pts, periodic=True)
    return Wire([edge])


def rounded_rect_wire(w: float, h: float, r: float, plane: Plane = Plane.XY) -> Wire:
    """Rounded rectangle wire centred on the plane origin."""
    with BuildSketch(plane) as sk:
        RectangleRounded(w, h, r)
    return sk.sketch.faces()[0].outer_wire()


def loft_sections(wires, ruled: bool = False) -> Solid:
    return Solid.make_loft(wires, ruled=ruled)


def half_ellipsoid_stack(half_w_x: float, half_w_y: float, z_mid: float, z_top: float, z_bot: float, n: int = 24):
    """Egg made from two half-ellipsoids that share the widest section at z_mid (C1 continuous).
    Returns a Solid built as a loft of ellipse sections (robust in OCC)."""
    wires = []
    zs = []
    for i in range(n + 1):  # bottom half
        u = i / n
        zs.append(z_bot + (z_mid - z_bot) * (1 - math.cos(u * math.pi / 2)))
    for i in range(1, n + 1):  # top half
        u = i / n
        zs.append(z_mid + (z_top - z_mid) * math.sin(u * math.pi / 2))
    secs = []
    for z in zs:
        if z <= z_mid:
            t = (z_mid - z) / (z_mid - z_bot)
        else:
            t = (z - z_mid) / (z_top - z_mid)
        k = math.sqrt(max(0.0, 1 - min(1.0, t) ** 2))
        secs.append((z, k))
    # replace the zero-size end sections by tiny ones (loft needs real wires)
    out = []
    for z, k in secs:
        k = max(k, 0.02)
        e = Edge.make_ellipse(half_w_x * k, half_w_y * k, Plane.XY.offset(z)) if half_w_x >= half_w_y else \
            Edge.make_ellipse(half_w_y * k, half_w_x * k, Plane.XY.offset(z).rotated((0, 0, 90)))
        out.append(Wire([e]))
    return Solid.make_loft(out)


def bbox_dict(shape):
    bb = shape.bounding_box()
    return dict(min=[round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)],
                max=[round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)],
                size=[round(bb.size.X, 3), round(bb.size.Y, 3), round(bb.size.Z, 3)])


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

def export_parts(parts: list[PartRec], sub_name: str, step: bool = True, out_dir: str | None = None) -> list[dict]:
    """Export every part as GLB (for Blender) + STEP + STL and write a manifest JSON.
    Returns the manifest records."""
    out_dir = out_dir or OUT
    for d in ("step", "stl", "manifest"):
        os.makedirs(os.path.join(out_dir, d), exist_ok=True)
    recs = []
    for p in parts:
        if p.mat not in spec.MATERIALS:
            raise ValueError(f"{p.id}: unknown material {p.mat}")
        shp = p.shape
        if shp is None:
            raise ValueError(f"{p.id}: shape is None")
        fid = p.id
        stl = os.path.join(out_dir, "stl", f"{fid}.stl")
        export_stl(shp, stl, tolerance=0.02, angular_tolerance=0.1)
        if step:
            export_step(shp, os.path.join(out_dir, "step", f"{fid}.step"))
        try:
            vol = float(shp.volume)
        except Exception:
            vol = 0.0
        recs.append(dict(id=p.id, name=p.name, mat=p.mat, sub=p.sub, joint=p.joint, explode=list(p.explode),
                         internal=p.internal, note=p.note, bbox=bbox_dict(shp), volume_mm3=round(vol, 1),
                         stl=os.path.relpath(stl, out_dir)))
    with open(os.path.join(out_dir, "manifest", f"{sub_name}.json"), "w") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    return recs


def run_module(build_fn, sub_name: str):
    """Standard __main__ entry for subassembly modules: build + export + print summary."""
    import time
    t = time.time()
    parts = build_fn()
    recs = export_parts(parts, sub_name)
    for r in recs:
        print(f"  {r['id']:8s} {r['mat']:11s} size={r['bbox']['size']} min={r['bbox']['min']} vol={r['volume_mm3']}")
    print(f"[{sub_name}] {len(recs)} parts exported in {time.time() - t:.1f}s -> {OUT}")
