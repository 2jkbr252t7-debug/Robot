"""T1 layout library – component envelopes, poses, interference / sweep checks, mass + CoG + tipping, STL export.
Run with /opt/venv/cad/bin/python (build123d).  Import:  sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1"); import t1lib as T

WORLD FRAME: mm, Z up, floor z = 0, origin = centre of the base on the floor; robot FRONT = -Y, robot RIGHT = -X.
J1 (torso yaw) and PAN (neck yaw) both turn about the world Z axis through x = y = 0.
Groups (kinematic chain):
  B  base, static (wheels, casters, battery, ...)
  T  torso – turns with J1 about Z
  P  pan stage – on T, turns with pan about Z (collar disc, well, lift servo + crank, ...)
  L  lift – on P, translates +Z by `lift` (0 = rest .. 20 = extended): neck halves, tilt servo, ...
  H  head – on L, tilts about the hinge axis (X axis at y = 0, z = AXZ(lift)); tilt + = nod DOWN (front goes down)
  AR / AL  right (-X) / left (+X) arm – on T, swing about the shoulder axis (X axis at y = SH_Y, z = SH_Z);
     arm angle 0 = hanging down, +90 = pointing forward (-Y), 180 = straight up, negative = backwards.
Pose dict: {"j1": deg, "pan": deg, "lift": mm, "tilt": deg, "armR": deg, "armL": deg}  (missing keys = 0)

LAYOUT JSON (one file per concept):
{ "name": "...", "Z_TT": <torso top world z = top face of the collar disc>, "SH": [SH_Y, SH_Z],
  "contacts": [[x, y], ...]   ground contact points of wheels + casters (base frame, static),
  "comps": [ {"name": "T_shell", "kind": ..., "group": "T", "mass": g | "mat": "resin"|"pla"|"petg"|"steel"|"brass"|"pcb",
              "color": key (see COLORS), "label": "slovenský popis", "at": [x, y, z] centre, "rot": [rx, ry, rz] deg (opt.),
              "cuts": [comp dicts subtracted, same keys, positions in world], "adds": [...], "ignore": ["other names"]} ],
  "allow": [["a", "b"], ...]  pairs that may touch / interpenetrate on purpose (shaft in hub, bearing in seat ...) }
kinds:  box   size [sx, sy, sz], optional "r" (round the 4 vertical edges), "rf" (round all edges)
        cyl   r, h, axis "x"|"y"|"z"        tube  r, ri, h, axis
        sblock  superellipse prism: a, b (half sizes x, y), n (exponent), h, optional "rf" (round top+bottom loops)
        sshell  hollow sblock: + "wall"; optional "open_top": true / "open_bottom": true (no top / bottom wall)
        sphere  r
The finished neck + head (variant B, rev. E2) is added automatically by neck_head(Z_TT) as simplified envelopes
(groups P/T/L/H) – do not model it again.  B-frame -> world: z_world = z_B + (Z_TT - 4).
"""
from __future__ import annotations
import json, math, os, sys, itertools
from build123d import (Box, Cylinder, Sphere, Pos, Rot, Location, Axis, Face, Solid, Compound, extrude, fillet,
                       export_stl)
sys.path.insert(0, "/home/user/Robot")
from nova.cad.common import superellipse_wire                                     # noqa: E402

DENS = {"resin": 1.15e-3, "pla": 1.24e-3, "petg": 1.27e-3, "steel": 7.85e-3, "brass": 8.5e-3, "pcb": 1.9e-3,
        "alu": 2.7e-3, "rubber": 1.2e-3, "pom": 1.41e-3}
COLORS = {"white": (0.92, 0.92, 0.90), "black": (0.06, 0.06, 0.07), "grey": (0.45, 0.46, 0.48),
          "servo": (0.16, 0.30, 0.62), "servo_bus": (0.10, 0.10, 0.12), "battery": (0.20, 0.55, 0.32),
          "pcb": (0.10, 0.42, 0.22), "elec": (0.12, 0.35, 0.65), "metal": (0.70, 0.70, 0.72), "cable": (0.95, 0.45, 0.10),
          "glow": (0.25, 0.85, 0.95), "rubber": (0.10, 0.10, 0.10), "motor": (0.75, 0.62, 0.30), "red": (0.85, 0.15, 0.12),
          "yellow": (0.95, 0.80, 0.15), "glass": (0.02, 0.02, 0.03)}
GROUPS = ("B", "T", "P", "L", "H", "AR", "AL")

# ---------------------------------------------------------------------------------------------------- variant B data
B_TOP = 4.0               # torso top (collar disc top) in the B frame
B_AXZ_REST = -3.5         # hinge axis z in the B frame at rest (16.5 extended)
B_HEAD_MASS = 165.0       # g: resin shell 72 + bezel 20 + display board ~55 + ears/LED 10 + lugs 4.5 + magnets/screws 3.5
B_NECK_MASS = 45.0        # g: neck halves 28.5 + MG90S 13.4 + pin/bearing/screws/foam/wires 3


