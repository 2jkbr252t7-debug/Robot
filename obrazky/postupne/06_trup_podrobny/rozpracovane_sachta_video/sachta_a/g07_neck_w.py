import numpy as np, sa_lib as L
N = np.concatenate([L.part("krk_predna_polovica"), L.part("krk_zadna_polovica")])
for z in np.arange(-37.0, 6.6, 0.5):
    s = L.slice_segments(N, 2, z).reshape(-1, 3)
    if len(s) == 0: continue
    print(round(z, 1), "x", round(s[:, 0].min(), 2), round(s[:, 0].max(), 2), "y", round(s[:, 1].min(), 2), round(s[:, 1].max(), 2))
