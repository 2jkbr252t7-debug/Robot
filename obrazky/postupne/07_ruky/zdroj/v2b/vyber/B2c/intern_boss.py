"""B2 boss point model (left): solid r <= 12.8 x 34.4..38.4 + stop ring r 11.6..12.8 x 38.4..39.1, minus the pinion slot
|y-3| <= 5.1 (z >= -24.55) and the shaft slot |y-3| <= 2.5 for x >= 36.5, z -30.0..-24.55 (both open to +X)."""
import numpy as np
import geo_b2 as GB
YA, ZA = 3.0, -17.0


def boss_b2(h=0.25):
    B = GB.box(34.4, 39.1, YA - 12.8, YA + 12.8, ZA - 12.8, ZA + 12.8, h)
    r = np.hypot(B[:, 1] - YA, B[:, 2] - ZA)
    keep = ((B[:, 0] <= 38.4) & (r <= 12.8)) | ((B[:, 0] > 38.4) & (r >= 11.6) & (r <= 12.8))
    B = B[keep]
    slot1 = (np.abs(B[:, 1] - YA) <= 5.1) & (B[:, 2] >= -24.55)
    slot2 = (np.abs(B[:, 1] - YA) <= 2.5) & (B[:, 0] >= 36.5) & (B[:, 2] >= -30.0) & (B[:, 2] <= -24.55)
    return B[~(slot1 | slot2)]
