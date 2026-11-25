"""JUDGE (vyber): own moving model of the pan stage + lift module + neck, following T4 checks.py pan_model():
  rigid with pan     : group P minus crank + cables, + B golier_kotuc, + t4_pan.ffc_riser()
  pan + lift 0..20   : group L minus cables, + every B part below z 6 except collar ring / collar disc / CELOK / trup
  posed per lift     : crank (rameno_zdvih, cap_kluky, skr_ramena) at crank_angle(lift), fpc_lift(lift), pigtail_tris(lift)
  pan FFC loop       : fpc_loop(pan) (static frame, posed per pan)
Stored as surface samples (h 0.2) in the STAGE frame, with flag lifted (z range z..z+20).  -> mov.npz
Nothing outside /tmp/claude-0/gapwf/fin/R1/vyber is written."""
import sys, os, json, math, time
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib  # noqa
T4 = "/tmp/claude-0/gapwf/fin/T4"; BST = "/tmp/claude-0/gapwf/fin/B/stl"
sys.path.insert(0, T4); cwd = os.getcwd(); os.chdir(T4)
import t4_common as C  # noqa
import t4_pan as MP  # noqa
H = 0.2
RMIN = 20.0
t0 = time.time()
PJ = json.load(open("parts.json")); REC = {p["name"]: p for p in PJ["parts"]}
grp = {n: r["group"] for n, r in REC.items()}
CRANK = ("rameno_zdvih", "cap_kluky", "skr_ramena"); CABLE = ("ffc_par", "pigtail_zdvih")
P_rigid = [n for n in REC if grp[n] == "P" and n not in CRANK + CABLE]
L_set = [n for n in REC if grp[n] == "L" and n not in CABLE]
SKIPB = ("golier_prstenec", "golier_kotuc", "trup", "CELOK")
B_lift = [f[:-4] for f in sorted(os.listdir(BST)) if f.endswith(".stl") and not f.startswith(SKIPB)]


def tris(shape):
    V_, T_ = C.mesh_of(shape, 0.01, 0.1)
    return V_[T_]


def smp(tr):
    P = vlib.sample_surface(tr, H)
    return P[np.hypot(P[:, 0], P[:, 1]) >= RMIN]


rig, rig_t, lif, lif_t = [], [], [], []
for n in P_rigid:
    p = smp(vlib.load_stl(f"{T4}/stl/{n}.stl")); rig.append(p); rig_t += [n] * len(p)
p = smp(vlib.load_stl(f"{BST}/golier_kotuc.stl")); rig.append(p); rig_t += ["golier_kotuc"] * len(p)
p = smp(tris(MP.ffc_riser())); rig.append(p); rig_t += ["ffc_riser"] * len(p)
for n in L_set:
    p = smp(vlib.load_stl(f"{T4}/stl/{n}.stl")); lif.append(p); lif_t += [n] * len(p)
for n in B_lift:
    tr = vlib.load_stl(f"{BST}/{n}.stl")
    tr = tr[tr[:, :, 2].min(1) < 6.0]
    if not len(tr): continue
    p = smp(tr); p = p[p[:, 2] < 6.0]; lif.append(p); lif_t += ["B:" + n] * len(p)
print("rigid/lift sampled", f"{time.time()-t0:.0f}s", flush=True)
for n in CRANK:
    T0 = vlib.load_stl(f"{T4}/stl/{n}.stl")
    for lf in np.arange(0.0, 20.01, 0.5):
        th = MP.crank_angle(lf); a = math.radians(-th); c, s = math.cos(a), math.sin(a)
        T = T0.copy(); y, z = T0[..., 1] - MP.YL, T0[..., 2] - MP.ZL
        T[..., 1] = MP.YL + c * y - s * z; T[..., 2] = MP.ZL + s * y + c * z
        p = smp(T); rig.append(p); rig_t += [n] * len(p)
for lf in np.arange(0.0, 20.01, 1.0):
    p = smp(tris(MP.fpc_lift(lf))); rig.append(p); rig_t += ["fpc_lift"] * len(p)
    p = smp(MP.pigtail_tris(lf)); rig.append(p); rig_t += ["pigtail"] * len(p)
print("posed sampled", f"{time.time()-t0:.0f}s", flush=True)
loop = []
for pan in np.arange(-90.3, 90.31, 5.0):
    loop.append(smp(tris(MP.fpc_loop(pan))))
os.chdir(cwd)
R = np.concatenate(rig); Lf = np.concatenate(lif); LP = np.concatenate(loop)
np.savez_compressed(os.path.join(HERE, "mov.npz"), R=R.astype(np.float32), Rt=np.array(rig_t), L=Lf.astype(np.float32),
                    Lt=np.array(lif_t), LOOP=LP.astype(np.float32))
print("saved", len(R), len(Lf), len(LP), f"{time.time()-t0:.0f}s")
print("B lifted parts:", B_lift)
