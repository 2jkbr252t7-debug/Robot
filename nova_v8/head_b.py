"""
NOVA mini (v8) - HEAD variant B "kapsula s vizorom" (HB01..HB05).  CONCEPT model.
Run from the repo root:  /opt/venv/cad/bin/python -m nova_v8.head_b
Exports STL + manifest "head_b" into build_v8/ (never into build/, which holds the finished v7.3).

A more modern sibling of the R01 head: a very round white capsule with ONE curved black visor that
follows a vertical cylinder (plan R95) across the front and wraps around the cheeks onto both sides.
No protruding bezel - the visor sits flush in the shell with a 0.6 mm shadow gap.  Shared numbers come
from nova_v8/concept.py (HEAD, HEAD_B, NECK, DISPLAY); the "local concept constants" block holds only
construction values of this sketch (wall, gaps, fillets, positions that concept.py leaves open).
Concept level: clean outer surfaces, real walls and seams, no bosses / snaps / screws.

Body construction: front silhouette prism 110 x 76 R34 (along Y, back loop R26)  INTERSECT  plan prism
(front arc R95 + R20 plan corners, along Z), then the whole front loop is rounded R9 -> one smooth
capsule.  The visor region is the band z 127..181 of the skin in front of y = -13 (side view: rounded
rear end R18), i.e. its top / bottom edges are straight in the front view and follow the R95 arc in
the top view.

Parts (sub "head_b", joint "J3" = head tilt about X through NECK.tilt_axis y=0 z=126)
  HB01     Predny obal hlavy    white        front shell (y < 19.7): wall 2.0, flush visor opening + 2.4 mm
                                             visor ledge, ear grooves, underside pocket for the Ø30 tilt barrel,
                                             1.2 mm lip behind the parting seam
  HB02     Zadny obal hlavy     white        rear cap (y > 20.3), 0.6 mm vertical parting seam behind the ears
  HB03     Vizor                glass        smoked PC / glass visor 1.6 mm, band 54 high, wraps onto the sides
  HB03C    Okienko kamery       black_gloss  RENDER-ONLY camera dot in the upper visor band (x 0, z 176)
  HB03E    Obsah displeja - oci eye          RENDER-ONLY two warm pill eyes 11 x 18 on the visor curvature
  HB05-R/L LED kruzok ucha      cyan_led     flush light-guide rings OD24 / ID18 on the sides (y +4, z 154)

Display check: the flat 3.5" module 86 x 56 x 6 (corner R3 assumed) at y -25.2 .. -19.2 is verified
against HB01 / HB03 (clearances printed by __main__).
"""
from __future__ import annotations

import math
import os
import sys
import time

from build123d import (Axis, Box, BuildSketch, Circle, Compound, Cylinder, GeomType, Locations, Mode, Plane, Pos,
                       Rectangle, RectangleRounded, Rot, ShapeList, SlotOverall, Sphere, Vector, chamfer, extrude,
                       fillet, offset)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nova.cad.common import PartRec, export_parts  # noqa: E402
from nova_v8 import concept as C  # noqa: E402

OUT_DIR = os.path.join(ROOT, "build_v8")
SUB = "head_b"

HB = C.HEAD_B
W, HH, D = HB["w"], HB["h"], HB["d"]                       # 110 x 76, depth 70
R_FV, R_BACK = HB["r_front_view"], HB["r_back"]            # 34, 26
VIS, EAR, EYE = HB["visor"], HB["ear"], HB["eyes"]
Z0 = C.HEAD["z0"]                                          # 116 head bottom
ZC = Z0 + HH / 2                                           # 154
Z1 = Z0 + HH                                               # 192
TILT_Y, TILT_Z = C.NECK["tilt_axis"]["y"], C.NECK["tilt_axis"]["z"]   # 0, 126
BARREL_R, BARREL_LEN = C.NECK["barrel_d"] / 2, C.NECK["barrel_len"]   # 15, 30
DISP_W, DISP_H, DISP_T = C.DISPLAY["outline"]              # 86 x 56 x 6
assert abs(ZC - VIS["zc"]) < 1e-9 and abs(ZC - EAR["z"]) < 1e-9

