"""build the voxel / finite-cell model of the pan stage bottom-to-top: P_sachta (resin), koleso_pan (brass, bonded under the
hub disc + back floor: nodes merged on z -41.9 inside the measured bond map), P_drziak_serva (resin, merged with the well on
the y 15.1 contact faces of pad A, pad B and the rail lips).  Saves the occupancy cache; returns the model."""
import os, sys, time, numpy as np
import fe3d, sa_lib as L
H = 0.4
O = np.array([-26.8, -26.9, -47.5])
SHAPE = (134, 146, 114)
E_RESIN, NU_RESIN = 1600.0, 0.38          # Z2: E 1.5-1.8 GPa assumed -> 1.6
E_BRASS, NU_BRASS = 100000.0, 0.34
CACHE = "cache_occ_h%.2f.npz" % H


def occupancies():
    if os.path.exists(CACHE):
        d = np.load(CACHE)
        return {k: d[k] for k in d.files}
    t0 = time.time(); occ = {}
    for n in ("P_sachta", "koleso_pan", "P_drziak_serva"):
        occ[n] = fe3d.occupancy_w(L.part(n), O, H, SHAPE)
        print(n, "occupancy", round(time.time() - t0, 1), "s", flush=True)
    np.savez_compressed(CACHE, **occ)
    return occ


def bond_mask_fn():
    d = np.load("g02_maps.npz"); xs, ys, bond = d["xs"], d["ys"], d["bond"]
    def fn(p):
        i = np.clip(np.round((p[:, 0] - xs[0]) / (xs[1] - xs[0])).astype(int), 0, len(xs) - 1)
        j = np.clip(np.round((p[:, 1] - ys[0]) / (ys[1] - ys[0])).astype(int), 0, len(ys) - 1)
        return (np.abs(p[:, 2] + 41.9) < 1e-6) & bond[i, j]
    return fn


def pocket_face_fn(p):
    """contact faces on y = 15.1: pad A (7, -15.8) r 3.65 minus D4.1; pad B stadium (18.4, -38..-34) r 3.25 U round
    (18.0, -33.3) r 3.65 minus D4.1 and the D2.05 dowel hole; rail lips x -6..16 (lower z -41.9..-40.2, upper -35.6..-33.9)"""
    on = np.abs(p[:, 1] - 15.1) < 1e-6
    x, z = p[:, 0], p[:, 2]
    rA = np.hypot(x - 7.0, z + 15.8)
    padA = (rA <= 3.65 + 1e-6) & (rA >= 2.05 - 1e-6)
    zc = np.clip(z, -38.0, -34.0)
    rB = np.hypot(x - 18.4, z - zc); rB2 = np.hypot(x - 18.0, z + 33.3); rD = np.hypot(x - 18.4, z + 38.0)
    padB = ((rB <= 3.25 + 1e-6) | (rB2 <= 3.65 + 1e-6)) & (rB2 >= 2.05 - 1e-6) & (rD >= 1.025 - 1e-6)
    rail = (x >= -6.0 - 1e-6) & (x <= 16.0 + 1e-6) & (((z >= -41.9 - 1e-6) & (z <= -40.2 + 1e-6)) | ((z >= -35.6 - 1e-6) & (z <= -33.9 + 1e-6)))
    return on & (padA | padB | rail)


def build(assemble=True):
    occ = occupancies()
    m = fe3d.Model(O, H, SHAPE)
    t0 = time.time()
    fe3d.add_body_fcw(m, "well", occ["P_sachta"], E_RESIN, NU_RESIN)
    fe3d.add_body_fcw(m, "gear", occ["koleso_pan"], E_BRASS, NU_BRASS)
    fe3d.add_body_fcw(m, "pocket", occ["P_drziak_serva"], E_RESIN, NU_RESIN)
    del occ
    for b in m.bodies:
        print(b["name"], "cells", len(b["cells"]), "partial", len(b["part"]), "volume", round(b["frac"].sum() * H ** 3, 1))
    m.build_nodes(merges=[("well", "gear", bond_mask_fn()), ("well", "pocket", pocket_face_fn)])
    print("merged nodes", m.merged, "nodes", m.nn, round(time.time() - t0, 1), "s", flush=True)
    if assemble:
        fe3d.assemble_fc(m)
    return m


if __name__ == "__main__":
    m = build()
