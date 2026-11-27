"""R4 sheet 3 pre-check: joint K3 (designed and verified on arm B0) combined with the rounding variants B1..B3.
Only the items that depend on the arm shape are re-measured; B0 is computed the same way as the reference.
  a) white arm (inner half, outside the D26.4 opening r >= 13.2) to the static K3 cover: pose independent ((x, r) distance
     to klb.cover_profile, the cover is a solid of revolution about the shoulder axis)
  b) white band around the D26.4 opening = (inner half's outline radius seen along the axis) - 13.2, per azimuth;
     reported at the front (-y), back (+y), top and bottom, and as the minimum
  c) printed black part ARM_naboj_prstenec_K3: (1) every vertex stays on the torso side of the seam (local x < seam - 0.5),
     (2) distance from its vertices that lie inside the arm to the OUTER cover surface (x >= seam)
  d) visible ring ARM_prstenec_K3 vs the arm's inner-half outline: ring outer radius 13.1 must stay inside the outline
usage: /opt/venv/cad/bin/python combo_chk.py  -> combo_chk.json"""
import sys, os, json, math, struct
sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/tvar"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
import numpy as np
from scipy.spatial import cKDTree
import variants_b as VA
import klb as KL

HERE = os.path.dirname(os.path.abspath(__file__))
YA, ZA = KL.YA, KL.ZA
DX = KL.arm_dx("K3")
HOLE_R = KL.K3["hole_r"]          # 13.2


def stl_verts(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.frombuffer(data[84:84 + 50 * n], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return np.unique(rec["v"].reshape(-1, 3).astype(float).round(5), axis=0)


def polar(P):
    dy, dz = P[:, 1] - YA, P[:, 2] - ZA
    return np.hypot(dy, dz), np.degrees(np.arctan2(dz, dy)) % 360.0     # az 0 = back (+y), 90 = top, 180 = front, 270 = bottom


cov = KL.cover_profile()
part = stl_verts(KL.stl("K3", "ARM_naboj_prstenec_K3"))
ring = stl_verts(KL.stl("K3", "ARM_prstenec_K3"))
out = {}
for vid in VA.VIDS:
    res = {}
    # inner half surface (dense), world frame
    rows, c0, c1 = VA.half_rows(vid, "vnut", 900, 400, VA.SEAM)
    P = VA.to_world(rows.reshape(-1, 3), vid, DX)
    r, az = polar(P)
    # a) white arm (outside the opening) to the cover
    m = r >= HOLE_R
    XR = np.c_[P[m, 0], r[m]]
    d = KL.poly_dist(XR, cov)
    i = int(np.argmin(d))
    res["white_arm_to_cover"] = round(float(d[i]), 3)
    res["white_arm_to_cover_at"] = dict(x=round(float(XR[i, 0]), 2), r=round(float(XR[i, 1]), 2), az=round(float(az[m][i]), 1))
    # b) band: outline radius per azimuth (1 deg bins) of the inner half, minus the hole radius
    bins = np.floor(az).astype(int) % 360
    rmax = np.full(360, np.nan)
    for b in range(360):
        s = bins == b
        if s.any():
            rmax[b] = r[s].max()
    band = rmax - HOLE_R
    res["band_min"] = round(float(np.nanmin(band)), 2); res["band_min_az"] = int(np.nanargmin(band))
    res["band_front"] = round(float(np.nanmin(band[160:201])), 2)     # around az 180 (front)
    res["band_back"] = round(float(np.nanmin(np.r_[band[340:360], band[0:21]])), 2)
    res["band_top"] = round(float(np.nanmin(band[70:111])), 2)
    res["band_bottom"] = round(float(np.nanmin(band[250:291])), 2)
    # d) visible ring (r 13.1) inside the outline
    rr, ra = polar(ring)
    res["ring_r_max"] = round(float(rr.max()), 3)
    # c) printed part: seam side + distance to the outer cover surface
    Q = VA.to_local(part, vid, DX)
    u = np.clip(-Q[:, 2] / VA.L, 0, 1)
    seam = np.asarray(VA.seam_x(vid, u), float)
    res["part_min_below_seam"] = round(float((seam - Q[:, 0]).min()), 3)
    ro, _, _ = VA.half_rows(vid, "vonk", 900, 400, VA.SEAM)
    O = ro.reshape(-1, 3)                       # local frame cover surface
    ins = VA.inside_local(vid, Q)
    dd, _ = cKDTree(O).query(Q[ins])
    res["part_inside_n"] = int(ins.sum()); res["part_to_cover_surface_min"] = round(float(dd.min()), 3)
    # the part's points outside the arm = the visible ring portion between the torso and the arm (must be the ring only)
    Pw = part[~ins]
    rq, _ = polar(Pw)
    res["part_outside_arm_x_max"] = round(float(Pw[:, 0].max()), 2) if len(Pw) else None
    out[vid] = res
    print(vid, json.dumps(res))
json.dump(out, open(os.path.join(HERE, "combo_chk.json"), "w"), indent=1)