# ---- local concept constants (construction values, not shared dimensions) ------------------
Y_FRONT = -38.0            # visor apex at x = 0 (head reaches 38 in front of / 32 behind the tilt axis:
                           # the flat display must clear the barrel pocket AND the curved visor)
Y_BACK = Y_FRONT + D       # +32
R_PLAN = VIS["r_plan"]     # 95  plan radius of the visor cylinder
Y_AXIS = Y_FRONT + R_PLAN  # +57 plan-arc centre
X_PS = W / 2 + 5.0         # plan-prism side lines lie outside the head (no coincident faces)
R_PF = 20.0                # plan corner arc R95 -> side
R_FRONT = 9.0              # 3D round of the whole front loop (must stay < 11 = white cap above the visor)
WALL = 2.0
VIS_T = 1.6                # visor thickness
GAP = 0.6                  # shadow gap visor <-> shell, and parting seam width
VZ0, VZ1 = ZC - VIS["h"] / 2, ZC + VIS["h"] / 2            # 127 .. 181
Y_VIS_REAR = -13.0         # rear end of the visor on the sides (ear ring starts at y -8)
R_VIS_END = 18.0           # side view: rounded rear corners of the visor band
LEDGE_D0, LEDGE_D1, LEDGE_W = VIS_T + 0.1, 3.0, 2.4        # visor ledge behind the shadow gap (depth from skin)
Y_SEAM = 20.0              # vertical parting plane front shell / rear cap (behind the ear rings)
LIP_D0, LIP_D1, LIP_OUT = WALL + 0.05, WALL + 1.2, 3.0     # backing lip under the parting seam
RING_OD, RING_ID = EAR["ring_od"], EAR["ring_id"]          # 24 / 18
RING_DEPTH, RING_GAP = 1.4, 0.15
EAR_Y, EAR_Z = EAR["y"], EAR["z"]                          # +4, 154
P_RIN = BARREL_R + 1.0     # barrel pocket: R16 about the tilt axis
P_XIN = BARREL_LEN / 2 + 1.2                                # |x| <= 16.2
P_WALL = 1.6
CAM_Z, CAM_D = 176.0, 2.8  # camera dot (sits in the wedge between curved visor and flat display)
DISP_CR = 3.0              # assumed corner radius of the display module outline
Y_DISP_FRONT = -25.2       # display front face (flat, behind the visor)


# ===========================================================================================
# helpers
# ===========================================================================================

def plane_y(y, cx=0.0, cz=ZC):
    return Plane(origin=(cx, y, cz), x_dir=(1, 0, 0), z_dir=(0, 1, 0))


def rr_prism_y(w, h, r, y0, y1, cx=0.0, cz=ZC):
    with BuildSketch(plane_y(y0, cx, cz)) as sk:
        RectangleRounded(w, h, r)
    return extrude(sk.sketch, y1 - y0)


