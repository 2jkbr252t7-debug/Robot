"""Q6b: true (uncapped) minimum arm-head/neck distance over the sweep 0..135 for each head pose (coarser head sampling 0.5 mm)"""
import json, time
from armgeo import *
exec(open("q6.py").read().split("Hp, Hown, Np_, Nown = [], [], [], []")[0].split("t0 = time.time()")[1])
t0 = time.time()
Hp, Hown = [], []
for i, n in enumerate(HEAD + NECK):
    P = vlib.sample_surface(load(n, BST), 0.8); Hp.append(P); Hown.append(np.full(len(P), i))
Hp = np.concatenate(Hp); Hown = np.concatenate(Hown); isneck = Hown >= len(HEAD)
NAMES = HEAD + NECK
out = []
for lift in (0.0, 20.0):
    for tilt in (0.0, tilt_down_max(lift)):
        for pan in (0, 45, 85, -45, -85):
            Q = np.where(isneck[:, None], Hp + np.array([0, 0, lift]), rotx(Hp, tilt, 0.0, AXZ) + np.array([0, 0, lift]))
            Q = rotz(Q, pan)
            k = Q[:, 0] > 40.0
            P = Q[k]; own = Hown[k]
            best = (1e9, None, None, None)
            for a in range(-45, 136, 5):
                if not len(P): break
                sd = sdf_world(swing(P, -a), dmax=20.0); j = sd.argmin()
                if sd[j] < best[0]: best = (float(sd[j]), a, NAMES[own[j]], P[j].round(1).tolist())
            out.append(dict(lift=lift, tilt=tilt, pan=pan, min_clear=round(best[0], 2), at_arm=best[1], part=best[2], head_pt=best[3]))
            print("lift %4.1f tilt %4.1f pan %+3d: min arm-head distance over -45..135 = %.2f at arm %s deg, part %s, head point %s (%.0f s)" %
                  (lift, tilt, pan, best[0], best[1], best[2], best[3], time.time() - t0), flush=True)
json.dump(out, open("q6c_out.json", "w"), indent=1)
