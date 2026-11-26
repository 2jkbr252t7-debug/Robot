"""NOVA mini - arm drive B1+ (fixer revision R2c/oprava): concept solids for the images (LEFT side, world frame B, assembly
position).  Writes work/stl_b/*.stl + work/b1p_data.json.  Never touches T3 / T4 / B / R1.  Right side = mirror (Blender)."""
import os, sys, json, math
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import g2b as G
import t4_common as C
from build123d import (Box, Pos, Rot, Plane, Polyline, make_face, revolve, extrude, Axis, Solid, Face, Vector, export_stl)

OUT = os.path.join(HERE, "stl_b")
os.makedirs(OUT, exist_ok=True)
INFO = {}
YA, ZA, XV = G.YA, G.ZA, G.XV
ONLY = set(sys.argv[1:])


def save(s, name, tol=0.01):
    ok = s.is_valid
    bb = s.bounding_box()
    export_stl(s, os.path.join(OUT, name + ".stl"), tolerance=tol, angular_tolerance=0.12)
    INFO[name] = dict(valid=bool(ok), volume=round(s.volume, 2),
                      bbox=[round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    print(f"{name:18s} valid {ok} vol {s.volume:9.2f} bbox x {bb.min.X:.2f}..{bb.max.X:.2f} y {bb.min.Y:.2f}..{bb.max.Y:.2f} "
          f"z {bb.min.Z:.2f}..{bb.max.Z:.2f}", flush=True)
    return s


def lathe(pts):
    w = Polyline(*[(a, r, 0) for a, r in pts], close=True)
    return revolve(make_face(w), Axis.X, 360)


def on_sh(s):
    return Pos(0, YA, ZA) * s


def on_v(s, x=XV, y=YA):
    return Pos(x, y, 0) * Rot(0, -90, 0) * s


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def xcyl(r, x0, x1, y=YA, z=ZA):
    return Solid.make_cylinder(r, x1 - x0, Plane(origin=(x0, y, z), z_dir=(1, 0, 0)))


def zcyl(r, z0, z1, x=XV, y=YA):
    return Solid.make_cylinder(r, z1 - z0, Plane(origin=(x, y, z0), z_dir=(0, 0, 1)))


def prism_yz(poly, x0, x1):
    w = Polyline(*[(x0, y, z) for y, z in poly], close=True)
    return extrude(make_face(w), amount=x1 - x0, dir=(1, 0, 0))


def prism_xy(poly, z0, z1):
    w = Polyline(*[(x, y, z0) for x, y in poly], close=True)
    return extrude(make_face(w), amount=z1 - z0, dir=(0, 0, 1))


def union(lst):
    s = lst[0]
    for q in lst[1:]:
        s = s + q
    return s


def ring(ri, ro, a0, a1):
    return lathe([(a0, ri), (a1, ri), (a1, ro), (a0, ro)])


def hex_xy(af, z0, z1, x=XV, y=YA, rot=0.0):
    rc = af / math.sqrt(3)
    return prism_xy([(x + rc * math.cos(rot + math.pi / 3 * i), y + rc * math.sin(rot + math.pi / 3 * i)) for i in range(6)], z0, z1)


def hex_yz(af, x0, x1, rot=0.0):
    rc = af / math.sqrt(3)
    return prism_yz([(YA + rc * math.cos(rot + math.pi / 3 * i), ZA + rc * math.sin(rot + math.pi / 3 * i)) for i in range(6)], x0, x1)


def star_xy(n, r_out, r_in, z0, z1, x=XV, y=YA, frac=0.5):
    """n-tooth spline outline (trapezoid teeth), extruded along Z"""
    pts = []
    for i in range(n):
        c = 2 * math.pi * i / n
        w = math.pi / n
        for a, r in ((c - w, r_in), (c - w * frac * 0.6, r_in), (c - w * frac * 0.35, r_out), (c + w * frac * 0.35, r_out),
                     (c + w * frac * 0.6, r_in)):
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    return prism_xy(pts, z0, z1)


def sector_yz(r0, r1, az0, az1, x0, x1, n=40):
    pts = [G.az_pt(a, r1) for a in np.linspace(az0, az1, n)] + [G.az_pt(a, r0) for a in np.linspace(az1, az0, n)]
    return prism_yz(pts, x0, x1)


def want(n):
    return not ONLY or n in ONLY


# ================================================================================================ column (T_spodok part), v2 + fixer
B = G.BOSS
if want("stlp"):
    boss = xcyl(B["r"], *B["x"]) + on_sh(ring(B["stop"][0], B["stop"][1], B["stop"][2], B["stop"][3]))
    boss = boss - box(B["x"][0] - 0.1, B["stop"][3] + 0.1, YA - G.PLUG["slot_hw"], YA + G.PLUG["slot_hw"], B["slot"][0], B["slot"][1])
    T = G.TONGUE
    tongue = on_v(ring(T["ri"], T["ro"], T["z"][0], T["z"][1]))
    tongue = tongue + on_v(ring(2.5, T["ri"] + 0.01, T["z"][0], T["z"][0] + 0.5))
    tongue_root = box(B["x"][0], 37.4, YA - 3.0, YA + 3.0, T["z"][0], B["slot"][0])
    back = union([box(34.4, 41.5, 9.2, 15.5, -78.0, -33.0), box(34.4, 38.4, 9.2, 15.5, -33.0, -26.0),
                  box(31.5, 34.4, 9.2, 15.5, -70.5, -48.8)])
    front = box(34.4, 41.5, -20.0, -14.6, -78.0, -44.5)
    strut = prism_yz([(-20.0, -44.5), (-9.0, -44.5), (-9.0, -21.0), (-13.5, -25.0), (-20.0, -38.0)], 34.4, 38.4)
    web = box(30.5, 32.65, -14.6, 9.2, -70.5, -48.8) + zcyl(2.6, -52.7, -48.8, 29.5, 4.0)
    pad = box(32.65, 44.0, -14.6, 9.2, -69.0, -66.5)            # pad height set after measuring the servo
    snap = box(44.0, 45.9, -5.0, 1.0, -69.0, -68.2) + box(45.35, 45.9, -5.0, 1.0, -68.2, -65.4)
    col = union([boss, tongue, tongue_root, back, front, strut, web, pad, snap])
    col = col - zcyl(2.0, -46.0, -24.0)
    col = col - zcyl(T["ri"], T["z"][0] + 0.5, T["z"][1] + 0.1)
    col = col - zcyl(1.6, T["z"][0] - 2.0, T["z"][0] + 0.6)
    col = col - box(37.0, 41.6, -17.6, -14.5, -66.8, -63.2)                     # cable slot (front leg)
    col = col - zcyl(1.4, -52.8, -48.7, 29.5, 4.0)
    for h in (12, 4, 8):                                                         # M2 insert holes
        y, z = G.clock_pt(h, G.PLUG["screw_r"])
        col = col - xcyl(1.55, 34.9, 38.5, y, z)
    for h in (10, 2):                                                            # peg holes D2.5
        y, z = G.clock_pt(h, G.PLUG["screw_r"])
        col = col - xcyl(1.25, 36.4, 38.5, y, z)
    save(col, "stlp")
    ins = []
    for h in (12, 4, 8):
        y, z = G.clock_pt(h, G.PLUG["screw_r"])
        ins.append(xcyl(1.6, 34.9, 38.4, y, z) - xcyl(0.85, 34.8, 38.5, y, z))
    save(union(ins), "vlozky")
    save(zcyl(1.75, -52.2, -48.8, 29.5, 4.0) - zcyl(1.0, -52.3, -48.7, 29.5, 4.0), "vlozka_F3a")

# ================================================================================================ column fill voxels -> mesh
if want("vypln"):
    d = np.load(G.FILL)
    P = d["P"].astype(float); Wv = d["web"].astype(float)
    h = 0.5

    def vox_mesh(P, name):
        lo = P.min(0) - h
        idx = np.round((P - lo) / h).astype(int)
        n = idx.max(0) + 2
        occ = np.zeros(n, bool); occ[idx[:, 0], idx[:, 1], idx[:, 2]] = True
        tris = []
        for ax in range(3):
            for sgn in (1, -1):
                sh = np.roll(occ, -sgn, axis=ax)
                face = occ & ~sh
                ii = np.argwhere(face)
                for i, j, k in ii:
                    c = lo + np.array([i, j, k]) * h
                    off = np.zeros(3); off[ax] = sgn * h / 2
                    u = np.zeros(3); v = np.zeros(3)
                    u[(ax + 1) % 3] = h / 2; v[(ax + 2) % 3] = h / 2
                    f = c + off
                    q = [f - u - v, f + u - v, f + u + v, f - u + v]
                    if sgn < 0:
                        q = q[::-1]
                    tris.append([q[0], q[1], q[2]]); tris.append([q[0], q[2], q[3]])
        tris = np.array(tris)
        G.write_stl(os.path.join(OUT, name + ".stl"), tris)
        INFO[name] = dict(n_vox=int(len(P)), bbox=np.r_[P.min(0) - h / 2, P.max(0) + h / 2].round(2).tolist(), tris=int(len(tris)))
        print(name, INFO[name], flush=True)
    key = lambda A: set(map(tuple, np.round(A, 3)))
    KW = key(Wv)
    Pf = np.array([p for p in P if tuple(np.round(p, 3)) not in KW])
    vox_mesh(Pf, "vypln")
    vox_mesh(Wv, "vypln_priecka")

# ================================================================================================ servo SCS0009 (earless)
S = G.SERVO
if want("servo"):
    case = box(S["x"][0], S["x"][1], S["y"][0], S["y"][1], S["z"][0], S["z"][1])
    try:
        case = case.fillet(0.6, case.edges())
    except Exception as e:
        print("case fillet failed", e)
    for zg in (-47.6, -63.4):
        case = case - (box(S["x"][0] - 1, S["x"][1] + 1, S["y"][0] - 1, S["y"][1] + 1, zg - 0.2, zg + 0.2)
                       - box(S["x"][0] + 0.25, S["x"][1] - 0.25, S["y"][0] + 0.25, S["y"][1] - 0.25, zg - 0.3, zg + 0.3))
    case = case + box(37.6, 40.4, -15.3, -14.2, -66.0, -63.6)
    save(case, "servo_telo")
    spl = star_xy(20, S["spl_r"], S["spl_root"], S["z"][1] - 0.02, S["spl_top"]) + zcyl(S["spl_root"] + 0.01, S["z"][1] - 0.02, S["spl_top"])
    spl = spl - zcyl(S["thr_r"], S["z"][1] - 1.0, S["spl_top"] + 0.1)
    save(spl, "servo_hriadel")

# ================================================================================================ vertical drive
c = G.CUP
if want("spojka"):
    cup = zcyl(c["r"], c["z0"], c["hex"][1])
    try:
        cup = cup.fillet(0.4, [e for e in cup.edges() if abs(e.center().Z - c["hex"][1]) < 0.01])
    except Exception as e:
        print("cup fillet", e)
    rin_tip = c["spl_root"] / 2 - 0.0      # internal spline tooth tips r 1.725, roots r 1.975
    cup = cup - star_xy(20, c["spl_od"] / 2, rin_tip + 0.12, c["z0"] - 0.1, c["spl_top"]) - zcyl(rin_tip + 0.13, c["z0"] - 0.1, c["spl_top"])
    cup = cup - zcyl(c["hole_r"], c["floor"][0] - 0.1, c["floor"][1] + 0.1)
    cup = cup - zcyl(c["rec_r"], c["rec"][0], c["rec"][1] + 0.01)
    cup = cup - hex_xy(c["hex_af"], c["hex"][0], c["hex"][1] + 0.1)
    save(cup, "spojka")
    k = G.CSCREW
    scr = zcyl(k["head_r"], *k["head"]) - hex_xy(1.5, k["head"][1] - 1.0, k["head"][1] + 0.1)
    scr = scr + zcyl(k["r"], k["tip"], k["head"][0] + 0.01)
    save(scr, "skrutka_spojky")
sv = G.SHAFT_V
if want("hriadel_zvisly"):
    sh = hex_xy(sv["hex_af"], *sv["hex"]) + zcyl(sv["r"], sv["j"][0], sv["j"][1] + 0.01) + zcyl(sv["key_r"], sv["key"][0], sv["key"][1])
    sh = sh - box(XV + sv["flat"], XV + 2.0, YA - 2, YA + 2, sv["key"][0] + 0.3, sv["key"][1] + 0.1)
    save(sh, "hriadel_zvisly")
b = G.B1
if want("B1"):
    save(on_v(ring(b["ri"] + 0.45, b["ro"] - 0.45, b["z"][0] + 0.06, b["z"][1] - 0.06)), "B1_tesnenie")
    save(on_v(ring(b["ri"], b["ri"] + 0.45, b["z"][0], b["z"][1]) + ring(b["ro"] - 0.45, b["ro"], b["z"][0], b["z"][1])), "B1")
    ps = G.PSHIM
    save(on_v(ring(ps["ri"], ps["ro"], ps["z"][0], ps["z"][1])), "podlozka_pastorka")

# ================================================================================================ gears (numpy meshes)
if want("kolesa"):
    W, F = G.pinion_world()
    G.write_stl(os.path.join(OUT, "pastorok.stl"), G.tris_from(W, F))
    W2, F2 = G.gear_world()
    G.write_stl(os.path.join(OUT, "koleso.stl"), G.tris_from(W2, F2))
    INFO["pastorok"] = dict(bbox=np.r_[W.min(0), W.max(0)].round(3).tolist())
    INFO["koleso"] = dict(bbox=np.r_[W2.min(0), W2.max(0)].round(3).tolist())
    gs = G.GSHIM
    save(on_sh(ring(gs["ri"], gs["ro"], *gs["x"])), "podlozka_kolesa")

# ================================================================================================ arm shaft M4x20, bearings, sleeve, C-shim
if want("hriadel"):
    m = G.M4
    scr = on_sh(lathe([(m["x"][0], 0), (m["x"][0], m["r"] - 0.2), (m["x"][0] + 0.2, m["r"]), (m["head"][0], m["r"]),
                       (m["head"][0], m["head_r"]), (m["head"][1] - 0.3, m["head_r"]), (m["head"][1], m["head_r"] - 0.3),
                       (m["head"][1], 0)]))
    scr = scr - hex_yz(m["hex_af"], m["head"][1] - m["hex_d"], m["head"][1] + 0.1)
    save(scr, "skrutka_M4")
    for nm, d in (("A1", G.A1), ("A2", G.A2)):
        save(on_sh(ring(d["ri"], d["ri"] + 0.5, *d["x"]) + ring(d["ro"] - 0.5, d["ro"], *d["x"])), nm)
        save(on_sh(ring(d["ri"] + 0.5, d["ro"] - 0.5, d["x"][0] + 0.06, d["x"][1] - 0.06)), nm + "_tesnenie")
    s = G.SLEEVE
    save(on_sh(ring(s["ri"], s["ro"], *s["x"])), "puzdro")
    cs = G.CSHIM
    csh = on_sh(ring(cs["ri"], cs["ro"], *cs["x"]))
    csh = csh - box(cs["x"][0] - 0.1, cs["x"][1] + 0.1, YA, YA + 6.0, ZA - cs["open"] / 2, ZA + cs["open"] / 2)   # opening toward +Y
    save(csh, "c_podlozka")

# ================================================================================================ plug cartridge (zatka), fixer version
P = G.PLUG
if want("zatka"):
    ny, nz = 37, 37
    gy = np.linspace(YA - 16.0, YA + 16.0, ny); gz = np.linspace(ZA - 16.0, ZA + 16.0, nz)
    pts = [[Vector(C.x_surface(float(y), float(z)) - P["recess"], float(y), float(z)) for z in gz] for y in gy]
    face = Face.make_surface_from_array_of_points(pts)
    prism = extrude(face, amount=14.0, dir=(-1, 0, 0))
    body = on_sh(lathe([(P["neck_x"][0], 0), (P["neck_x"][0], P["neck_r"]), (P["neck_x"][1], P["neck_r"]),
                        (P["neck_x"][1], P["body_r"]), (51.0, P["body_r"]), (51.0, 0)]))
    body = body & prism
    ringp = on_sh(lathe([(43.0, 0), (43.0, P["ring_r"]), (P["ring_x1"], P["ring_r"]), (P["ring_x1"], P["seat_r"]),
                         (P["seat_x1"], P["seat_r"]), (P["seat_x1"], 0)]))
    plug = body + ringp
    lug = sector_yz(P["lug"]["r"][0], P["lug"]["r"][1], P["lug"]["az"][0], P["lug"]["az"][1], P["lug"]["x"][0] - 0.05, P["lug"]["x"][1])
    plug = plug + lug
    for h in (10, 2):
        y, z = G.clock_pt(h, P["screw_r"])
        plug = plug + xcyl(P["peg_r"], P["peg_x"][0], P["peg_x"][1] + 0.1, y, z)
    cav = on_sh(lathe([(38.0, 0), (38.0, P["cav_r"]), (P["cav_x1"], P["cav_r"]), (P["cav_x1"], 3.5), (P["bore7_x1"], 3.5),
                       (P["bore7_x1"], 2.5), (P["seat_x1"] + 0.5, 2.5), (P["seat_x1"] + 0.5, 0)]))
    plug = plug - cav
    plug = plug - box(38.0, P["slot_x1"], YA - P["slot_hw"], YA + P["slot_hw"], ZA - 15.0, ZA - 2.0)
    heads = []
    for hcl, (nm, L, extra) in G.SCREWS.items():
        y, z = G.clock_pt(hcl, P["screw_r"])
        xf = C.x_surface(y, z) - P["recess"]
        xh = xf - extra                                             # head top
        plug = plug - xcyl(1.1, 38.0, xf + 1.0, y, z)
        plug = plug - Solid.make_cone(1.0, 2.0, 1.0, Plane(origin=(xh - 0.95, y, z), z_dir=(1, 0, 0)))
        if extra > 0:
            plug = plug - xcyl(2.0, xh + 0.04, xf + 1.0, y, z)
        hd = Solid.make_cone(1.0, 1.9, 0.9, Plane(origin=(xh - 0.92, y, z), z_dir=(1, 0, 0))) + xcyl(0.98, xh - L, xh - 0.9, y, z)
        hd = hd - box(xh - 0.5, xh + 0.1, y - 0.15, y + 0.15, z - 0.75, z + 0.75) - box(xh - 0.5, xh + 0.1, y - 0.75, y + 0.75, z - 0.15, z + 0.15)
        heads.append(hd)
        INFO[f"screw_{hcl}"] = dict(face_x=round(xf, 2), head_x=round(xh, 2), tip_x=round(xh - L, 2), name=nm)
    save(plug, "zatka")
    save(union(heads), "zatka_skrutky")
    INFO["face_x_axis"] = round(C.x_surface(YA, ZA) - P["recess"], 3)

# ================================================================================================ arm side: 6800, hub, washer, drive hub, magnets, lip
if want("ruka"):
    d = G.B6800
    save(on_sh(ring(d["ri"], d["ri"] + d["ring"], *d["x"]) + ring(d["ro"] - d["ring"], d["ro"], *d["x"])), "L6800")
    save(on_sh(ring(d["ri"] + d["ring"], d["ro"] - d["ring"], d["x"][0] + 0.1, d["x"][1] - 0.1)), "L6800_tesnenie")
    H = G.HUB
    hub = on_sh(lathe([(H["x0"], H["ri"]), (H["bore_x"][0], H["ri"]), (H["bore_x"][0], H["bore_r"]), (H["fl"][0], H["bore_r"]),
                       (H["fl"][0], H["fl_ri"]), (H["fl"][1], H["fl_ri"]), (H["fl"][1], H["cav_r"]), (H["x1"], H["cav_r"]),
                       (H["x1"], H["ro"]), (H["x0"], H["ro"])]))
    rb = H["rib"]
    hub = hub + sector_yz(rb["r"][0], rb["r"][1] + 0.05, rb["az"][0], rb["az"][1], rb["x"][0], rb["x"][1])
    save(hub, "naboj_surovy")
    rib_only = sector_yz(rb["r"][0], rb["r"][1], rb["az"][0], rb["az"][1], rb["x"][0], rb["x"][1])
    save(rib_only, "rebro")
    w = G.WASHER
    save(on_sh(ring(w["ri"], w["ro"], *w["x"])), "podlozka_M10")
    D = G.DRIVE
    m = G.M4
    dh = on_sh(lathe([(D["boss_x"][0], D["boss"][0]), (D["x"][0], D["boss"][0]), (D["x"][0], 0.0), (D["x"][1], 0.0), (D["x"][1], D["r"]),
                      (D["x"][0], D["r"]), (D["x"][0], D["boss"][1]), (D["boss_x"][0], D["boss"][1])]))
    dh = dh - on_sh(lathe([(m["head"][0] - 0.1, 0), (m["head"][1], 0), (m["head"][1], m["head_r"]), (m["head"][0] - 0.1, m["head_r"])]))
    dh = dh + hex_yz(D["key_af"] - 0.05, m["head"][1] - m["hex_d"] + 0.2, m["head"][1] + 0.05)
    for i in range(D["n"]):
        y, z = G.az_pt(360.0 / D["n"] * i + 90.0, D["mag_R"])
        dh = dh - xcyl(D["pocket_r"], D["x"][0] + D["skin"], D["x"][1] + 0.1, y, z)
    save(dh, "unasac")
    mags = []
    for az in G.MAG["az"]:
        y, z = G.az_pt(az, D["mag_R"])
        mags.append(xcyl(G.MAG["r"], D["x"][0] + D["skin"] + 0.02, D["x"][0] + D["skin"] + 0.02 + G.MAG["t"], y, z))
    save(union(mags), "magnety_spojky")
    l = G.LIP
    save(on_sh(ring(l["ri"], l["ro"], *l["x"])), "kruzok")

# ================================================================================================ torso cutters (Blender booleans; same as v2)
if want("cut"):
    cut_L = box(30.4, 47.0, -21.0, 20.5, -78.0, -3.0) - zcyl(4.0, -80, 0, 27.09, 12.89)
    save(cut_L, "cut_spodok_L")

INFO_PATH = os.path.join(HERE, "b1p_data.json")
old = json.load(open(INFO_PATH)) if os.path.exists(INFO_PATH) else {}
old.update(INFO)
bc = G.BUCK
bx0, bx1 = bc["c"][0] - bc["size"][0] / 2, bc["c"][0] + bc["size"][0] / 2
by0, by1 = bc["c"][1] - bc["size"][1] / 2, bc["c"][1] + bc["size"][1] / 2
old["buck_box"] = [bx0, bx1, by0, by1, bc["ztop"] - bc["size"][2], bc["ztop"]]
old["cable"] = [(39.0, -14.9, -64.8), (39.5, -16.0, -65.0), (41.0, -16.2, -65.1), (42.3, -16.4, -66.2), (42.4, -16.6, -69.0),
                (41.5, -15.6, -70.3), (36.0, -13.6, -71.3), (31.0, -12.6, -72.0), (27.0, -11.9, -72.2), (24.0, -11.6, -71.0),
                (22.0, -11.0, -68.0)]
json.dump(old, open(INFO_PATH, "w"), indent=1)
print("done")
