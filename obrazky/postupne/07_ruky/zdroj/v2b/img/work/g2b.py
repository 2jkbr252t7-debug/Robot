"""NOVA mini - arm drive B1+ (fixer revision R2c/oprava): shared numbers + numpy helpers for the images (CAD venv and Blender).
Frame B: mm, Z up, front -Y, robot LEFT = +X.  LEFT side values; right = mirror x -> -x.
Every number from /tmp/claude-0/gapwf/fin/R2c/oprava/final_B1plus_fix.json (fixer)."""
import sys, os, math, struct
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v1/work")
import v1geo as V          # noqa: E402  (arm pebble placement, swing, magnets)
import gears_b1 as GB      # noqa: E402  (rack-generated tooth profile, copy of B1 gears.py)

DX = -1.0
YA, ZA = 3.0, -17.0
XV = 39.0
O = np.array([XV, YA, ZA])

# servo SCS0009 (earless).  v2 image model: case 21.5 high (drawing says 25.25 -> open item).  Top face -45.0 = highest point
# of the case (fixer); the output spline is drawn short enough for the printed spline cup (top <= -41.6).
SERVO = dict(x=(32.95, 45.05), y=(-14.3, 8.9), z=(-66.5, -45.0), spl_r=1.975, spl_root=1.8, spl_top=-41.75, thr_r=0.8)
# printed coupler cup, path B (20T internal spline)
CUP = dict(r=4.5, z0=-44.7, spl_top=-41.6, floor=(-41.6, -40.6), hole_r=1.2, rec_r=2.05, rec=(-40.6, -38.4),
           hex_af=5.0, hex=(-38.4, -35.5), spl_od=3.95, spl_root=3.45)
CSCREW = dict(head_r=1.9, head=(-40.6, -38.6), r=1.0, tip=-45.6)            # DIN 912 M2x5
SHAFT_V = dict(hex_af=4.98, hex=(-38.4, -35.5), r=1.5, j=(-35.5, -24.5), key_r=1.25, key=(-24.5, -20.47), flat=0.85)
B1 = dict(ri=1.5, ro=3.0, z=(-26.35, -23.85))                               # MR63ZZ
PSHIM = dict(ri=1.55, ro=1.9, z=(-23.85, -23.43))                           # 0.42 nominal
GEAR_N = dict(m=2 * 4.0 / 12, z1=12, z2=18, alpha=25.0, ha1=0.9, ha2=0.8, hf=1.15, rho=0.38, b=2.8)
GSHIM = dict(ri=2.05, ro=2.9, x=(44.238, 44.54))                            # 0.30 nominal
A1 = dict(ri=2.0, ro=3.5, x=(44.54, 47.04))
SLEEVE = dict(ri=2.5, ro=3.5, x=(47.04, 52.6))
A2 = dict(ri=2.0, ro=3.5, x=(52.6, 55.1))
M4 = dict(r=2.0, x=(40.0, 60.0), head_r=3.5, head=(60.0, 64.0), hex_af=3.0, hex_d=2.0)
CSHIM = dict(ri=2.1, ro=4.4, x=(59.5, 59.95), open=4.2)
B6800 = dict(ri=5.0, ro=9.5, x=(55.3, 60.3), ring=1.1)
WASHER = dict(ri=5.25, ro=10.0, x=(61.2, 63.2))
DRIVE = dict(boss=(3.5, 4.5), boss_x=(60.0, 63.2), r=11.0, x=(63.2, 66.25), pocket_r=2.55, mag_R=7.7, skin=0.25, n=8, key_af=3.0)
MAG = dict(r=2.5, t=2.0, az=(90.0, 180.0, 270.0, 0.0))                     # 4 magnets in opposite pockets (az 0 = +Y, 90 = +Z)
HUB = dict(ri=7.5, x0=47.0, bore_r=9.5, bore_x=(55.3, 60.4), fl=(60.4, 61.2), fl_ri=5.0, cav_r=11.5, ro=12.7, x1=67.55,
           rib=dict(x=(53.0, 55.0), r=(5.5, 7.5), az=(135.0, 225.0)))
LIP = dict(ri=10.4, ro=11.5, x=(66.75, 67.55))
PLUG = dict(neck_r=11.0, neck_x=(38.6, 40.6), body_r=13.5, recess=1.0, cav_r=6.9, cav_x1=44.54, ring_r=6.5, ring_x1=52.5,
            seat_r=5.0, seat_x1=59.5, bore7_x1=55.1, slot_hw=5.1, slot_x1=44.0, screw_r=9.0,
            lug=dict(x=(52.5, 54.8), r=(5.0, 7.0), az=(276.0, 359.5)), peg_r=1.2, peg_x=(36.6, 38.7))
SCREWS = {12: ("M2×8", 8.0, 0.0), 4: ("M2×10", 10.0, 0.0), 8: ("M2×10", 10.0, 1.3)}   # DIN 965, extra countersink depth
BOSS = dict(r=12.8, x=(34.4, 38.4), stop=(11.6, 12.8, 38.4, 39.1), slot=(-24.55, -15.5))
TONGUE = dict(ri=3.0, ro=4.4, z=(-26.85, -24.05))
PAN_ENV2 = [(-47.20, -41.90, 17.50), (-41.90, -40.90, 26.50), (-40.90, -17.00, 33.40), (-17.00, -11.50, 32.20), (-11.50, 4.00, 26.50)]
BUCK = dict(c=(28.75, -1.5), size=(17.8, 17.8, 10.3), ztop=-70.95)
FILL = "/tmp/claude-0/gapwf/fin/R2c/oprava/colfill_fix_L.npz"

