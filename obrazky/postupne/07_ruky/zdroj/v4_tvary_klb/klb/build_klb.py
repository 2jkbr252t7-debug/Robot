"""R4/klb: build the exact meshes (STL + STEP) of every new / changed visible shoulder-joint part, left side, frame B.
CAD venv:  /opt/venv/cad/bin/python build_klb.py [K0,K1,...]
Writes stl/<vid>/<part>.stl, step/<vid>/<part>.step and build_klb.json (validity, volume, bbox).
The plug is rebuilt with the recipe of R1/img_v2/work/parts_v2.py (zatka: torso-following face recessed 1.0, body r 13.5,
ring r 6.5 to x 52.5, seat r 5 to 57.5, cavity, gear slot, 3 countersunk screws at r 9 / 12-4-8 o'clock, 2 pin holes),
then changed per variant (klb.py).  Never writes outside R4."""
import os, sys, json, math
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v2/work")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import numpy as np
import klb as K
import g2 as G
import t4_common as C
from build123d import (Box, Pos, Plane, Polyline, make_face, revolve, extrude, Axis, Solid, Face, Vector, export_stl, export_step)

YA, ZA = G.YA, G.ZA
P = G.PLUG
REP = {}


def lathe(pts):
    w = Polyline(*[(float(a), float(r), 0) for a, r in pts], close=True)
    return revolve(make_face(w), Axis.X, 360)


def on_sh(s):
    return Pos(0, YA, ZA) * s


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def xcyl(r, x0, x1, y=YA, z=ZA):
    return Solid.make_cylinder(r, x1 - x0, Plane(origin=(x0, y, z), z_dir=(1, 0, 0)))


def union(lst):
    s = lst[0]
    for q in lst[1:]:
        s = s + q
    return s