def rr_prism_x(y0, y1, z0, z1, r, x0=-80.0, x1=80.0):
    """Rounded rectangle drawn in the side view (Y, Z) extruded along X."""
    pl = Plane(origin=(x0, (y0 + y1) / 2, (z0 + z1) / 2), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    with BuildSketch(pl) as sk:
        RectangleRounded(y1 - y0, z1 - z0, r)
    return extrude(sk.sketch, x1 - x0)


def cyl_x(r, x0, x1, y, z):
    lo, hi = min(x0, x1), max(x0, x1)
    return Pos((lo + hi) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, hi - lo)


def cyl_y(r, y0, y1, x, z):
    lo, hi = min(y0, y1), max(y0, y1)
    return Pos(x, (lo + hi) / 2, z) * Rot(90, 0, 0) * Cylinder(r, hi - lo)


def slab_y(y0, y1):
    return Pos(0, (y0 + y1) / 2, ZC) * Box(200, y1 - y0, 200)


def check(name, s, vmin=None):
    if not s.is_valid:
        raise RuntimeError(f"{name}: invalid solid")
    if vmin is not None and s.volume < vmin:
        raise RuntimeError(f"{name}: volume {s.volume:.0f} < {vmin}")
    return s


def retry(fn, label, tries=4):
    """OCC booleans run in parallel mode - retry rare non-deterministic failures."""
    err = None
    for _ in range(tries):
        try:
            out = fn()
            if out is not None and out.is_valid and out.volume > 0:
                return out
        except Exception as ex:  # pragma: no cover
            err = ex
    raise RuntimeError(f"{label}: boolean failed {tries}x ({err})")


def single(shape, label):
    sols = shape.solids()
    if len(sols) != 1:
        vols = sorted((round(s.volume, 1) for s in sols), reverse=True)
        raise RuntimeError(f"{label}: {len(sols)} solids {vols}")
    return sols[0]


def edges_where(shape, pred):
    out = []
    for e in shape.edges():
        pts = [e.position_at(t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        if all(pred(p) for p in pts):
            out.append(e)
    return ShapeList(out)


def try_fillet(shape, edges, r, label):
    if not edges:
        print(f"  ({label}: no edges)")
        return shape
    try:
        out = fillet(edges, r)
        if out.is_valid and abs(out.volume - shape.volume) < 0.05 * shape.volume:
            return out
        print(f"  ({label}: fillet result rejected)")
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: fillet R{r} skipped: {ex})")
    return shape


def try_chamfer(shape, edges, d, label):
    if not edges:
        print(f"  ({label}: no edges)")
        return shape
    try:
        out = chamfer(edges, d)
        if out.is_valid and abs(out.volume - shape.volume) < 0.05 * shape.volume:
            return out
        print(f"  ({label}: chamfer result rejected)")
    except Exception as ex:  # pragma: no cover
        print(f"  ({label}: chamfer {d} skipped: {ex})")
    return shape


# ===========================================================================================
# capsule body
# ===========================================================================================

def capsule_body():
    """Outer skin as a solid: silhouette prism (R34, back loop R26) & plan prism (R95 + R20), front loop R9."""
    sil = rr_prism_y(W, HH, R_FV, Y_FRONT - 6, Y_BACK)
    sil = fillet(sil.edges().group_by(Axis.Y)[-1], R_BACK)
    with BuildSketch(Plane.XY.offset(Z0 - 10)) as sk:
        with Locations((0, Y_AXIS)):
            Circle(R_PLAN)
        with Locations((0, (Y_FRONT - 5 + Y_BACK + 10) / 2)):
            Rectangle(2 * X_PS, Y_BACK + 10 - (Y_FRONT - 5), mode=Mode.INTERSECT)
        fillet(sk.vertices().filter_by(lambda v: v.Y < 0), R_PF)
    plan = extrude(sk.sketch, HH + 20)
    body = check("body", sil & plan)
    front_loop = edges_where(body, lambda p: p.Y < Y_BACK - R_BACK - 1)
    front_loop = ShapeList([e for e in front_loop if e.geom_type != GeomType.LINE])
    body = fillet(front_loop, R_FRONT)
    return check("body", body)


class Skin:
    """Body + cached inward offsets (depth d below the skin)."""

    def __init__(self):
        self.body = capsule_body()
        self._off = {}

    def inner(self, d):
        if d not in self._off:
            o = offset(self.body, amount=-d)
            if not o.is_valid or o.volume >= self.body.volume:
                raise RuntimeError(f"offset -{d} failed")
            self._off[d] = o
        return self._off[d]

    def band(self, d0, d1):
        """Layer between depth d0 and d1 below the skin (d0 = 0 -> the skin itself)."""
        outer = self.body if d0 == 0 else self.inner(d0)
        return retry(lambda: outer - self.inner(d1), f"band {d0}..{d1}")


# ===========================================================================================
# parts
# ===========================================================================================

def visor_cutter(grow=0.0):
    """Side-view rounded rectangle (front end far outside the head) extruded along X."""
    return rr_prism_x(Y_FRONT - 30 - grow, Y_VIS_REAR + grow, VZ0 - grow, VZ1 + grow, R_VIS_END + grow)


def ear_annulus(ro, ri):
    return cyl_x(ro, -70, 70, EAR_Y, EAR_Z) - cyl_x(ri, -71, 71, EAR_Y, EAR_Z)


def build_shells(sk: Skin):
    body = sk.body
    shell = sk.band(0, WALL)

    # ---- flush visor: the visor is the skin layer inside the cutter, the shell gets a 0.6 larger opening
    visor = retry(lambda: sk.band(0, VIS_T) & visor_cutter(), "visor")
    visor = single(visor, "HB03")
    shell = retry(lambda: shell - visor_cutter(GAP), "visor opening")
    ledge = retry(lambda: (sk.band(LEDGE_D0, LEDGE_D1) & visor_cutter(GAP + 0.6)) - visor_cutter(-LEDGE_W),
                  "visor ledge")

    # ---- parting seam (vertical plane behind the ears) ----
    h02 = retry(lambda: shell & slab_y(Y_SEAM + GAP / 2, Y_BACK + 5), "HB02")
    h01 = retry(lambda: shell & slab_y(Y_FRONT - 5, Y_SEAM - GAP / 2), "HB01 split")
    lip = retry(lambda: (sk.band(WALL - 0.5, LIP_D1) & slab_y(Y_SEAM - 3, Y_SEAM - GAP / 2))
                + (sk.band(LIP_D0, LIP_D1) & slab_y(Y_SEAM - 1.5, Y_SEAM + LIP_OUT)), "seam lip")
    h01 = retry(lambda: h01 + ledge, "ledge")
    h01 = retry(lambda: h01 + lip, "lip")

    # ---- underside pocket for the Ø30 tilt barrel (R16 about the tilt axis, open downwards) ----
    p_in = cyl_x(P_RIN, -P_XIN, P_XIN, TILT_Y, TILT_Z) + \
        Pos(0, TILT_Y, (Z0 - 6 + TILT_Z) / 2) * Box(2 * P_XIN, 2 * P_RIN, TILT_Z - Z0 + 6)
    xo, ro = P_XIN + P_WALL, P_RIN + P_WALL
    p_out = cyl_x(ro, -xo, xo, TILT_Y, TILT_Z) + \
        Pos(0, TILT_Y, (Z0 - 6 + TILT_Z) / 2) * Box(2 * xo, 2 * ro, TILT_Z - Z0 + 6)
    h01 = retry(lambda: h01 + (p_out & body), "pocket walls")
    h01 = retry(lambda: h01 - p_in, "pocket")
    e_pk = edges_where(h01, lambda p: abs(p.Z - Z0) < 0.02 and max(abs(p.X) - P_XIN, abs(p.Y - TILT_Y) - P_RIN) > -0.02
                       and abs(p.X) < P_XIN + 0.02 and abs(p.Y - TILT_Y) < P_RIN + 0.02)
    h01 = try_fillet(h01, e_pk, 1.0, "pocket rim")

    # ---- flush ear rings: 1.5 deep groove, ring 1.4 deep, 0.15 radial gaps ----
    groove = retry(lambda: sk.band(0, RING_DEPTH + 0.1) & ear_annulus(RING_OD / 2 + RING_GAP, RING_ID / 2 - RING_GAP),
                   "ear groove")
    h01 = retry(lambda: h01 - groove, "ear grooves")
    rings = retry(lambda: sk.band(0, RING_DEPTH) & ear_annulus(RING_OD / 2, RING_ID / 2), "rings")
    ring_l = single(rings & slab_x(0, 80), "HB05-L")
    ring_r = single(rings & slab_x(-80, 0), "HB05-R")

    h01 = single(h01, "HB01")
    h02 = single(h02, "HB02")
    return (check("HB01", h01, 20000), check("HB02", h02, 3000), check("HB03", visor, 3000),
            check("HB05-R", ring_r, 50), check("HB05-L", ring_l, 50))


def slab_x(x0, x1):
    return Pos((x0 + x1) / 2, 0, ZC) * Box(x1 - x0, 200, 200)


def camera_dot():
    """Render-only lens: very low spherical cap on the visor (x 0 -> visor is the R95 cylinder, y = Y_FRONT)."""
    r, sag = CAM_D / 2, 0.2
    rs = (r * r + sag * sag) / (2 * sag)
    sph = Pos(0, Y_FRONT - sag + rs, CAM_Z) * Sphere(rs)
    lens = sph & cyl_y(r, Y_FRONT - 1.0, Y_FRONT + 0.05, 0.0, CAM_Z)
    return check("HB03C", lens)


def eyes():
    """Render-only pills 11 x 18 that follow the R95 visor cylinder, 0.02..0.17 mm in front of it."""
    shell = Pos(0, Y_AXIS, EYE["z"]) * Cylinder(R_PLAN + 0.17, 40) - Pos(0, Y_AXIS, EYE["z"]) * Cylinder(R_PLAN + 0.02, 41)
    out = None
    for sx in (-1, 1):
        with BuildSketch(plane_y(Y_FRONT - 6, sx * EYE["x"], EYE["z"])) as s:
            SlotOverall(EYE["h"], EYE["w"], rotation=90)
        e = extrude(s.sketch, 12) & shell
        out = e if out is None else out + e
    return check("HB03E", out)


def display_dummy():
    """Flat 3.5" module (outline incl. PCB + ESP32) - used only for the fit check, not exported."""
    return rr_prism_y(DISP_W, DISP_H, DISP_CR, Y_DISP_FRONT, Y_DISP_FRONT + DISP_T)


# ===========================================================================================

def build():
    sk = Skin()
    h01, h02, h03, ring_r, ring_l = build_shells(sk)
    up, fy, ex = 80.0, 30.0, 26.0
    J = "J3"
    return [
        PartRec("HB01", "Predný obal hlavy", h01, "white", SUB, J, (0, 0, up),
                note="koncept: biela kapsula 110×76×70, rohy spredu R34, čelo R95, stena 2.0, "
                     "lícujúci otvor vizora, vybranie zdola pre valec náklonu Ø30"),
        PartRec("HB02", "Zadný obal hlavy", h02, "white", SUB, J, (0, fy, up),
                note="zadná kapsula za deliacou škárou 0.6 (rovina y = +20, za ušami), zadné zaoblenie R26"),
        PartRec("HB03", "Vizor", h03, "glass", SUB, J, (0, -fy, up),
                note="čierny dymový vizor 1.6 mm, valec R95, pás 54 mm, zahnutý 14 mm do bokov, tieňová škára 0.6"),
        PartRec("HB03C", "Okienko kamery", camera_dot(), "black_gloss", SUB, J, (0, -fy - 8, up),
                note="len objekt pre render: kamera v klinovom priestore medzi vizorom a plochým displejom"),
        PartRec("HB03E", "Obsah displeja – oči", eyes(), "eye", SUB, J, (0, -fy - 8, up),
                note="len objekt pre render: dve teplé pilulky 11×18 na zakrivení vizora"),
        PartRec("HB05-R", "LED krúžok ucha pravý", ring_r, "cyan_led", SUB, J, (-ex, 0, up),
                note="lícujúci svetlovod Ø24/Ø18 v boku hlavy, tyrkysová LED"),
        PartRec("HB05-L", "LED krúžok ucha ľavý", ring_l, "cyan_led", SUB, J, (ex, 0, up),
                note="lícujúci svetlovod Ø24/Ø18 v boku hlavy, tyrkysová LED"),
    ]


def overlaps(parts, tol=1.0):
    bad = []
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            ba, bb = a.shape.bounding_box(), b.shape.bounding_box()
            if (ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y
                    or ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z):
                continue
            try:
                common = a.shape & b.shape
                v = 0.0 if common is None else common.volume
            except Exception:
                v = -1
            if v > tol or v < 0:
                bad.append((a.id, b.id, round(v, 2)))
    return bad


if __name__ == "__main__":
    t = time.time()
    parts = build()
    recs = export_parts(parts, SUB, step=False, out_dir=OUT_DIR)
    for p, r in zip(parts, recs):
        print(f"  {r['id']:8s} {r['mat']:11s} valid={p.shape.is_valid} size={r['bbox']['size']} "
              f"min={r['bbox']['min']} vol={r['volume_mm3']}")
    print("  overlaps:", overlaps(parts) or "none")
    disp = display_dummy()
    for p in parts:
        if p.id in ("HB01", "HB03", "HB03C"):
            print(f"  display clearance to {p.id}: {disp.distance_to(p.shape):.2f} mm")
    print(f"[{SUB}] {len(recs)} parts exported in {time.time() - t:.1f}s -> {OUT_DIR}")
