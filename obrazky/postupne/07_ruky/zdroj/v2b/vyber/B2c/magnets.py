"""B2: axial force of small axially magnetised NdFeB discs (surface-charge model, numerical quadrature).
 magnet -> magnet (coaxial, attracting, gap g)  and  magnet -> thick soft-steel plate (image method: = magnet pair at gap 2 g;
 a thin DIN 125 washer saturates partly -> factor k_sat 0.6..0.9 reported as a band).
Also the lateral offset case (magnet pair misaligned by s) for the detent/drag estimate.
writes magnets.json"""
import math, json, os
import numpy as np

MU0 = 4e-7 * math.pi


def face_pts(R, nr=24, nt=48):
    # equal-area rings
    r_edges = R * np.sqrt(np.linspace(0, 1, nr + 1))
    rc = 0.5 * (r_edges[:-1] + r_edges[1:])
    dA_ring = math.pi * (r_edges[1:] ** 2 - r_edges[:-1] ** 2) / nt
    th = (np.arange(nt) + 0.5) * 2 * math.pi / nt
    RR, TT = np.meshgrid(rc, th, indexing="ij")
    P = np.c_[(RR * np.cos(TT)).ravel(), (RR * np.sin(TT)).ravel()]
    A = np.repeat(dA_ring, nt)
    return P, A


def pair_force(R1, t1, R2, t2, gap, Br1=1.18, Br2=1.18, s=0.0):
    """axial force (N, attraction positive) between magnet 1 (z in [-t1, 0]) and magnet 2 (z in [gap, gap + t2]),
    both magnetised +z, magnet 2 offset laterally by s (mm).  dimensions in mm."""
    M1, M2 = Br1 / MU0, Br2 / MU0
    P1, A1 = face_pts(R1); P2, A2 = face_pts(R2)
    P2 = P2 + np.array([s, 0.0])
    faces1 = [(0.0, +M1), (-t1, -M1)]
    faces2 = [(gap + t2, +M2), (gap, -M2)]
    Fz = 0.0
    for z1, s1 in faces1:
        for z2, s2 in faces2:
            dx = (P2[:, None, 0] - P1[None, :, 0]) * 1e-3
            dy = (P2[:, None, 1] - P1[None, :, 1]) * 1e-3
            dz = (z2 - z1) * 1e-3
            d3 = (dx * dx + dy * dy + dz * dz) ** 1.5
            q = (s1 * A1[None, :] * 1e-6) * (s2 * A2[:, None] * 1e-6)
            Fz += np.sum(MU0 / (4 * math.pi) * q * dz / d3)
    return -Fz          # force on magnet 2 along +z; attraction = negative z -> return positive


if __name__ == "__main__":
    out = {}
    # sanity: 2 x (D10 x 5) N42-ish pair at contact ~ published  (supermagnete S-10-05 pair ~ 2x single 'adhesive force')
    for (D, t, Br, lab) in ((4.0, 2.0, 1.18, "D4x2 N35"), (5.0, 2.0, 1.22, "D5x2 N38"), (3.0, 2.0, 1.18, "D3x2 N35")):
        rows = []
        for g in (0.05, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5):
            Fmm = pair_force(D / 2, t, D / 2, t, g, Br, Br)
            Fst = pair_force(D / 2, t, D / 2, t, 2 * g, Br, Br)      # thick steel plate at gap g
            rows.append(dict(gap=g, magnet_magnet_N=round(Fmm, 3), magnet_thick_steel_N=round(Fst, 3)))
        out[lab] = rows
        print(lab)
        for r in rows:
            print("   gap %.2f  mag-mag %.3f N   mag-steel(thick) %.3f N" % (r["gap"], r["magnet_magnet_N"], r["magnet_thick_steel_N"]))
    # check vs a published number: supermagnete S-04-02-N (D4x2 N45, Br~1.33): 'adhesive force approx. 330 g' on thick steel
    F = pair_force(2.0, 2.0, 2.0, 2.0, 0.0001, 1.33, 1.33)
    print("D4x2 N45 on thick steel at contact (model): %.2f N  (supermagnete S-04-02-N lists ~3.2 N = 330 g, unverified)" % F)
    out["check_D4x2_N45_contact_N"] = round(F, 3)
    # lateral misalignment (drag / detent) for D4x2 pair at 0.6 gap
    out["D4x2_N35_pair_gap0.6_offset"] = [dict(s=s, F=round(pair_force(2, 2, 2, 2, 0.6, 1.18, 1.18, s), 3)) for s in (0, 1, 2, 3, 4, 6)]
    print(out["D4x2_N35_pair_gap0.6_offset"])
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "magnets.json"), "w"), indent=1)
