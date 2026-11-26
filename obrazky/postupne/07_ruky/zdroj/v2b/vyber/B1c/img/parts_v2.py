"""NOVA mini - arm drive v2 (judge-final K3): concept solids for the images (LEFT side, world frame B, assembly position).
Writes work/stl/*.stl + work/v2_data.json.  Never touches T3 / T4 / B.  Right side = mirror (done in Blender)."""
import os, sys, json, math
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import g2 as G
import t4_common as C
from build123d import (Box, Pos, Rot, Plane, Polyline, make_face, revolve, extrude, Axis, Solid, Face, Vector, export_stl,
                       fillet, Location)

OUT = os.path.join(HERE, "stl")
os.makedirs(OUT, exist_ok=True)
INFO = {}
YA, ZA, XV = G.YA, G.ZA, G.XV


def save(s, name, tol=0.01):
    ok = s.is_valid
    bb = s.bounding_box()
    export_stl(s, os.path.join(OUT, name + ".stl"), tolerance=tol, angular_tolerance=0.12)
    INFO[name] = dict(valid=bool(ok), volume=round(s.volume, 2),
                      bbox=[round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    print(f"{name:16s} valid {ok} vol {s.volume:9.2f} bbox x {bb.min.X:.2f}..{bb.max.X:.2f} y {bb.min.Y:.2f}..{bb.max.Y:.2f} "
          f"z {bb.min.Z:.2f}..{bb.max.Z:.2f}", flush=True)
    return s


def lathe(pts):
    """closed profile [(a, r)] revolved about the X axis through the origin"""
    w = Polyline(*[(a, r, 0) for a, r in pts], close=True)
    return revolve(make_face(w), Axis.X, 360)


def on_sh(s):
    """lathe about X -> shoulder axis"""
    return Pos(0, YA, ZA) * s


def on_v(s, x=XV, y=YA):
    """lathe about X (a = z coordinate) -> vertical axis through (x, y)"""
    return Pos(x, y, 0) * Rot(0, -90, 0) * s


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def xcyl(r, x0, x1, y=YA, z=ZA):
    return Solid.make_cylinder(r, x1 - x0, Plane(origin=(x0, y, z), z_dir=(1, 0, 0)))


def zcyl(r, z0, z1, x=XV, y=YA):
    return Solid.make_cylinder(r, z1 - z0, Plane(origin=(x, y, z0), z_dir=(0, 0, 1)))


def prism_yz(poly, x0, x1):
    """polygon [(y, z)] extruded along X from x0 to x1"""
    w = Polyline(*[(x0, y, z) for y, z in poly], close=True)
    f = make_face(w)
    return extrude(f, amount=x1 - x0, dir=(1, 0, 0))


def union(lst):
    s = lst[0]
    for q in lst[1:]:
        s = s + q
    return s


def ring(ri, ro, a0, a1):
    return lathe([(a0, ri), (a1, ri), (a1, ro), (a0, ro)])


# ================================================================================================ column (new T_spodok part)
B = G.BOSS
boss = xcyl(B["r"], *B["x"]) + on_sh(ring(B["stop"][0], B["stop"][1], B["stop"][2], B["stop"][3]))
boss = boss - box(B["x"][0] - 0.1, B["stop"][3] + 0.1, YA - G.PLUG["slot_hw"], YA + G.PLUG["slot_hw"], B["slot"][0], B["slot"][1])
T = G.TONGUE
tongue = on_v(ring(T["ri"], T["ro"], T["z"][0], T["z"][1]))
tongue = tongue + on_v(ring(2.5, T["ri"] + 0.01, T["z"][0], T["z"][0] + 0.5))        # D5 shoulder under the bearing
# tongue root: web from the boss bottom strip to the ring
tongue_root = box(B["x"][0], 37.4, YA - 3.0, YA + 3.0, T["z"][0], B["slot"][0])
# back leg
back = union([box(34.4, 41.5, 9.2, 15.5, -78.0, -33.0), box(34.4, 38.4, 9.2, 15.5, -33.0, -26.0),
              box(31.5, 34.4, 9.2, 15.5, -70.5, -48.8)])
# front leg + strut
front = box(34.4, 41.5, -20.0, -14.6, -78.0, -44.5)
strut = prism_yz([(-20.0, -44.5), (-9.0, -44.5), (-9.0, -21.0), (-13.5, -25.0), (-20.0, -38.0)], 34.4, 38.4)
# web (left only) + F3a_2 insert boss
web = box(30.5, 32.65, -14.6, 9.2, -70.5, -48.8) + zcyl(2.6, -52.7, -48.8, 29.5, 4.0)
pad = box(32.65, 44.0, -14.6, 9.2, -69.0, -66.8)
snap = box(44.0, 45.9, -5.0, 1.0, -69.0, -68.2) + box(45.35, 45.9, -5.0, 1.0, -68.2, -65.4)
col = union([boss, tongue, tongue_root, back, front, strut, web, pad, snap])
# cuts: vertical shaft hole, tongue bore, cable slot, rod holes, insert + dowel holes
col = col - zcyl(2.0, -46.0, -24.0)
col = col - zcyl(T["ri"], T["z"][0] + 0.5, T["z"][1] + 0.1)
col = col - zcyl(1.6, T["z"][0] - 2.0, T["z"][0] + 0.6)
col = col - box(37.0, 41.6, -17.6, -14.5, -66.8, -63.2)
col = col - zcyl(1.525, -78.1, -32.0, 38.0, 12.35) - zcyl(1.525, -78.1, -47.0, 38.0, -17.3)
col = col - zcyl(1.4, -52.8, -48.7, 29.5, 4.0)
for h in (12, 4, 8):
    y, z = G.clock_pt(h, G.PLUG["screw_r"])
    col = col - xcyl(1.55, 34.9, 38.5, y, z)
for h in (10, 2):
    y, z = G.clock_pt(h, G.PLUG["screw_r"])
    col = col - xcyl(1.0, 36.4, 38.5, y, z)
save(col, "stlp")
rods = zcyl(1.5, -78.0, -32.0, 38.0, 12.35) + zcyl(1.5, -78.0, -47.0, 38.0, -17.3)
save(rods, "tyce")
ins = []
for h in (12, 4, 8):
    y, z = G.clock_pt(h, G.PLUG["screw_r"])
    ins.append(xcyl(1.6, 34.9, 38.4, y, z) - xcyl(0.85, 34.8, 38.5, y, z))
save(union(ins), "vlozky")
ins_f3 = zcyl(1.75, -52.2, -48.8, 29.5, 4.0) - zcyl(1.0, -52.3, -48.7, 29.5, 4.0)
save(ins_f3, "vlozka_F3a")
dow = []
for h in (10, 2):
    y, z = G.clock_pt(h, G.PLUG["screw_r"])
    dow.append(xcyl(1.0, 36.6, 40.4, y, z))
save(union(dow), "kolíky".replace("í", "i"))
poron = union([box(32.95, 44.0, -14.3, 8.9, -66.8, -66.5), box(34.4, 41.5, -14.6, -14.3, -63.0, -45.6),
               box(34.4, 41.5, 8.9, 9.2, -66.5, -45.6)])
save(poron, "poron")

# ================================================================================================ servo SCS0009 (earless)
S = G.SERVO
case = box(S["x"][0], S["x"][1], S["y"][0], S["y"][1], S["z"][0], S["z"][1])
try:
    case = case.fillet(0.6, case.edges())
except Exception as e:
    print("case fillet failed", e)
for zg in (-47.6, -63.4):                      # case joints (cosmetic grooves)
    case = case - (box(S["x"][0] - 1, S["x"][1] + 1, S["y"][0] - 1, S["y"][1] + 1, zg - 0.2, zg + 0.2)
                   - box(S["x"][0] + 0.25, S["x"][1] - 0.25, S["y"][0] + 0.25, S["y"][1] - 0.25, zg - 0.3, zg + 0.3))
case = case + zcyl(S["boss_r"], S["boss_z"][0] - 0.05, S["boss_z"][1])
case = case + box(37.6, 40.4, -15.3, -14.2, -66.0, -63.6)                # cable strain relief (front end, bottom)
save(case, "servo_telo")
save(zcyl(S["spl_r"], S["boss_z"][1] - 0.02, S["spl_top"]), "servo_hriadel")

# ================================================================================================ coupler, vertical shaft, B1
c = G.COUPLER
horn = zcyl(c["r"], c["z"][0], -42.7) - zcyl(S["spl_r"] + 0.02, c["z"][0] - 0.1, -42.6)
save(horn, "spojka_paka")
sleeve = zcyl(3.0, -42.7, c["z"][1]) - zcyl(1.5, -42.8, c["z"][1] + 0.1)
sleeve = sleeve - xcyl(0.8, XV, XV + 3.2, YA, -39.6)
save(sleeve, "spojka_puzdro")
grub = xcyl(0.8, XV + 1.6, XV + 2.95, YA, -39.6) - xcyl(0.45, XV + 2.5, XV + 3.0, YA, -39.6)
save(grub, "spojka_skrutka")
sv = G.SHAFT_V
shaft_v = zcyl(sv["r"], sv["z"][0], sv["z"][1]) - box(XV + 1.2, XV + 1.6, YA - 2, YA + 2, sv["z"][0] - 0.1, -37.5)
save(shaft_v, "hriadel_zvisly")
b = G.B1
save(on_v(ring(b["ri"] + 0.45, b["ro"] - 0.45, b["z"][0] - 0.04, b["z"][1] + 0.04)), "B1_tesnenie")
save(on_v(ring(b["ri"], b["ri"] + 0.45, b["z"][0], b["z"][1]) + ring(b["ro"] - 0.45, b["ro"], b["z"][0], b["z"][1])), "B1")
save(on_v(ring(1.55, 2.6, b["z"][1], b["z"][1] + 0.5)), "podlozka_B1")

# ================================================================================================ gears (numpy meshes)
W, F = G.pinion_world()
G.write_stl(os.path.join(OUT, "pastorok.stl"), G.tris_from(W, F))
W2, F2 = G.gear_world()
G.write_stl(os.path.join(OUT, "koleso.stl"), G.tris_from(W2, F2))
INFO["pastorok"] = dict(bbox=np.r_[W.min(0), W.max(0)].round(3).tolist())
INFO["koleso"] = dict(bbox=np.r_[W2.min(0), W2.max(0)].round(3).tolist())
save(on_sh(ring(2.0, 2.9, 44.05, 44.5)), "podlozka_A1")

# ================================================================================================ arm shaft, A1/A2, e-clip
sa = G.SHAFT_A
shaft_a = on_sh(lathe([(sa["x0"], 0), (sa["x0"], sa["r"]), (sa["xstep"], sa["r"]), (sa["xstep"], sa["r2"]), (sa["x1"], sa["r2"]),
                       (sa["x1"], 0)]))
shaft_a = shaft_a - box(sa["xstep"] - 0.05, sa["x1"] + 0.1, YA + 1.2, YA + 2.1, ZA - 2, ZA + 2)     # D-flat for washer 1
save(shaft_a, "hriadel_ruky")
for nm, d in (("A1", G.A1), ("A2", G.A2)):
    save(on_sh(ring(d["ri"], d["ri"] + 0.5, *d["x"]) + ring(d["ro"] - 0.5, d["ro"], *d["x"])), nm)
    save(on_sh(ring(d["ri"] + 0.5, d["ro"] - 0.5, d["x"][0] - 0.04, d["x"][1] + 0.04)), nm + "_tesnenie")
ec = on_sh(ring(1.65, 3.6, 51.15, 51.75)) - box(51.0, 52.0, YA - 1.4, YA + 1.4, ZA - 4.0, ZA)
save(ec, "poistka")

# ================================================================================================ plug cartridge (zatka)
P = G.PLUG
ny, nz = 37, 37
gy = np.linspace(YA - 16.0, YA + 16.0, ny); gz = np.linspace(ZA - 16.0, ZA + 16.0, nz)
pts = [[Vector(C.x_surface(float(y), float(z)) - P["recess"], float(y), float(z)) for z in gz] for y in gy]
face = Face.make_surface_from_array_of_points(pts)
prism = extrude(face, amount=14.0, dir=(-1, 0, 0))
print("face prism valid", prism.is_valid, "vol", round(prism.volume, 1), flush=True)
body = on_sh(lathe([(P["neck_x"][0], 0), (P["neck_x"][0], P["neck_r"]), (P["neck_x"][1], P["neck_r"]),
                    (P["neck_x"][1], P["body_r"]), (51.0, P["body_r"]), (51.0, 0)]))
body = body & prism
print("body after face cut", body.is_valid, round(body.volume, 1), flush=True)
ringp = on_sh(lathe([(43.0, 0), (43.0, P["ring_r"]), (P["ring_x1"], P["ring_r"]), (P["ring_x1"], P["seat_r"]),
                     (P["seat_x1"], P["seat_r"]), (P["seat_x1"], 0)]))
plug = body + ringp
cav = on_sh(lathe([(38.0, 0), (38.0, P["cav_r"]), (P["cav_x1"], P["cav_r"]), (44.4, 3.5), (47.05, 3.5), (47.05, 2.6),
                   (48.55, 2.6), (48.55, 3.5), (51.05, 3.5), (51.05, 3.8), (51.9, 3.8), (51.9, 2.3), (58.0, 2.3), (58.0, 0)]))
plug = plug - cav
plug = plug - box(38.0, P["slot_x1"], YA - P["slot_hw"], YA + P["slot_hw"], ZA - 15.0, ZA - 2.0)
heads = []
for h in (12, 4, 8):
    y, z = G.clock_pt(h, P["screw_r"])
    xf = C.x_surface(y, z) - P["recess"]
    plug = plug - xcyl(1.1, 38.0, xf + 1.0, y, z)
    cs = Solid.make_cone(1.1, 2.6, 1.5, Plane(origin=(xf - 0.95, y, z), z_dir=(1, 0, 0)))
    plug = plug - cs
    hd = Solid.make_cone(1.0, 1.85, 0.85, Plane(origin=(xf - 0.92, y, z), z_dir=(1, 0, 0))) + xcyl(1.0, 34.0, xf - 0.9, y, z)
    hd = hd - box(xf - 0.6, xf + 0.1, y - 0.55, y + 0.55, z - 0.55, z + 0.55)            # socket
    heads.append(hd)
for h in (10, 2):
    y, z = G.clock_pt(h, P["screw_r"])
    plug = plug - xcyl(1.0, 38.0, 40.5, y, z)
save(plug, "zatka")
save(union(heads), "zatka_skrutky")
INFO["face_x_axis"] = round(C.x_surface(YA, ZA) - P["recess"], 3)
# homing pin on the ring end (azimuth -50 deg from 6 o'clock toward the back -> hidden)
th = math.radians(-50.0)
py, pz = YA + 4.1 * math.sin(th), ZA - 4.1 * math.cos(th)
save(xcyl(0.5, P["seat_x1"] - 0.3, 58.15, py, pz), "doraz_kolik")
INFO["pin_yz"] = [round(py, 3), round(pz, 3)]

# ================================================================================================ arm side: 6700, hub, clutch stack
d = G.B6700
save(on_sh(ring(d["ri"], d["ri"] + 0.9, *d["x"]) + ring(d["ro"] - 0.9, d["ro"], *d["x"])), "L6700")
save(on_sh(ring(d["ri"] + 0.9, d["ro"] - 0.9, d["x"][0] - 0.05, d["x"][1] + 0.05)), "L6700_tesnenie")
cl = G.CLUTCH
hub = on_sh(lathe([(47.0, 7.0), (53.5, 7.0), (53.5, 7.5), (57.5, 7.5), (57.5, 6.0), (cl["fl"][0], 6.0), (cl["fl"][0], 5.85),
                   (cl["fl"][1] + 0.2, 5.85), (cl["fl"][1] + 0.2, 10.2), (47.0, 10.2)]))
# homing lug (rotates with the arm), drawn at rest at azimuth +40 deg (meets the pin at -50 deg after -90 deg of swing)
lug = on_sh(lathe([(57.65, 3.35), (58.15, 3.35), (58.15, 6.2), (57.65, 6.2)])) & prism_yz(
    [(YA + 0.0, ZA), (YA + 8.0 * math.sin(math.radians(28)), ZA - 8.0 * math.cos(math.radians(28))),
     (YA + 8.0 * math.sin(math.radians(52)), ZA - 8.0 * math.cos(math.radians(52)))], 57.0, 59.0)
hub = hub + lug
save(hub, "naboj_surovy")
save(on_sh(ring(1.6, 5.85, cl["fl"][0], cl["fl"][1])), "priruba")
w1 = on_sh(ring(1.5, 3.0, *cl["w1"])) - box(cl["w1"][0] - 0.1, cl["w1"][1] + 0.1, YA + 1.2, YA + 1.6, ZA - 1.6, ZA + 1.6)
save(w1, "podlozka_1")
save(on_sh(ring(1.6, 3.6, *cl["w2"])), "podlozka_2")
save(on_sh(lathe([(cl["spr"][0], 2.1), (cl["spr"][0] + 0.3, 2.1), (cl["spr"][1], 4.0), (cl["spr"][1] - 0.3, 4.0)])), "pruzina")
save(on_sh(ring(1.55, 3.4, *cl["w3"])), "podlozka_3")
scr = on_sh(lathe([(cl["head"][0], 0), (cl["head"][0], 1.9), (cl["head"][1] - 0.25, 1.9), (cl["head"][1], 1.65), (cl["head"][1], 0)]))
scr = scr + xcyl(1.0, 56.8, cl["head"][0] + 0.05)
hexp = [(YA + 0.8 * math.cos(math.pi / 3 * i), ZA + 0.8 * math.sin(math.pi / 3 * i)) for i in range(6)]
scr = scr - prism_yz(hexp, cl["head"][1] - 0.9, cl["head"][1] + 0.1)
save(scr, "skrutka_ruky")

# ================================================================================================ torso cutters (Blender booleans)
cut_L = box(30.4, 47.0, -21.0, 20.5, -78.0, -3.0) - zcyl(4.0, -80, 0, 27.09, 12.89)
save(cut_L, "cut_spodok_L")
save(box(-47.0, -32.65, -21.0, 20.5, -78.0, -3.0), "cut_spodok_P")
bc = G.BUCK
bx0, bx1 = bc["c"][0] - bc["size"][0] / 2, bc["c"][0] + bc["size"][0] / 2
by0, by1 = bc["c"][1] - bc["size"][1] / 2, bc["c"][1] + bc["size"][1] / 2
save(box(bx0 - 0.3, bx1 + 0.3, by0 - 0.3, by1 + 0.3, bc["ztop"] - bc["size"][2] - 0.5, bc["ztop"] + 0.2), "cut_menic")
save(box(31.0, 40.0, -30.0, 30.0, -50.0, -40.0) - zcyl(3.15, -51, -39, 29.5, 4.0), "cut_paluba")
save(box(39.0, 41.2, YA - 2.0, YA + 2.0, -33.5, -27.5), "cut_bok_L")
# right-side web = J1 cradle end wall thickened to x -32.65
save(box(-32.65, -31.9, -14.6, 9.2, -70.5, -48.8), "stena_P")

# ================================================================================================ data for Blender / sheets
INFO["buck_box"] = [bx0, bx1, by0, by1, bc["ztop"] - bc["size"][2], bc["ztop"]]
cable = [(39.0, -14.9, -64.8), (39.5, -16.0, -65.0), (41.0, -16.2, -65.1), (42.3, -16.4, -66.2), (42.4, -16.6, -69.0),
         (41.5, -15.6, -70.3), (36.0, -13.6, -71.3), (31.0, -12.6, -72.0), (27.0, -11.9, -72.2), (24.0, -11.6, -71.0),
         (22.0, -11.0, -68.0)]
INFO["cable"] = cable
json.dump(INFO, open(os.path.join(HERE, "v2_data.json"), "w"), indent=1)
print("done")
