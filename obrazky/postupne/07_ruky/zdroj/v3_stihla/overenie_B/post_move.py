"""where can the two upper cover-magnet posts (v1/v2 design: D3x2 magnet in a printed post r 2.2 x 2.4 each side of the seam,
3.5 inside the outline) go in variant B with M2b so that they clear the rotating drive hub by >= 0.3?"""
import sys, math, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar"); import variants as VA
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech"); import parts as PT
vid = sys.argv[1] if len(sys.argv) > 1 else "B"; oid = sys.argv[2] if len(sys.argv) > 2 else "M2b"
YA, ZA = 3.0, -17.0
mov = [p for p in PT.options()[oid]["parts"] if p.pebble and p.role in ("drive", "static")]
arm = [p for p in PT.options()[oid]["parts"] if p.pebble and p.role == "arm"]
def sdist2d(X, prof):
    P_ = np.asarray(prof, float); ins = PT._inpoly(X, P_); d = np.full(len(X), 1e9)
    for i in range(len(P_)):
        A, B = P_[i], P_[(i + 1) % len(P_)]; AB = B - A
        t = np.clip(((X - A) @ AB) / max(AB @ AB, 1e-12), 0, 1); d = np.minimum(d, np.linalg.norm(X - (A + t[:, None] * AB), axis=1))
    return np.where(ins, -d, d)
res = []
for u in np.r_[np.arange(0.02, 0.10, 0.01), np.arange(0.30, 0.52, 0.01)]:
    c, ti, to, w, _, _ = [float(np.asarray(v)) for v in VA.section(vid, u)]
    worst = (1e9, None)
    for side in (1, -1):
        th = np.linspace(0, 2 * np.pi, 48, endpoint=False)
        pts = [np.c_[np.full(48, c + side * (0.25 + s)), (w - 3.5) + rr * np.cos(th), -VA.L * u + rr * np.sin(th)]
               for s in np.linspace(0, 2.4, 13) for rr in (2.2, 1.1, 0.0)]
        W = VA.to_world(np.concatenate(pts), vid, -1.0)
        X = np.c_[W[:, 0], np.hypot(W[:, 1] - YA, W[:, 2] - ZA)]
        for p in mov:
            m = float(sdist2d(X, p.outline_xr() if p.mag is not None else p.prof).min())
            if m < worst[0]: worst = (m, p.name)
        # front post (y < 0) is the mirror in y about the centre line; azimuth differs but parts are revolved -> same
    # room for the post inside the shell: post top must stay 1.2 under the skin (post r 2.2 at 3.5 from the outline -> 1.3)
    res.append(dict(u=round(float(u), 2), min_to_moving=round(worst[0], 3), part=worst[1], w=round(w, 2), to=round(to, 2), ti=round(ti, 2)))
    print(res[-1])
json.dump(res, open(f"post_move_{vid}_{oid}.json", "w"), indent=1)
