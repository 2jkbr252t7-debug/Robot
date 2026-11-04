"""CONCEPT 3 (user): the NECK itself turns (pan), inserted into a FIXED neck base that is screwed to the torso.
Base = black, oval, its top dips to the front and back (like the user's photo) with a round lip around the neck.
Neck = v6 neck with a round bottom (turns inside the lip, 0.5 mm gap) + barrel/caps/head unchanged."""
import os, sys, time, math, json
sys.path.insert(0, "/home/user/Robot")
from nova import spec
spec.MATERIALS["servo_blue"] = dict(desc="servo", rgb=(0.22, 0.42, 0.86), rough=0.45)
spec.MATERIALS["bracket"] = dict(desc="držiak", rgb=(0.60, 0.38, 0.86), rough=0.45)
from build123d import (Axis, Location, Pos, Rot, Cylinder, Box, Solid, Edge, Wire, Vector, export_stl,
                       BuildSketch, Plane, RectangleRounded, extrude, fillet)
from nova.cad.common import PartRec, export_parts
from nova_mini import krk as K
from nova_mini import hlava_skrupina as HS
from nova_v8 import klasik as KL
B = "/tmp/claude-0/pan15"
t0 = time.time()
def zcyl(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)
def sstep(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
TOP = 4.0                       # torso top / base top (level part)
R_N = 14.0                      # narrower neck bottom (user: "o čosi užší"), turns inside the collar ring, gap 0.5
RING_IN, RING_OUT = 14.5, 20.5  # fixed sunk collar ring, flush with the domed torso top
K.NX_TOP, K.NY_TOP = 11.0, 6.5
K.Z_N1 = 13.0                   # head much closer to the torso (user: smaller gap between head and torso)
K.AX_Z = K.Z_N1 + K.B_R - 2.0
K.HEAD_Z0 = K.AX_Z - 3.0          # barrel mostly inside the head (user: "valec nemôže až tak vytŕčať")
K.HEAD_DY = 0.0                 # joint under the middle of the head (user sketch "nejako takto")
K.NY_TOP = 5.0
Z_J = TOP                       # neck emerges here
FOOT_Z0 = -4.0
# ---------- rotating neck: v6 barrel + bell with a ROUND bottom ----------
def prof(z):
    t = min(1.0, max(0.0, (z - Z_J) / (K.Z_N1 - Z_J)))
    return (K.NX_TOP + (R_N - K.NX_TOP) * (1 - t) ** 1.8,      # cone with a soft flare at the bottom (sketch)
            -(K.NY_TOP + (R_N - K.NY_TOP) * (1 - t) ** 1.9),
            K.NY_TOP + (R_N - K.NY_TOP) * (1 - t) ** 1.6)
K._prof = prof
K.BELL_Z0 = Z_J
K.collar_plate = lambda: zcyl(R_N, FOOT_Z0, Z_J + 0.05)
K.COLLAR_TOP = Z_J
K.dome_cutter = lambda gap=0.6: zcyl(60, -40, FOOT_Z0 - 0.5)
K.C_A = K.C_B = 4.2 + 10.5
K.N3_SCREW_X = 8.0
P = K.build_all(verbose=True)
N1 = P["N1"]
print("N1", N1.is_valid, len(N1.solids()), flush=True)
HS.R_BACK = 25.0
sys.path.insert(0, "/tmp/claude-0/pan15")
import softhead as SH
mv = Location((0, K.HEAD_DY, K.HEAD_Z0))
saddle, hcut = K.head_saddle_cut()
head = (SH.outer() - SH.white_cut()).moved(mv) - hcut      # white shell behind the black visor
eyes = None
for _sx in (-1, 1):
    _e = Pos(_sx * 11.0, SH.YF + K.HEAD_DY - 0.2, K.HEAD_Z0 + 38.0) * Box(10.0, 0.4, 17.5)
    _e = fillet([ed for ed in _e.edges() if abs(ed.tangent_at(0.5).Y) > 0.9], 4.9)
    eyes = _e if eyes is None else eyes + _e
frame = SH.visor().moved(mv) - hcut      # black glass visor, visible from the side (photo)
screen = Pos(0, SH.YF + SH.GLASS_REC + K.HEAD_DY - 0.12, K.HEAD_Z0 + 36.0) * Box(80.0, 0.25, 48.0)
_d, _r = SH.ears()
ears, leds = _d.moved(mv), _r.moved(mv)
print("custom head", head.is_valid, "glass", frame.is_valid, flush=True)
cam_ring = Pos(0, SH.YF + K.HEAD_DY - 0.35, K.HEAD_Z0 + 62.0) * Rot(90, 0, 0) * Cylinder(3.0, 0.7)
cam_lens = Pos(0, SH.YF + K.HEAD_DY - 0.75, K.HEAD_Z0 + 62.0) * Rot(90, 0, 0) * Cylinder(1.9, 0.3)
# ---------- domed torso top (original KLASIK shoulders) + fixed collar ring flush in it ----------
KL.K["torso"]["w"], KL.K["torso"]["d"] = 108.0, 74.0     # torso about as wide as the head (sketch)
torso = KL.loft(KL.torso_secs()).moved(Location((0, 0, -117.0 + TOP)))
band = zcyl(RING_OUT, TOP - 4.0, TOP + 1.0)
base = (torso & band) - zcyl(RING_IN, -10, 10)
torso = torso - zcyl(RING_OUT + 0.4, TOP - 4.4, TOP + 1.0) - zcyl(RING_IN, -70, 10) - zcyl(30.0, -70, -11.0) - zcyl(19.6, -11.0, TOP - 4.4)
print("base", base.is_valid, round(base.volume), "torso", torso.is_valid, flush=True)
# ---------- pan drive (hidden): N3 on the neck foot, hub on a 6805 bearing, vertical MG90S ----------
n3 = zcyl(R_N, -5.5, -4.0) + (zcyl(12.5, -12.0, -5.4) - zcyl(9.5, -12.1, -5.6))
n3 = n3 + (zcyl(12.5, -13.5, -12.0) - zcyl(1.6, -14, -11) - zcyl(2.2, -14, -11, 5.5, 5.5))
n3 = n3 - zcyl(2.6, -11.9, -3.9, 5.5, 5.5)
brg = zcyl(18.5, -12.0, -5.0) - zcyl(12.5, -12.1, -4.9)
housing = (zcyl(22.0, -13.0, -6.0) - zcyl(18.5, -12.5, -5.9)) - zcyl(16.0, -14, -12.4)
housing = housing + (zcyl(26.0, -13.0, -11.6) - zcyl(21.9, -13.1, -11.5))
_c = Pos(5.5, 0, -18.0 - 22.5 / 2) * Box(22.8, 12.2, 22.5)
pservo = fillet(_c.edges(), 0.5) + zcyl(5.9, -18.0, -15.0) + zcyl(2.4, -15.0, -13.6) + Pos(5.5, 0, -23.5) * Box(32.3, 12.2, 2.5)
horn = ((Pos(0, 0, -13.75) * (Box(14, 5.2, 1.5) + Box(5.2, 14, 1.5))) & zcyl(7.0, -15, -12)) + zcyl(3.5, -15.2, -13.6)
bracket = (Pos(5.5, 0, -25.75) * Box(44.0, 18.0, 2.0)) - Pos(5.5, 0, -25.75) * Box(23.4, 12.8, 3.0)
for xs in (-17.0, 28.0):
    bracket = bracket + Pos(xs, 0, (-26.75 + -12.9) / 2) * Box(3.0, 18.0, 13.85)
cab = zcyl(1.5, -20.0, 3.0, 5.5, 5.5) + Pos(5.5, 5.5 + 7.0, -20.0) * Rot(90, 0, 0) * Cylinder(1.5, 14.0)
# ---------- checks ----------
ax = Axis((0, 0, K.AX_Z), (1, 0, 0))
pan = Axis((0, 0, 0), (0, 0, 1))
res = {}
for ang in (-40, -35, -30, 30, 35, 40):
    hr = head.rotate(ax, ang)
    dr = K.display_envelope().rotate(ax, ang)
    res[ang] = (round(hr.distance_to(base), 2), round(hr.distance_to(N1), 3), round(dr.distance_to(P["S1"]), 2),
                round((hr & N1).volume if (hr & N1) else 0, 3))
    print(f"  tilt {ang:+d}: head-base {res[ang][0]} head-N1 {res[ang][1]} display-servo {res[ang][2]} INT {res[ang][3]}", flush=True)
json.dump({"tilt": res}, open(f"{B}/clear.json", "w"))
# ---------- render set ----------
recs = [PartRec("N1", "krk", N1, "black_satin", "neck", "J2", internal=True),
        PartRec("BASE", "zapusteny golier (pevny)", base, "black_satin", "torso", "J1", internal=True),
        PartRec("N2P", "viecko P", P["N2P"], "black_satin", "neck", "J3", internal=True),
        PartRec("N2L", "viecko L", P["N2L"], "black_satin", "neck", "J3", internal=True),
        PartRec("S1", "servo naklonu", P["S1"], "servo_blue", "neck", "J2", internal=True),
        PartRec("HORN", "paka serva", P["HORN"], "white", "neck", "J3", internal=True),
        PartRec("L1", "lozisko MR128", P["L1"], "metal", "neck", "J3", internal=True),
        PartRec("N3", "unasac + naboj", n3, "grey", "neck", "J2", internal=True),
        PartRec("BRG", "lozisko 6805", brg, "metal", "torso", "J1", internal=True),
        PartRec("HOUSING", "puzdro loziska", housing, "bracket", "torso", "J1", internal=True),
        PartRec("PSERVO", "servo otacania", pservo, "servo_blue", "torso", "J1", internal=True),
        PartRec("PHORN", "paka serva otacania", horn, "white", "torso", "J2", internal=True),
        PartRec("BRACKET", "drziak serva", bracket, "bracket", "torso", "J1", internal=True),
        PartRec("CABLE", "kabel do hlavy", cab, "rubber", "neck", "J2", internal=True),
        PartRec("HEAD", "hlava", head, "white", "head", "J3"),
        PartRec("FRAME", "predne sklo", frame, "black_gloss", "head", "J3"),
        PartRec("EYES", "oci", eyes, "eye", "head", "J3"),
        PartRec("EARS", "usi", ears, "black_satin", "head", "J3"),
        PartRec("LEDS", "led krúžky uší", leds, "cyan_led", "head", "J3"),
        PartRec("CAMR", "kamera", cam_ring, "metal", "head", "J3"),
        PartRec("CAML", "kamera sklo", cam_lens, "glass", "head", "J3"),
        PartRec("TORSO", "trup (ilustracne)", torso, "white", "torso", "J1")]
for nm, s in {"N1": N1, "N2P": P["N2P"], "N2L": P["N2L"], "HEAD": head, "FRAME": frame, "EARS": ears, "CAMR": cam_ring, "CAML": cam_lens, "EYES": eyes, "LEDS": leds}.items():
    src = next(r for r in recs if r.id == nm)
    recs.append(PartRec(f"{nm}_P", src.name, s.rotate(pan, 35), src.mat, src.sub, src.joint))
for nm, s in {"N1": N1, "N2P": P["N2P"], "N2L": P["N2L"], "BASE": base}.items():
    src = next(r for r in recs if r.id == nm)
    recs.append(PartRec(f"{nm}_X", src.name, s, src.mat, src.sub, src.joint))
export_parts(recs, "pan3", step=False, out_dir=B)
for r in recs:
    export_stl(r.shape, f"{B}/stl/{r.id}.stl", tolerance=0.02, angular_tolerance=0.1)
print("done", f"{time.time()-t0:.0f}s", flush=True)
