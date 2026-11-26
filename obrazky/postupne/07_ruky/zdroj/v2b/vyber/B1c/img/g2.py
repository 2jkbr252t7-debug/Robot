"""NOVA mini - arm drive v2 (judge-final K3): shared numbers + pure-numpy helpers (importable from the CAD venv and
from Blender's python).  Frame B: mm, Z up, front -Y, robot LEFT = +X.  Values for the LEFT side; right = mirror x -> -x."""
import sys, math, struct
import numpy as np

sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v1/work")
import v1geo as V          # noqa: E402  (arm pebble placement, swing, magnets)

DX = -1.0                  # arm 1.0 mm closer to the torso than T3/T4
YA, ZA = 3.0, -17.0        # shoulder axis || X
XV = 39.0                  # vertical drive axis (x 39, y 3)
O = np.array([XV, YA, ZA]) # bevel apex

# servo SCS0009 (ears cut off)
SERVO = dict(x=(32.95, 45.05), y=(-14.3, 8.9), z=(-66.5, -45.0), boss_r=3.5, boss_z=(-45.0, -44.0), spl_r=1.975, spl_top=-40.25)
# bevel pair
BEV = dict(m=0.5, z1=16, z2=24, b=2.4)
# shafts / bearings
SHAFT_V = dict(r=1.5, z=(-41.0, -20.82))
B1 = dict(ri=1.5, ro=3.0, z=(-26.35, -23.85))
SHAFT_A = dict(r=2.0, r2=1.5, x0=41.39, xstep=57.7, x1=60.5)
A1 = dict(ri=2.0, ro=3.5, x=(44.55, 47.05))
A2 = dict(ri=2.0, ro=3.5, x=(48.55, 51.05))
B6700 = dict(ri=5.0, ro=7.5, x=(53.5, 57.5))
COUPLER = dict(r=4.0, z=(-44.0, -37.0))
# plug
PLUG = dict(neck_r=11.0, neck_x=(38.6, 40.6), body_r=13.5, recess=1.0, cav_r=6.8, cav_x1=44.0, ring_r=6.5, ring_x1=52.5,
            seat_r=5.0, seat_x1=57.5, slot_hw=5.0, slot_x1=44.0, screw_r=9.0)
# clutch stack (x)
CLUTCH = dict(w1=(57.7, 58.2), fl=(58.2, 59.4), w2=(59.4, 59.7), spr=(59.7, 60.25), w3=(60.25, 60.75), head=(60.75, 62.05))
# column
BOSS = dict(r=12.8, x=(34.4, 38.4), stop=(11.6, 12.8, 38.4, 39.1), slot=(-24.55, -15.5))
TONGUE = dict(ri=3.0, ro=4.4, z=(-26.85, -24.05))
PAN_ENV2 = [(-47.20, -41.90, 17.50), (-41.90, -40.90, 26.50), (-40.90, -17.00, 33.40), (-17.00, -11.50, 32.20), (-11.50, 4.00, 26.50)]
BUCK = dict(c=(28.75, -1.5), size=(17.8, 17.8, 10.3), ztop=-70.95)

# clock positions on the left plug / boss seen from +X (viewer right = +Y): angle t -> (dy, dz) = (sin t, cos t)
CLOCK = {h: (math.sin(math.radians(30 * h)), math.cos(math.radians(30 * h))) for h in range(12)}


def clock_pt(h, r):
    s, c = CLOCK[h % 12]
    return YA + r * s, ZA + r * c


def bevel_params():
    m, z1, z2, b = BEV["m"], BEV["z1"], BEV["z2"], BEV["b"]
    d1 = math.atan2(z1, z2); d2 = math.pi / 2 - d1
    Re = 0.5 * m * math.hypot(z1, z2)
    return dict(d1=d1, d2=d2, Re=Re, k=(Re - b) / Re, ha=m, hf=1.25 * m)


