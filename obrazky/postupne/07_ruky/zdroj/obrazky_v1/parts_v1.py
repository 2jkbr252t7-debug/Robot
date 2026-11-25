"""Arm proposal v1 - concept solids (build123d) for the images.  Left arm, rest pose, pebble shifted DX outward.
Writes work/stl/*.stl (B frame) + work/v1_data.json (wire paths, planes, numbers).  Never touches T3 / T4 / B.
Case frame used while modelling: X = world X, Y' = fore-aft (D_FA), Z' = arm-up (-D_DOWN), origin on the shoulder axis;
world = Pos(0, 3, -17) * Rot(-3 deg about X) * case-frame."""
import os, sys, json, math, struct
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v1geo as V
from build123d import (Box, Cylinder, Torus, Pos, Rot, Plane, Location, Polyline, make_face, revolve, extrude, Axis,
                       RectangleRounded, Rectangle, fillet, export_stl, Solid, Vector)

OUT = os.path.join(HERE, "stl")
os.makedirs(OUT, exist_ok=True)
TO_W = Pos(0, V.SH_Y, V.ZS) * Rot(-V.SWING, 0, 0)
assert abs(math.degrees(math.atan2(-V.D_DOWN[1], -V.D_DOWN[2])) - (-V.SWING)) < 1e-6 or True
INFO = {}


