import sys, struct, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as V

def tri_rows(R, c0, c1, closed=True):
    K, N, _ = R.shape
    V_ = R.reshape(-1, 3); idx = lambda k, j: k * N + (j % N)
    F = []
    for k in range(K - 1):
        for j in range(N if closed else N - 1):
            a, b, c, d = idx(k, j), idx(k, j + 1), idx(k + 1, j), idx(k + 1, j + 1)
            F += [(a, c, b), (b, c, d)]
    i0 = len(V_); i1 = i0 + 1
    V_ = np.vstack([V_, c0, c1])
    for j in range(N):
        F.append((i0, idx(0, j + 1), idx(0, j)))
        F.append((i1, idx(K - 1, j), idx(K - 1, j + 1)))
    return V_, np.array(F)

def orient(Vv, F):
    # make normals point outward (signed volume > 0)
    a, b, c = Vv[F[:, 0]], Vv[F[:, 1]], Vv[F[:, 2]]
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6
    return (F[:, [0, 2, 1]] if vol < 0 else F), abs(vol)

def write_stl(path, Vv, F):
    with open(path, 'wb') as f:
        f.write(b'NOVA mini arm shape'.ljust(80, b' ')); f.write(struct.pack('<I', len(F)))
        for t in F:
            p = Vv[t]; n = np.cross(p[1] - p[0], p[2] - p[0]); l = np.linalg.norm(n); n = n / l if l > 0 else n
            f.write(struct.pack('<12fH', *n, *p[0], *p[1], *p[2], 0))

out = sys.argv[1]
for vid, nm in (("0", "0_sucasna"), ("A", "A_mierne_stihlejsia"), ("B", "B_stihla")):
    for half, hn in (("vonk", "vonkajsi_kryt"), ("vnut", "vnutorna_cast")):
        R, c0, c1 = V.half_rows(vid, half, nu=160, nth=120)
        Vl, F = tri_rows(R, c0, c1)
        for side, sn in ((1, "lava"), (-1, "prava")):
            Vw = np.asarray(V.to_world(Vl, vid, dx=-1.0, sx=side), float)
            FF, vol = orient(Vw, F)
            write_stl(f"{out}/ruka_{nm}_{sn}_{hn}.stl", Vw, FF)
        print(vid, half, "verts", len(Vl), "tris", len(F), "vol mm3", round(vol, 1), "x range", Vw[:,0].min().round(2), Vw[:,0].max().round(2))
