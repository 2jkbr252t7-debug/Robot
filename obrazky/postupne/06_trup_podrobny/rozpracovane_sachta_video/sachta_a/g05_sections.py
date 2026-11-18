"""raster sections of P_sachta + gear + T_cap + washer + F15 + T_most (quick-look PNGs, 0.025 px) and measurements of
the wall-floor junctions in the section x = 0 and in the radial section through the corners"""
import json, math, sys, numpy as np
from PIL import Image
import sa_lib as L
parts = {"P_sachta": (40, 40, 40), "koleso_pan": (200, 160, 40), "T_cap": (120, 200, 120), "pd_F15": (90, 90, 200),
         "skr_F15": (60, 60, 160), "T_most": (160, 160, 200), "ptfe_podlozka": (230, 230, 230), "P_drziak_serva": (150, 60, 60),
         "L_pata": (150, 150, 150), "T_paluba": (200, 150, 200), "ptfe_cap": (235, 235, 235)}
def rot_tris(T, az):
    """rotate about Z by -az so that the plane at azimuth az becomes the x-z plane (y = 0)"""
    a = math.radians(-az); c, s = math.cos(a), math.sin(a)
    T2 = T.copy(); T2[:, :, 0] = c * T[:, :, 0] - s * T[:, :, 1]; T2[:, :, 1] = s * T[:, :, 0] + c * T[:, :, 1]
    return T2
def section(name_png, axis, value, u_rng, v_rng, h=0.025, az=None, scale=1):
    imgs = None
    for n, col in parts.items():
        T = L.part(n)
        if az is not None:
            T = rot_tris(T, az)
        us, vs, M = L.raster_slice(T, axis, value, u_rng, v_rng, h)
        if imgs is None:
            imgs = np.full(M.shape + (3,), 255, np.uint8)
        imgs[M] = col
    im = Image.fromarray(np.transpose(imgs, (1, 0, 2))[::-1])
    im.save(name_png)
    return us, vs
# section x = 0: plane axis 0 -> (u, v) = (y, z)
section("g05_sec_x0.png", 0, 0.0, (-27, 27), (-49, -30))
# radial section through the corner (21, 8.5): az 22.04 -> rotate so it is the x-z plane, then axis 1 (y=0): (u, v) = (z, x)
az = math.degrees(math.atan2(8.5, 21.0))
section("g05_sec_corner.png", 1, 0.0, (-49, -0.0), (-27, 27), az=az)
print("corner az", az)
