import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
def sec(name, fixed, val, a_rng, b_rng, da, db, d='stl', chars=" #"):
    """ASCII section: fixed axis ('x','y','z') = val; rows = b (descending), cols = a"""
    M = part(name, d, 0.2)
    ax = {'x': (1, 2, 0), 'y': (0, 2, 1), 'z': (0, 1, 2)}[fixed]
    A = np.arange(a_rng[0], a_rng[1] + 1e-9, da); B = np.arange(b_rng[0], b_rng[1] + 1e-9, db)
    AA, BB = np.meshgrid(A, B, indexing='ij'); P = np.zeros((AA.size, 3)); P[:, ax[0]] = AA.ravel(); P[:, ax[1]] = BB.ravel(); P[:, ax[2]] = val
    I = M.inside(P).reshape(AA.shape)
    print(f"{name} [{d}] section {fixed} = {val}: cols {'xyz'[ax[0]]} {a_rng[0]}..{a_rng[1]} step {da}, rows {'xyz'[ax[1]]} {b_rng[1]} (top) .. {b_rng[0]} step {db}")
    for j in range(len(B) - 1, -1, -1):
        print(f"{B[j]:8.2f} " + "".join(chars[int(v)] for v in I[:, j]))
    return A, B, I
if __name__ == "__main__":
    # F10_A insert hole region of P_sachta: plan section at z -15.8 and at z -14.2
    sec('P_sachta', 'z', -15.8, (0.0, 8.5), (9.9, 15.3), 0.1, 0.1)
    sec('P_sachta', 'x', 4.2, (9.9, 15.3), (-19.0, -12.0), 0.1, 0.1)
    sec('P_sachta', 'z', -15.8, (0.0, 12.0), (9.9, 15.3), 0.1, 0.1, d='rev3_backup/stl')
