"""own binary/ascii STL reader + uniform surface sampler (numpy only)"""
import struct
import numpy as np


def load_stl(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        V = []
        for line in data.decode("ascii", "ignore").splitlines():
            s = line.split()
            if s and s[0] == "vertex":
                V.append([float(v) for v in s[1:4]])
        return np.array(V, float).reshape(-1, 3, 3)
    n = struct.unpack("<I", data[80:84])[0]
    a = np.frombuffer(data, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)
    return a["v"].astype(float)


def sample(T, h=0.15, seed=0):
    """points on the triangles with spacing ~h (regular barycentric grid per triangle + the vertices/edges)"""
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    e = np.maximum(np.linalg.norm(B - A, axis=1), np.maximum(np.linalg.norm(C - B, axis=1), np.linalg.norm(A - C, axis=1)))
    k = np.maximum(1, np.ceil(e / h).astype(int))
    out = []
    for kk in np.unique(k):
        m = k == kk
        i, j = np.meshgrid(np.arange(kk + 1), np.arange(kk + 1), indexing="ij")
        ok = (i + j) <= kk
        a_ = (i[ok] / kk)[None, :, None]; b_ = (j[ok] / kk)[None, :, None]
        P = A[m][:, None, :] + a_ * (B[m] - A[m])[:, None, :] + b_ * (C[m] - A[m])[:, None, :]
        out.append(P.reshape(-1, 3))
    return np.unique(np.round(np.concatenate(out), 4), axis=0)