CLOCK = {h: (math.sin(math.radians(30 * h)), math.cos(math.radians(30 * h))) for h in range(12)}


def clock_pt(h, r):
    s, c = CLOCK[h % 12]
    return YA + r * s, ZA + r * c


def az_pt(az_deg, r):
    """azimuth about the shoulder axis: 0 = +Y, 90 = +Z (fixer convention) -> (y, z)"""
    a = math.radians(az_deg)
    return YA + r * math.cos(a), ZA + r * math.sin(a)


# ------------------------------------------------------------------------------------------------ printed bevel pair
def bevel_params():
    g = GEAR_N
    d1 = math.atan2(g["z1"], g["z2"]); d2 = math.pi / 2 - d1
    Re = 0.5 * g["m"] * math.hypot(g["z1"], g["z2"])
    return dict(d1=d1, d2=d2, Re=Re, k=(Re - g["b"]) / Re)


def bevel_mesh(z, delta, ha, Re, k, bore_r, web=0.0, phase=0.0, nfl=9, nland=3):
    """closed triangle mesh of a straight bevel gear (local frame: a along the axis from the apex, r radial, phi).
    Heel outline = rack-generated tooth of the Tredgold virtual spur gear (z_v = z / cos delta), phi = theta_v / cos delta."""
    g = GEAR_N
    m = g["m"]
    zv = z / math.cos(delta)
    tp = GB.tooth_profile(zv, m, g["alpha"], ha, g["hf"], g["rho"], 0.0)
    r_v, psi_v = tp["r"], tp["psi"]
    ok = psi_v > 1e-4
    r_v, psi_v = r_v[ok], psi_v[ok]
    Rv = tp["rp"]
    rr = np.linspace(r_v.min(), r_v.max(), nfl)
    ps = np.interp(rr, r_v, psi_v) / math.cos(delta)
    hs = rr - Rv                                     # height above the pitch line along the back cone

    def back(h):
        return Re * math.sin(delta) + h * math.cos(delta), Re * math.cos(delta) - h * math.sin(delta)
    prof = []
    for i in range(z):
        c = phase + 2 * math.pi * i / z
        for h, p in zip(hs, ps):                      # rising flank
            prof.append((c - p, h))
        for t in np.linspace(-1, 1, nland)[1:-1]:     # tip land
            prof.append((c + t * ps[-1], hs[-1]))
        for h, p in zip(hs[::-1], ps[::-1]):          # falling flank
            prof.append((c + p, h))
        c2 = phase + 2 * math.pi * (i + 1) / z
        a0, a1 = c + ps[0], c2 - ps[0]
        for t in np.linspace(0, 1, nland + 2)[1:-1]:   # root land
            prof.append((a0 + t * (a1 - a0), hs[0]))
    N = len(prof)
    H = np.array([(back(h)[1], back(h)[0], p) for p, h in prof])
    T = H.copy(); T[:, 0] *= k; T[:, 1] *= k
    r_root, a_root = back(hs[0])
    phis = H[:, 2]
    a_back = a_root + web
    rings = [T, H, np.c_[np.full(N, a_root), np.full(N, r_root), phis]]
    if web > 0:
        rings.append(np.c_[np.full(N, a_back), np.full(N, r_root), phis])
    rings.append(np.c_[np.full(N, a_back), np.full(N, bore_r), phis])
    rings.append(np.c_[np.full(N, k * a_root), np.full(N, bore_r), phis])
    rings.append(np.c_[np.full(N, k * a_root), np.full(N, k * r_root), phis])
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
        T.append([verts[f[0]], verts[f[1]], verts[f[2]]]); T.append([verts[f[0]], verts[f[2]], verts[f[3]]])
    T = np.array(T)
    ar = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
    return T[ar > 1e-10]


def write_stl(path, tris, name=b"nova B1+ concept"):
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
    v, F = bevel_mesh(GEAR_N["z1"], p["d1"], GEAR_N["ha1"], p["Re"], p["k"], SHAFT_V["key_r"], web=0.0, phase=0.0)
    a, u, w = v[:, 0], v[:, 1], v[:, 2]
    return np.c_[XV + u, YA + w, ZA - a], F       # axis -Z; phi 0 toward +X (mesh line)


def gear_world():
    p = bevel_params()
    pitch = 2 * math.pi / GEAR_N["z2"]
    v, F = bevel_mesh(GEAR_N["z2"], p["d2"], GEAR_N["ha2"], p["Re"], p["k"], M4["r"], web=0.6, phase=-math.pi / 2 + pitch / 2)
    a, u, w = v[:, 0], v[:, 1], v[:, 2]
    return np.c_[XV + a, YA + u, ZA + w], F       # axis +X; space centred on the mesh line (-Z)


def sweep_x(r, y=YA):
    return math.sqrt(max(r * r - y * y, 0.0))


if __name__ == "__main__":
    p = bevel_params(); print({k: round(v, 4) for k, v in p.items()})
    W, F = pinion_world(); print("pinion bbox", W.min(0).round(3), W.max(0).round(3))
    W, F = gear_world(); print("gear bbox", W.min(0).round(3), W.max(0).round(3))
