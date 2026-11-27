import numpy as np, struct
def load(path):
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[80:84])[0]
    if len(data) == 84 + 50 * n:
        rec = np.frombuffer(data[84:84 + 50 * n], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        return rec["v"].astype(float)
    # ascii
    V = []
    for line in data.decode(errors="ignore").splitlines():
        s = line.strip().split()
        if s and s[0] == "vertex":
            V.append([float(t) for t in s[1:4]])
    return np.array(V).reshape(-1, 3, 3)
def sample(T, h=0.2):
    """uniform-ish surface samples of a triangle soup"""
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    ar = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
    n = np.maximum(1, np.ceil(ar / (h * h * 0.5)).astype(int))
    out = [T.reshape(-1, 3)]
    rng = np.random.default_rng(0)
    idx = np.repeat(np.arange(len(T)), n)
    u = rng.random(len(idx)); v = rng.random(len(idx))
    m = u + v > 1; u[m] = 1 - u[m]; v[m] = 1 - v[m]
    out.append(A[idx] + u[:, None] * (B[idx] - A[idx]) + v[:, None] * (C[idx] - A[idx]))
    return np.concatenate(out)