def neck_head(Z_TT: float) -> list[dict]:
    """simplified envelopes of the finished neck + head (variant B rev. E2), REST pose, in world coordinates"""
    dz = Z_TT - B_TOP
    z = lambda zb: zb + dz
    return [
        {"name": "B_hlava", "kind": "box", "size": [110, 66, 79], "rf": 14, "at": [0, 0, z(46.5)], "group": "H",
         "mass": B_HEAD_MASS - 12, "color": "white", "label": "hlava (hotová, verzia B)", "cog": [0, -8, z(46.0)]},
        {"name": "B_ram_tvar", "kind": "box", "size": [108, 2, 77], "rf": 0.9, "at": [0, -32, z(46.5)], "group": "H",
         "mass": 0, "color": "glass", "label": "displej"},
        {"name": "B_usi", "kind": "cyl", "r": 12.5, "h": 117.6, "axis": "x", "at": [0, -1, z(46.5)], "group": "H",
         "mass": 12, "color": "black", "label": "uši"},
        {"name": "B_uska", "kind": "box", "size": [45, 20, 29], "at": [0, 0, z(1.0)], "group": "H", "mass": 0,
         "color": "black", "label": "ušká pántu", "ignore": ["B_krk"]},
        {"name": "B_krk", "kind": "box", "size": [45, 20, 43], "r": 0.5, "at": [0, 0, z(-15.0)], "group": "L",
         "mass": B_NECK_MASS, "color": "black", "label": "krk 45×20 (hotový)"},
        {"name": "B_kabel_krk", "kind": "box", "size": [3.0, 7.5, 6.0], "at": [13.9, -3.0, z(-39.5)], "group": "L",
         "mass": 0, "color": "cable", "label": "vodiče hlavy (4) a serva náklonu (3) – výstup zo spodku krku"},
        {"name": "B_golier_kotuc", "kind": "cyl", "r": 26.5, "h": 6, "axis": "z", "at": [0, 0, z(1.0)], "group": "P",
         "mass": 8.8, "color": "black", "label": "golier – otočný kotúč (pan)",
         "cuts": [{"kind": "box", "size": [45.5, 20.5, 8], "at": [0, 0, z(1.0)]}]},
        {"name": "B_golier_prstenec", "kind": "tube", "r": 28.25, "ri": 26.75, "h": 6, "axis": "z", "at": [0, 0, z(1.0)],
         "group": "T", "mass": 1.8, "color": "black", "label": "golier – pevný prstenec (v trupe)"},
    ]


def b_frame_dz(Z_TT: float) -> float:
    return Z_TT - B_TOP


# ---------------------------------------------------------------------------------------------------- geometry
def _axis_rot(axis):
    return {"x": Rot(0, 90, 0), "y": Rot(90, 0, 0), "z": Rot(0, 0, 0)}[axis]


def _sblock(a, b, n, h, rf=0.0):
    w = superellipse_wire(a, b, n, -h / 2, count=96)
    s = extrude(Face(w), amount=h)
    if rf > 0:
        for r in (rf, rf * 0.75, rf * 0.5, rf * 0.3):
            try:
                loops = [e for e in s.edges() if abs(abs(e.center().Z) - h / 2) < 1e-3]
                t = fillet(loops, r)
                if t.is_valid:
                    return t
            except Exception:
                continue
    return s


def raw_shape(c: dict):
    k = c["kind"]
    if k == "box":
        s = Box(*c["size"])
        if c.get("rf"):
            r = min(c["rf"], min(c["size"]) / 2 - 0.01)
            try:
                s = fillet(s.edges(), r)
            except Exception:
                pass
        elif c.get("r"):
            r = min(c["r"], min(c["size"][:2]) / 2 - 0.01)
            try:
                s = fillet(s.edges().filter_by(Axis.Z), r)
            except Exception:
                pass
    elif k == "cyl":
        s = _axis_rot(c.get("axis", "z")) * Cylinder(c["r"], c["h"])
    elif k == "tube":
        s = _axis_rot(c.get("axis", "z")) * (Cylinder(c["r"], c["h"]) - Cylinder(c["ri"], c["h"] + 0.2))
    elif k == "sphere":
        s = Sphere(c["r"])
    elif k in ("sblock", "sshell"):
        s = _sblock(c["a"], c["b"], c.get("n", 2.6), c["h"], c.get("rf", 0))
        if k == "sshell":
            t = c["wall"]
            hi = c["h"] - (0 if c.get("open_top") else t) - (0 if c.get("open_bottom") else t)
            zc = ((t if not c.get("open_bottom") else -0.1) - (t if not c.get("open_top") else -0.1)) / 2
            inner = Pos(0, 0, zc) * _sblock(c["a"] - t, c["b"] - t, c.get("n", 2.6), hi + (0.2 if c.get("open_top") or c.get("open_bottom") else 0),
                                            max(0.0, c.get("rf", 0) - t))
            s = s - inner
    else:
        raise ValueError(f"unknown kind {k}")
    if c.get("rot"):
        rx, ry, rz = c["rot"]
        s = Rot(rx, ry, rz) * s
    s = Pos(*c.get("at", (0, 0, 0))) * s
    for a in c.get("adds", []):
        s = s + raw_shape(a)
    for cu in c.get("cuts", []):
        s = s - raw_shape(cu)
    return s