def save(s, vid, name):
    d = os.path.join(HERE, "stl", vid); os.makedirs(d, exist_ok=True)
    ds = os.path.join(HERE, "step", vid); os.makedirs(ds, exist_ok=True)
    ok = s.is_valid
    bb = s.bounding_box()
    export_stl(s, os.path.join(d, name + ".stl"), tolerance=0.01, angular_tolerance=0.1)
    try:
        export_step(s, os.path.join(ds, name + ".step"))
    except Exception as e:
        print("step failed", name, e)
    REP[f"{vid}/{name}"] = dict(valid=bool(ok), volume=round(s.volume, 2),
                                bbox=[round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    print(f"{vid}/{name:18s} valid {ok} vol {s.volume:9.2f} bbox x {bb.min.X:.2f}..{bb.max.X:.2f} y {bb.min.Y:.2f}..{bb.max.Y:.2f} "
          f"z {bb.min.Z:.2f}..{bb.max.Z:.2f}", flush=True)
    return s


SCREWS = [(h, *G.clock_pt(h, P["screw_r"])) for h in (12, 4, 8)]


def face_x(y, z):
    return C.x_surface(float(y), float(z)) - P["recess"]


def plug(shift=0.0, screw_x=None):
    """the v2 plug (zatka) as a solid; shift lengthens the ring / seat outboard (K3v); screw_x overrides the face x at the
    screws (countersink seat moved down into a pocket)"""
    ny, nz = 41, 41
    gy = np.linspace(YA - 16.0, YA + 16.0, ny); gz = np.linspace(ZA - 16.0, ZA + 16.0, nz)
    pts = [[Vector(face_x(y, z), float(y), float(z)) for z in gz] for y in gy]
    face = Face.make_surface_from_array_of_points(pts)
    prism = extrude(face, amount=14.0, dir=(-1, 0, 0))
    body = on_sh(lathe([(P["neck_x"][0], 0), (P["neck_x"][0], P["neck_r"]), (P["neck_x"][1], P["neck_r"]),
                        (P["neck_x"][1], P["body_r"]), (51.0, P["body_r"]), (51.0, 0)]))
    body = body & prism
    ringp = on_sh(lathe([(43.0, 0), (43.0, P["ring_r"]), (P["ring_x1"] + shift, P["ring_r"]), (P["ring_x1"] + shift, P["seat_r"]),
                         (P["seat_x1"] + shift, P["seat_r"]), (P["seat_x1"] + shift, 0)]))
    pl = body + ringp
    return pl


def plug_cuts(pl, shift=0.0, screw_x=None, access=None):
    cav = on_sh(lathe([(38.0, 0), (38.0, P["cav_r"]), (P["cav_x1"], P["cav_r"]), (44.4, 3.5), (47.05, 3.5), (47.05, 2.6),
                       (48.55, 2.6), (48.55, 3.5), (51.05, 3.5), (51.05, 3.8), (51.9, 3.8), (51.9, 2.3), (58.0 + shift, 2.3),
                       (58.0 + shift, 0)]))
    pl = pl - cav
    pl = pl - box(38.0, P["slot_x1"], YA - P["slot_hw"], YA + P["slot_hw"], ZA - 15.0, ZA - 2.0)
    heads = []
    for h, y, z in SCREWS:
        xf = face_x(y, z) if screw_x is None else min(face_x(y, z), screw_x)
        pl = pl - xcyl(1.1, 38.0, xf + 1.0, y, z)
        pl = pl - Solid.make_cone(1.1, 2.6, 1.5, Plane(origin=(xf - 0.95, y, z), z_dir=(1, 0, 0)))
        if access is not None:                                  # access bore through the cover to the countersunk head
            pl = pl - xcyl(access[0], xf - 0.3, access[1], y, z)
        hd = Solid.make_cone(1.0, 1.85, 0.85, Plane(origin=(xf - 0.92, y, z), z_dir=(1, 0, 0))) + xcyl(1.0, 34.0, xf - 0.9, y, z)
        hd = hd - box(xf - 0.6, xf + 0.1, y - 0.55, y + 0.55, z - 0.55, z + 0.55)
        heads.append(hd)
    for h in (10, 2):
        y, z = G.clock_pt(h, P["screw_r"])
        pl = pl - xcyl(1.0, 38.0, 40.5, y, z)
    return pl, union(heads)


def rev(profile):
    return on_sh(lathe([tuple(p) for p in profile]))


def merged(pf):
    """the collar / ring profile with its nest closed onto the hub (no glue gaps) for the one-piece black part"""
    keep = dict(K.NEST)
    K.NEST.update(x_step=52.8, r_step=9.6, x_back=54.8, r_rim=12.2)
    try:
        return pf()
    finally:
        K.NEST.clear(); K.NEST.update(keep)


def hub_union(ring, shift=0.0):
    """printable black part = visible collar / ring + the M2b arm hub (ARM_naboj) + stop rib (ARM_rebro), shifted for K3v"""
    sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
    import parts as MP
    from build123d import Rot
    out = ring
    for p in MP.options()["M2b"]["parts"]:
        if p.name not in ("ARM_naboj", "ARM_rebro"):
            continue
        P = np.array(p.prof, float).copy(); P[:, 0] += shift
        w = Polyline(*[(float(a), float(r), 0) for a, r in P], close=True)
        if p.az is None:
            s = revolve(make_face(w), Axis.X, 360)
        else:
            s = Rot(p.az[0], 0, 0) * revolve(make_face(w), Axis.X, p.az[1] - p.az[0])
        out = out + on_sh(s)
    n = len(out.solids())
    print("   hub union solids:", n)
    return out


def build(vid):
    if vid == "K0":
        pl, sc = plug_cuts(plug())
        save(pl, vid, "PLG_zatka_K0"); save(sc, vid, "PLG_skrutky")
    elif vid == "K1":
        p = K.K1["pocket"]
        pl = plug() - rev(K.pocket_profile())
        pl, sc = plug_cuts(pl, screw_x=p["x_floor"])
        save(pl, vid, "PLG_zatka_K1"); save(sc, vid, "PLG_skrutky")
        pf = K.VARIANTS["K1"]["parts"][2]["profile"]
        save(rev(pf()), vid, "ARM_golier_K1")
        save(hub_union(rev(merged(pf))), vid, "ARM_naboj_golier_K1")
    elif vid in ("K2", "K3", "K3v"):
        sh = K.SHIFT_K3V if vid == "K3v" else 0.0
        cv = rev(K.cover_profile(sh))
        pl = (plug(sh) - rev(K.cover_trim_profile(sh))) + cv
        pl, sc = plug_cuts(pl, sh, access=(K.COVER["screw_hole_r"], K.COVER["x_end"] + sh + 1.0))
        save(pl, vid, f"PLG_zatka_{vid}"); save(sc, vid, "PLG_skrutky")
        if vid != "K2":
            prof = [q for q in K.VARIANTS[vid]["parts"] if q["role"] == "rotating"][0]
            save(rev(prof["profile"]()), vid, prof["id"])
            save(hub_union(rev(merged(prof["profile"])), sh), vid, prof["id"].replace("ARM_", "ARM_naboj_"))


if __name__ == "__main__":
    vids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(K.VIDS)
    for v in vids:
        build(v)
    p = os.path.join(HERE, "build_klb.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(REP)
    json.dump(old, open(p, "w"), indent=1)
    print("screws (h, y, z, face x):", [(h, round(y, 2), round(z, 2), round(face_x(y, z), 3)) for h, y, z in SCREWS])
