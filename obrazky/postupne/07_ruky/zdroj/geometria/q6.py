"""Q6: left arm vs head / neck of variant B over head poses (pan, lift, tilt).  Arm swept about the shoulder axis."""
import json, time
from armgeo import *
t0 = time.time()
HEAD = ["hlava_skrupina", "ram_displeja", "displej", "pena_displeja", "drziak_displeja", "magnety", "usi", "led_kruzky",
        "led_dosky", "oci_len_vizualizacia", "usko_kryt", "usko_lozisko", "paka", "klzny_kruzok"]
NECK = ["krk_predna_polovica", "krk_zadna_polovica"]
AXZ = -3.5
CRIT = 2.0


def rotx(Q, deg, cy=0.0, cz=0.0):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a); R_ = np.array(Q, float, copy=True)
    y, z = R_[..., 1] - cy, R_[..., 2] - cz
    R_[..., 1] = c * y - s * z + cy; R_[..., 2] = s * y + c * z + cz
    return R_


def rotz(Q, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a); R_ = np.array(Q, float, copy=True)
    x, y = R_[..., 0], R_[..., 1]
    R_[..., 0] = c * x - s * y; R_[..., 1] = s * x + c * y
    return R_


def tilt_down_max(lift):
    return round(min(40.0, 4.0 + 1.9 * float(lift)), 3)


Hp, Hown, Np_, Nown = [], [], [], []
for i, n in enumerate(HEAD):
    P = vlib.sample_surface(load(n, BST), 0.3); Hp.append(P); Hown.append(np.full(len(P), i))
for i, n in enumerate(NECK):
    P = vlib.sample_surface(load(n, BST), 0.3); Np_.append(P); Nown.append(np.full(len(P), i))
Hp = np.concatenate(Hp); Hown = np.concatenate(Hown); Np_ = np.concatenate(Np_); Nown = np.concatenate(Nown)
NAMES = HEAD + NECK
print("head samples %d, neck samples %d (%.0f s)" % (len(Hp), len(Np_), time.time() - t0))
POS = list(range(0, 136, 5)); NEG = list(range(0, -46, -5))
out = []
for lift in (0.0, 20.0):
    for tilt in (0.0, tilt_down_max(lift)):
        for pan in (0, 45, 85, -45, -85):
            Q = rotz(rotx(Hp, tilt, 0.0, AXZ) + np.array([0, 0, lift]), pan)
            Qn = rotz(Np_ + np.array([0, 0, lift]), pan)
            P = np.concatenate([Q, Qn]); own = np.concatenate([Hown, Nown + len(HEAD)])
            k = P[:, 0] > 49.49 - 6.0                       # x is invariant under the arm swing: only these can come within 6 mm
            P = P[k]; own = own[k]
            def clr(a):
                if len(P) == 0: return 99.0, None, None
                sd = sdf_world(swing(P, -a)); j = sd.argmin()
                return float(sd[j]), NAMES[own[j]], P[j].round(2).tolist()
            rec = dict(lift=lift, tilt=tilt, pan=pan, n_pts=int(len(P)), pos={}, neg={})
            lim = None
            for a in POS:
                d, part, at = clr(a); rec["pos"][a] = round(d, 3)
                if d < CRIT:
                    # refine 1 deg
                    a_ok = a - 5
                    for b in range(a - 4, a + 1):
                        d2, part2, at2 = clr(b)
                        if d2 < CRIT:
                            lim = dict(max_angle=a_ok, first_fail=b, d_fail=round(d2, 3), part=part2, at=at2); break
                        a_ok = b
                    break
            if lim is None: lim = dict(max_angle=135, first_fail=None)
            dmin = min(rec["pos"].values())
            rec["limit_pos"] = lim
            limn = None
            for a in NEG:
                d, part, at = clr(a); rec["neg"][a] = round(d, 3)
                if d < CRIT: limn = dict(min_angle=a + 5, part=part, at=at); break
            rec["limit_neg"] = limn or dict(min_angle=-45)
            d135 = clr(135) if lim["max_angle"] == 135 else (None, None, None)
            rec["clear_at_135"] = d135[0]
            out.append(rec)
            print("lift %4.1f tilt %4.1f pan %+3d : pts %6d  max arm angle %s  (first fail %s: %s mm, part %s at %s)  back limit %s  | min clr over 0..%d: %.2f (%.0f s)" %
                  (lift, tilt, pan, len(P), lim["max_angle"], lim.get("first_fail"), lim.get("d_fail"), lim.get("part"), lim.get("at"),
                   rec["limit_neg"]["min_angle"], max(rec["pos"]), dmin, time.time() - t0), flush=True)
json.dump(out, open("q6_out.json", "w"), indent=1)