class Layout:
    def __init__(self, data: dict | str):
        if isinstance(data, str):
            data = json.load(open(data))
        self.d = data
        self.Z_TT = float(data["Z_TT"])
        self.SH = data.get("SH", [0.0, self.Z_TT - 20.0])
        self.comps = list(data["comps"]) + ([] if data.get("no_neck_head") else neck_head(self.Z_TT))
        names = [c["name"] for c in self.comps]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            raise ValueError(f"duplicate names {dup}")
        self.allow = {frozenset(p) for p in data.get("allow", [])}
        for c in self.comps:
            for o in c.get("ignore", []):
                self.allow.add(frozenset((c["name"], o)))
        self._raw = {}

    def raw(self, name):
        if name not in self._raw:
            c = self.comp(name)
            self._raw[name] = raw_shape(c)
        return self._raw[name]

    def comp(self, name):
        return next(c for c in self.comps if c["name"] == name)

    # -------------------------------------------------------------- pose transforms
    def axz(self, lift=0.0):
        return B_AXZ_REST + b_frame_dz(self.Z_TT) + lift

    def loc(self, group: str, pose: dict) -> Location:
        j1 = Rot(0, 0, pose.get("j1", 0.0))
        pan = Rot(0, 0, pose.get("pan", 0.0))
        lift = Pos(0, 0, pose.get("lift", 0.0))
        if group == "B":
            return Location()
        if group == "T":
            return j1
        if group == "P":
            return j1 * pan
        if group == "L":
            return j1 * pan * lift
        if group == "H":
            ax = self.axz(0.0)
            tilt = Pos(0, 0, ax) * Rot(pose.get("tilt", 0.0), 0, 0) * Pos(0, 0, -ax)
            return j1 * pan * lift * tilt
        if group in ("AR", "AL"):
            th = pose.get("armR" if group == "AR" else "armL", 0.0)
            ys, zs = self.SH
            return j1 * Pos(0, ys, zs) * Rot(-th, 0, 0) * Pos(0, -ys, -zs)
        raise ValueError(group)

    def shape(self, name, pose):
        return self.raw(name).moved(self.loc(self.comp(name)["group"], pose))

    # -------------------------------------------------------------- checks
    def clashes(self, pose: dict, tol=0.5, only_moving=False, names=None):
        """pairs with intersection volume > tol mm3 (skips allowed pairs). only_moving: only pairs of different groups"""
        sel = [c for c in self.comps if names is None or c["name"] in names]
        S = {c["name"]: self.shape(c["name"], pose) for c in sel}
        BB = {n: s.bounding_box() for n, s in S.items()}
        out = []
        for a, b in itertools.combinations(sel, 2):
            na, nb = a["name"], b["name"]
            if frozenset((na, nb)) in self.allow or (na.startswith("B_") and nb.startswith("B_")):
                continue                          # B_* = finished neck/head, verified in rev. E2 (envelopes overlap)
            if only_moving and a["group"] == b["group"]:
                continue
            A, B = BB[na], BB[nb]
            if A.min.X > B.max.X or B.min.X > A.max.X or A.min.Y > B.max.Y or B.min.Y > A.max.Y or \
               A.min.Z > B.max.Z or B.min.Z > A.max.Z:
                continue
            try:
                v = (S[na] & S[nb]).volume
            except Exception as ex:
                v = -1
                print("boolean failed", na, nb, repr(ex)[:60])
            if v > tol or v < 0:
                out.append((na, nb, round(v, 2)))
        return out

    def gaps(self, pose: dict, a_names, b_names):
        """minimum distance between two sets of components (mm) in a pose"""
        best = (1e9, None, None)
        for a in a_names:
            sa = self.shape(a, pose)
            for b in b_names:
                d = sa.distance_to(self.shape(b, pose))
                if d < best[0]:
                    best = (d, a, b)
        return best

    def sweep(self, poses: list[dict], tol=0.5):
        """clashes between parts of DIFFERENT groups over a list of poses -> {pair: [pose index, ...]}"""
        res = {}
        for i, p in enumerate(poses):
            for a, b, v in self.clashes(p, tol, only_moving=True):
                res.setdefault(f"{a} x {b}", []).append((i, v))
        return res

    # -------------------------------------------------------------- mass
    def mass_of(self, c):
        if "mass" in c:
            return float(c["mass"])
        if "mat" in c:
            return self.raw(c["name"]).volume * DENS[c["mat"]]
        return 0.0

    def cog(self, pose: dict):
        M, S = 0.0, [0.0, 0.0, 0.0]
        rows = []
        for c in self.comps:
            m = self.mass_of(c)
            if m <= 0:
                continue
            if c.get("cog"):
                p = self.loc(c["group"], pose) * Location(tuple(c["cog"]))
                cc = p.position
            else:
                sh = self.shape(c["name"], pose)
                try:
                    cc = sh.center(center_of=__import__("build123d").CenterOf.MASS)
                except Exception:
                    cc = sh.bounding_box().center()
            M += m
            cc = (cc.X, cc.Y, cc.Z)
            for i in range(3):
                S[i] += m * cc[i]
            rows.append((c["name"], round(m, 1)))
        return M, [s / M for s in S], rows

    def tipping(self, pose: dict, accel_g=0.0):
        """support polygon = convex hull of contacts; returns min margin (mm) and min tip angle (deg) incl. an
        optional horizontal acceleration (fraction of g) applied in the worst direction"""
        M, c, _ = self.cog(pose)
        pts = hull([tuple(p) for p in self.d["contacts"]])
        res = []
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
            ex, ey = x2 - x1, y2 - y1
            L = math.hypot(ex, ey)
            d = ((c[0] - x1) * ey - (c[1] - y1) * ex) / L        # >0 inside for a CW hull -> sign fixed below
            res.append(d)
        sgn = 1 if sum(res) > 0 else -1
        res = [sgn * r for r in res]
        m = min(res)
        ang = math.degrees(math.atan2(m, c[2]))
        return {"mass_g": round(M, 1), "cog": [round(v, 1) for v in c], "margin_mm": round(m, 1),
                "tip_deg": round(ang, 1), "margin_at_accel_mm": round(m - c[2] * accel_g, 1)}

    # -------------------------------------------------------------- export for renders
    def export(self, pose: dict, out_dir: str, tol=0.05, ang=0.3):
        os.makedirs(out_dir, exist_ok=True)
        meta = []
        for c in self.comps:
            fn = os.path.join(out_dir, c["name"] + ".stl")
            export_stl(self.shape(c["name"], pose), fn, tolerance=tol, angular_tolerance=ang)
            meta.append({"name": c["name"], "group": c["group"], "color": c.get("color", "grey"),
                         "label": c.get("label", c["name"]), "stl": fn})
        json.dump({"pose": pose, "Z_TT": self.Z_TT, "dz_B": b_frame_dz(self.Z_TT), "parts": meta,
                   "loc": {g: _loc_matrix(self.loc(g, pose)) for g in GROUPS}},
                  open(os.path.join(out_dir, "parts.json"), "w"), indent=1)
        return out_dir


