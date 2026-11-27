"""C7: hidden internals of the variant plug STLs vs the M2b static / torso parts (which the plug must carry) and vs the M2b
arm-side bearing: penetration test of M2b part surface samples inside the plug solid (ray parity along +x)."""
import sys, os, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
import numpy as np
import mio, klb as K
M2B = "/tmp/claude-0/gapwf/fin/R3/mech/stl/M2b"


def inside_mesh(T, Q):
    """ray parity along +x (slightly skewed) for points Q against triangle soup T"""
    d = np.array([1.0, 1e-4, 2e-4]); d /= np.linalg.norm(d)
    cnt = np.zeros(len(Q), int)
    v0, v1, v2 = T[:, 0], T[:, 1], T[:, 2]
    e1 = v1 - v0; e2 = v2 - v0
    h = np.cross(d, e2); a = np.einsum("ij,j->i", e1, h) if False else (e1 * h).sum(1)
    for i in range(0, len(Q), 200):
        q = Q[i:i + 200]
        s = q[:, None, :] - v0[None]
        f = 1.0 / np.where(np.abs(a) > 1e-14, a, 1e-14)
        u = f[None] * (s * h[None]).sum(2)
        qq = np.cross(s, e1[None])
        v = f[None] * (qq @ d)
        t = f[None] * (qq * e2[None]).sum(2)
        hit = (np.abs(a)[None] > 1e-14) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        cnt[i:i + 200] = hit.sum(1)
    return cnt % 2 == 1


OUT = {}
for vid in ("K0", "K1", "K2", "K3", "K3v"):
    sh = K.arm_dx(vid) - K.DX0
    T = mio.load(K.stl(vid, f"PLG_zatka_{vid}"))
    row = {}
    for nm in ("BRG_MR128_vnut", "BRG_MR128_vonk", "BRG_A2_MR74", "M4_DIN7984_M4x20", "PLG_doraz", "ARM_rebro", "ARM_naboj"):
        Q = mio.sample(mio.load(os.path.join(M2B, nm + ".stl")), 0.25).copy(); Q[:, 0] += sh
        ins = inside_mesh(T, Q)
        row[nm] = dict(n=int(len(Q)), inside_plug=int(ins.sum()),
                       xr_range=None if not ins.any() else [mio.xr(Q[ins])[:, 0].min().round(2), mio.xr(Q[ins])[:, 0].max().round(2),
                                                           mio.xr(Q[ins])[:, 1].min().round(2), mio.xr(Q[ins])[:, 1].max().round(2)])
    OUT[vid] = row
    print(vid, {k: (v["inside_plug"], v["xr_range"]) for k, v in row.items() if v["inside_plug"]})
json.dump(OUT, open(os.path.join(HERE, "c7_plug_m2b.json"), "w"), indent=1, default=float)