def bevel_mesh(z, delta, Re, k, m, bore_r, web=0.0, phase=0.0, nflank=4, nland=3):
    """closed triangle mesh of a straight bevel gear in its local frame: axis +a from the apex (a = distance along the axis),
    radial r, angle phi.  Returns (verts (N,3) as (a, r*cos phi, r*sin phi), faces)."""
    ha, hf = m, 1.25 * m
    tan_a = math.tan(math.radians(20.0))

    def back(h):          # (r, a) on the heel back cone at height h above the pitch line
        return Re * math.sin(delta) + h * math.cos(delta), Re * math.cos(delta) - h * math.sin(delta)

    def half_ang(h):
        t = math.pi * m / 2 - 2 * h * tan_a
        r, _ = back(h)
        return 0.5 * t / r
    prof = []             # (phi, h)
    hs_up = np.linspace(-hf, ha, nflank)
    for i in range(z):
        c = phase + 2 * math.pi * i / z
        for h in hs_up:                                      # rising flank
            prof.append((c - half_ang(h), h))
        for t in np.linspace(-1, 1, nland)[1:-1]:            # tip land
            prof.append((c + t * half_ang(ha), ha))
        for h in hs_up[::-1]:                                # falling flank
            prof.append((c + half_ang(h), h))
        c2 = phase + 2 * math.pi * (i + 1) / z
        a0, a1 = c + half_ang(-hf), c2 - half_ang(-hf)
        for t in np.linspace(0, 1, nland + 2)[1:-1]:          # root land
            prof.append((a0 + t * (a1 - a0), -hf))
    N = len(prof)
    H = np.array([(back(h)[1], back(h)[0], p) for p, h in prof])          # (a, r, phi) heel
    T = H.copy(); T[:, 0] *= k; T[:, 1] *= k                              # toe = heel scaled to the apex
    r_root, a_root = back(-hf - 0.03)
    phis = H[:, 2]
    Hr = np.c_[np.full(N, a_root), np.full(N, r_root), phis]
    Tr = np.c_[np.full(N, k * a_root), np.full(N, k * r_root), phis]
    a_back = a_root + web
    rings = [T, H, Hr]
    if web > 0:
        rings.append(np.c_[np.full(N, a_back), np.full(N, r_root), phis])
    rings.append(np.c_[np.full(N, a_back), np.full(N, bore_r), phis])
    rings.append(np.c_[np.full(N, k * a_root), np.full(N, bore_r), phis])
    rings.append(Tr)
    P = np.concatenate(rings)
    K = len(rings)
    F = []
    for j in range(K):
        jn = (j + 1) % K
        for i in range(N):
            i1 = (i + 1) % N
            F.append((j * N + i, jn * N + i, jn * N + i1, j * N + i1))
    verts = np.c_[P[:, 0], P[:, 1] * np.cos(P[:, 2]), P[:, 1] * np.sin(P[:, 2])]
    return verts, F


def tris_from(verts, faces):
    T = []
    for f in faces:
        if len(f) == 3:
            T.append([verts[f[0]], verts[f[1]], verts[f[2]]])
        else:
            T.append([verts[f[0]], verts[f[1]], verts[f[2]]]); T.append([verts[f[0]], verts[f[2]], verts[f[3]]])
    T = np.array(T)
    ar = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
    return T[ar > 1e-10]


def write_stl(path, tris, name=b"nova v2 concept"):
    tris = np.asarray(tris, np.float32)
    with open(path, "wb") as f:
        f.write(name.ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
        rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec["n"] = nrm; rec["v"] = tris
        f.write(rec.tobytes())


def pinion_world():
    p = bevel_params()
    v, F = bevel_mesh(BEV["z1"], p["d1"], p["Re"], p["k"], BEV["m"], SHAFT_V["r"], web=0.0, phase=0.0)
    a, u, w = v[:, 0], v[:, 1], v[:, 2]
    W = np.c_[XV + u, YA + w, ZA - a]          # axis -Z; phi = 0 toward +X (mesh line at (43, 3, -23))
    return W, F


def gear_world():
    p = bevel_params()
    pitch = 2 * math.pi / BEV["z2"]
    v, F = bevel_mesh(BEV["z2"], p["d2"], p["Re"], p["k"], BEV["m"], SHAFT_A["r"], web=0.5, phase=-math.pi / 2 + pitch / 2)
    a, u, w = v[:, 0], v[:, 1], v[:, 2]
    W = np.c_[XV + a, YA + u, ZA + w]          # axis +X; phi = -90 deg -> -Z (mesh line), space centred there
    return W, F


def swing_matrix(deg):
    return V.swing_matrix(deg)


def sweep_x(r, y=YA):
    return math.sqrt(max(r * r - y * y, 0.0))


if __name__ == "__main__":
    p = bevel_params()
    print({k: round(v, 4) for k, v in p.items()})
    W, F = pinion_world(); print("pinion bbox", W.min(0).round(3), W.max(0).round(3))
    W, F = gear_world(); print("gear bbox", W.min(0).round(3), W.max(0).round(3))
    for h in (12, 4, 8, 10, 2):
        print("clock", h, np.round(clock_pt(h, 9.0), 2))