def _loc_matrix(loc: Location):
    t = loc.wrapped.Transformation()
    return [[t.Value(r, c) for c in range(1, 5)] for r in range(1, 4)] + [[0, 0, 0, 1]]


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) <= 2:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


STD_POSES = [  # sweep set every concept must pass (add more of your own)
    {}, {"lift": 20}, {"lift": 20, "tilt": 40}, {"lift": 20, "tilt": -40}, {"lift": 12.5, "tilt": 25},
    {"pan": 85}, {"pan": -85}, {"pan": 85, "lift": 20, "tilt": 40}, {"pan": -85, "lift": 20, "tilt": -40},
    {"armR": 90, "armL": 90}, {"armR": 180, "armL": 180}, {"armR": -45, "armL": -45}, {"armR": 135, "armL": 45},
    {"armR": 180, "armL": 180, "pan": 85, "lift": 20, "tilt": 40}, {"armR": 180, "armL": 180, "pan": -85},
    {"j1": 150, "armR": 90, "armL": 90}, {"j1": -150, "armR": -45, "armL": 180},
    {"j1": 90, "pan": 85, "lift": 20, "tilt": 40, "armR": 90, "armL": 90},
]

if __name__ == "__main__":
    L = Layout(sys.argv[1])
    print("static clashes:", L.clashes({}))
    print("sweep:", json.dumps(L.sweep(STD_POSES), indent=1))
    for p in ({}, {"j1": 90, "pan": 85, "lift": 20, "tilt": 40, "armR": 90, "armL": 90}):
        print("tipping", p, L.tipping(p, accel_g=0.15))