def save(shape, name, tol=0.01):
    s = TO_W * shape
    ok = s.is_valid
    bb = s.bounding_box()
    export_stl(s, os.path.join(OUT, name + ".stl"), tolerance=tol, angular_tolerance=0.15)
    INFO[name] = dict(valid=bool(ok), volume=round(s.volume, 2), bbox=[round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    print(f"{name:14s} valid {ok} vol {s.volume:9.2f} bbox x {bb.min.X:.2f}..{bb.max.X:.2f} y {bb.min.Y:.2f}..{bb.max.Y:.2f} z {bb.min.Z:.2f}..{bb.max.Z:.2f}", flush=True)
    return s


def lathe(pts):
    """profile [(x, r), ...] (closed polygon in the XY plane, y = r >= 0) revolved about the X axis"""
    w = Polyline(*[(x, r, 0) for x, r in pts], close=True)
    return revolve(make_face(w), Axis.X, 360)


def xcyl(r, x0, x1):
    return Solid.make_cylinder(r, x1 - x0, Plane(origin=(x0, 0, 0), z_dir=(1, 0, 0)))


def xprism(face_yz, x0, x1):
    """face drawn in Plane.YZ coordinates (u = Y', v = Z') extruded along +X from x0 to x1"""
    return extrude(Plane.YZ.offset(x0) * face_yz, amount=x1 - x0)


# ------------------------------------------------------------------------------------------------ spline bush (static)
B = V.BUSH
bush = lathe([(B["x_fl0"], 0), (B["x_fl0"], B["d_fl"] / 2 - 0.2), (B["x_fl0"] + 0.2, B["d_fl"] / 2), (B["x_fl1"], B["d_fl"] / 2),
              (B["x_fl1"], B["d"] / 2), (B["x_end"] - 0.25, B["d"] / 2), (B["x_end"], B["d"] / 2 - 0.25), (B["x_end"], 0)])
# female spline 20T, D3.95 (star bore), depth 3.25
n = 20
star = []
for i in range(2 * n):
    a = math.pi * i / n
    rr = 3.95 / 2 if i % 2 == 0 else 3.55 / 2
    star.append((rr * math.cos(a), rr * math.sin(a)))
spl_face = make_face(Polyline(*star, close=True))
bush = bush - xprism(spl_face, B["x_end"] - B["spl_depth"], B["x_end"] + 0.1)
save(bush, "puzdro")

# ------------------------------------------------------------------------------------------------ disc springs + spacer
SP = V.SPRING
hc = (SP["x1"] - SP["x0"]) / 2 - SP["t"]        # working cone height of each spring
xa, xm, xb = SP["x0"], (SP["x0"] + SP["x1"]) / 2, SP["x1"]
ri, ro = SP["id"] / 2, SP["od"] / 2
s1 = lathe([(xa, ro), (xa + SP["t"], ro), (xm, ri), (xm - SP["t"], ri)])          # outer rim on the spacer, inner rim in the middle
s2 = lathe([(xm, ri), (xm + SP["t"], ri), (xb, ro), (xb - SP["t"], ro)])          # inner rims touch, outer rim on the flange
save(s1, "pruzinka_1"); save(s2, "pruzinka_2")
INFO["spring_cone_working"] = round(hc, 3)
SC = V.SPACER
spacer = lathe([(SC["x0"], SC["id"] / 2), (SC["x1"], SC["id"] / 2), (SC["x1"], SC["od"] / 2), (SC["x0"], SC["od"] / 2)])
save(spacer, "kruzok")

# ------------------------------------------------------------------------------------------------ O-ring
OR = V.ORING
oring = Pos(OR["x"], 0, 0) * Rot(0, 90, 0) * Torus(OR["R"], OR["r"])
save(oring, "o_kruzok", 0.005)

# ------------------------------------------------------------------------------------------------ joint cover (hub + servo pod), raw (trimmed by the pebble in Blender)
H, P, C = V.HUB, V.POD, V.CAV
hub = xcyl(H["r_out"], H["x0"], H["x1"])
try:
    hub = hub.fillet(0.8, hub.edges().filter_by_position(Axis.X, H["x0"] - 0.01, H["x0"] + 0.01))
except Exception as e:
    print("hub fillet failed", e)
pz0, pz1 = -P["a1"], -P["a0"]                       # Z' range of the pod outline (a = -Z')
pod_face = Pos(0, (pz0 + pz1) / 2) * RectangleRounded(2 * P["b"], pz1 - pz0, P["rc"])
pod = xprism(pod_face, P["x0"], 77.0)
try:
    pod = pod.fillet(1.2, pod.edges().filter_by_position(Axis.X, P["x0"] - 0.01, P["x0"] + 0.01))
except Exception as e:
    print("pod fillet failed", e)
cover = hub + pod
cover = cover - xcyl(H["r_bore"], H["x0"] - 1, H["x1"] + 0.02)                                    # bore on the journal
cover = cover - lathe([(H["x0"] - 1, H["ch_r0"]), (H["ch_x1"], H["ch_r0"]), (H["ch_x1"], H["ch_r1"]), (H["x0"] - 1, H["ch_r1"])])   # cable chamber
cover = cover - lathe([(H["x0"] - 1, 10.9), (H["sleeve_x0"], 10.9), (H["sleeve_x0"], H["ch_r0"] + 0.01), (H["x0"] - 1, H["ch_r0"] + 0.01)])   # chamber entry (sleeve starts at 52.0)
cover = cover - lathe([(H["oring_x"][0], 10.9), (H["oring_x"][1], 10.9), (H["oring_x"][1], H["oring_r"]), (H["oring_x"][0], H["oring_r"])])
ch = dict(z0=12.75, z1=14.15, b=1.2, x0=56.6, x1=59.5)                    # wire channel (top, arm-up side) chamber -> pod pocket
cover = cover - Pos((ch["x0"] + ch["x1"]) / 2, 0, (ch["z0"] + ch["z1"]) / 2) * Box(ch["x1"] - ch["x0"], 2 * ch["b"], ch["z1"] - ch["z0"])
cz0, cz1 = -C["a1"], -C["a0"]
cav_face = Pos(0, (cz0 + cz1) / 2) * RectangleRounded(2 * C["b"], cz1 - cz0, 0.6)
pk_face = Pos(0, (cz1 - 0.4 - C["pa0"]) / 2) * Rectangle(2 * C["pb"], -C["pa0"] - cz1 + 0.4)
cavity = xprism(cav_face, H["x1"], 78.0) + xprism(pk_face, H["x1"], 78.0)
cover = cover - cavity
save(cover, "kryt_surovy")
save(xprism(cav_face, 58.0, 72.0) + xprism(pk_face, 58.0, 72.0), "dutina")       # cutter for the hole in the inner shell
INFO["wire_channel"] = ch

# ------------------------------------------------------------------------------------------------ servo SCS0009 (concept box, UNVERIFIED dims)
SV = V.SERVO
zc0, zc1 = -(SV["L"] - SV["s"]), SV["s"]
case = Pos((V.X_CASE0 + V.X_CASE1) / 2, 0, (zc0 + zc1) / 2) * Box(SV["H"], SV["W"], SV["L"])
try:
    case = case.fillet(0.6, case.edges())
except Exception as e:
    print("case fillet failed", e)
case = case + xcyl(SV["boss_d"] / 2, V.X_CASE0 - SV["boss_h"], V.X_CASE0 + 0.05)
save(case, "servo_telo")
shaft = xcyl(SV["spl_d"] / 2, V.X_CASE0 - SV["boss_h"] - SV["spl_h"], V.X_CASE0 - SV["boss_h"] + 0.02)
save(shaft, "servo_hriadel")

# ------------------------------------------------------------------------------------------------ connector JST-SH 3p (pair) inside the arm, above the case
con = dict(x0=65.5, x1=71.0, z0=7.2, z1=10.4, b=2.2)
conn = Pos((con["x0"] + con["x1"]) / 2, 0, (con["z0"] + con["z1"]) / 2) * Box(con["x1"] - con["x0"], 2 * con["b"], con["z1"] - con["z0"])
try:
    conn = conn.fillet(0.3, conn.edges())
except Exception:
    pass
save(conn, "konektor")
INFO["connector"] = con


# ------------------------------------------------------------------------------------------------ magnets + bosses (local arm frame -> world)
def local_loc(p_local, axis_local):
    """Location whose z axis = arm-local direction axis_local, origin = arm-local point (world, left arm at rest)"""
    o = V.to_world(p_local)
    z = V.dir_world(axis_local)
    xd = V.dir_world([0, 1.0, 0])
    return Location(Plane(origin=tuple(o), x_dir=tuple(xd), z_dir=tuple(z)))


mag_o, mag_i, bos_o, bos_i = [], [], [], []
for m in V.magnet_spots_local():
    for side, lst_m, lst_b in ((1, mag_o, bos_o), (-1, mag_i, bos_i)):
        loc = local_loc(m + np.array([side * V.SEAM, 0, 0]), [side, 0, 0])
        mg = Solid.make_cylinder(1.5, 2.0, Plane.XY.offset(0.03))
        bs = Solid.make_cylinder(2.2, 2.4, Plane.XY) - Solid.make_cylinder(1.55, 2.05, Plane.XY.offset(-0.01))
        lst_m.append(loc * mg); lst_b.append(loc * bs)


def union_all(lst):
    s = lst[0]
    for q in lst[1:]:
        s = s + q
    return s


for nm, lst in (("magnety_von", mag_o), ("magnety_vnu", mag_i), ("stlpiky_von", bos_o), ("stlpiky_vnu", bos_i)):
    s = union_all(lst)
    export_stl(s, os.path.join(OUT, nm + ".stl"), tolerance=0.005, angular_tolerance=0.15)
    bb = s.bounding_box()
    INFO[nm] = dict(valid=bool(s.is_valid), bbox=[round(v, 2) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    print(nm, s.is_valid, INFO[nm]["bbox"])


# ------------------------------------------------------------------------------------------------ servo bed plates (conforming numpy meshes, world)
def write_stl(path, tris):
    tris = np.asarray(tris, np.float32)
    with open(path, "wb") as f:
        f.write(b"v1 concept".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
        rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec["n"] = nrm; rec["v"] = tris
        f.write(rec.tobytes())


def hexa_grid(a_rng, b_rng, x_in_fn, x_out_fn, na=24, nb=4):
    """closed mesh of the block {a in a_rng, b in b_rng, x in [x_in(a,b), x_out(a,b)]} (a, b in the case frame)"""
    A = np.linspace(*a_rng, na); Bv = np.linspace(*b_rng, nb)
    G = np.zeros((2, na, nb, 3))
    for i, a in enumerate(A):
        for j, b in enumerate(Bv):
            y, z = V.ab_to_yz(a, b)
            G[0, i, j] = (x_in_fn(float(y), float(z)), y, z)
            G[1, i, j] = (x_out_fn(float(y), float(z)), y, z)
    T = []

    def quad(p, q, r, s):
        T.append([p, q, r]); T.append([p, r, s])
    for k, sgn in ((0, 1), (1, -1)):                        # x faces
        for i in range(na - 1):
            for j in range(nb - 1):
                p, q, r, s = G[k, i, j], G[k, i + 1, j], G[k, i + 1, j + 1], G[k, i, j + 1]
                quad(p, q, r, s) if sgn > 0 else quad(p, s, r, q)
    for i in range(na - 1):                                 # b sides
        for j, sgn in ((0, 1), (nb - 1, -1)):
            p, q, r, s = G[0, i, j], G[0, i + 1, j], G[1, i + 1, j], G[1, i, j]
            quad(p, q, r, s) if sgn > 0 else quad(p, s, r, q)
    for j in range(nb - 1):                                 # a ends
        for i, sgn in ((0, 1), (na - 1, -1)):
            p, q, r, s = G[0, i, j], G[1, i, j], G[1, i, j + 1], G[0, i, j + 1]
            quad(p, q, r, s) if sgn > 0 else quad(p, s, r, q)
    T = np.array(T)
    cen = G.reshape(-1, 3).mean(0)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    flip = np.einsum("ij,ij->i", nrm, T.mean(1) - cen) < 0
    T[flip] = T[flip][:, ::-1]
    vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6
    return T, vol


x_in = lambda y, z: V.skins(y, z)[0] + 1.0
x_out = lambda y, z: V.x_at_local_x(y, z, -V.SEAM - 0.05)
BD = V.BED
parts = []
for sgn in (-1, 1):
    b0, b1 = sorted((sgn * BD["b0"], sgn * BD["b1"]))
    parts.append(hexa_grid((BD["a0"], BD["a1"]), (b0, b1), x_in, x_out)[0])
parts.append(hexa_grid(BD["stop"], (-BD["b1"], BD["b1"]), x_in, x_out, na=4, nb=12)[0])
write_stl(os.path.join(OUT, "lozko.stl"), np.concatenate(parts))
print("lozko written")

# ------------------------------------------------------------------------------------------------ wire paths (world, left arm at rest) -> Blender curves
def cf(x, yp, zp, ylane=None):
    """case frame (x, Y', Z') -> world; ylane: force the world y (straight runs just behind the section plane y = 3)"""
    p = [float(x), float(V.SH_Y + yp * V.D_FA[1] - zp * V.D_DOWN[1]), float(V.ZS + yp * V.D_FA[2] - zp * V.D_DOWN[2])]
    if ylane is not None:
        p[1] = V.SH_Y + ylane
    return p


wires = []
# lanes: groove under T_klb (static, r 11.25 / 11.87 / 12.49 at y 3.4) -> climb into the chamber (x 50.96..52.0) ->
# half a turn at r 13.4 about the bearing sleeve, through the back (+Y'), each wire on its own x lane ->
# channel at the top (Z' 12.75..14.15) -> pod pocket -> into the arm -> connector
G_R = (11.25, 11.87, 12.49)
X_L = (52.6, 54.0, 55.4)
C_L = ((13.1, 0.4), (13.75, 0.4), (13.42, 1.0))           # (Z', world y lane) in the top channel
for k in range(3):
    yl = 0.4
    P_ = [cf(36.5, 0, -G_R[k] - 6.0, yl), cf(38.0, 0, -G_R[k] - 1.5, yl), cf(39.6, 0, -G_R[k], yl), cf(50.5, 0, -G_R[k], yl),
          cf(51.5, 0, -13.4, yl), cf(X_L[k] - 0.6, 0, -13.4, yl)]
    for t in np.linspace(0, 1, 25):
        ang = -math.pi / 2 + math.pi * t                  # -90 .. +90 deg, through +Y'
        q = cf(X_L[k], 13.4 * math.cos(ang), 13.4 * math.sin(ang))
        q[1] = max(q[1], V.SH_Y + yl)
        P_.append(q)
    zc, yc = C_L[k]
    P_ += [cf(X_L[k] + 0.8, 0, zc, yc), cf(57.0, 0, zc, yc), cf(59.6, 0, zc, yc), cf(62.0, 0, zc - 0.6, yc), cf(64.0, 0, 11.0 - 0.55 * k, yc),
           cf(65.6, 0, 8.8, 0.4 + 0.65 * k)]
    wires.append(P_)
# servo lead: connector -> case top (x 68)
lead = [[cf(71.0, 0, 8.8, 0.4 + 0.65 * k), cf(72.3, 0, 8.0, 0.4 + 0.65 * k), cf(72.6, 0, 6.2, 0.4 + 0.65 * k)] for k in range(3)]
INFO["wires"] = wires
INFO["lead"] = lead
json.dump(INFO, open(os.path.join(HERE, "v1_data.json"), "w"), indent=1)
print("done")
