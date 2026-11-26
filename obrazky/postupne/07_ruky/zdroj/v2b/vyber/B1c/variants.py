"""variants for the judge's re-check"""
import copy
import geo as G


def get(var):
    p = copy.deepcopy(G.K3)
    if var == "K3":
        return p, None
    if var == "K3f":            # judge fix: 1.0 x 45 deg chamfer on the outboard corners of both servo ears
        p["servo"]["ear_ch"] = 1.0
        return p, None
    if var == "K3h":            # servo 25.25 tall (maker height incl. shaft taken as case) - bottom 3.75 lower
        p["servo"]["ear_ch"] = 1.0
        p["servo"]["H"] = 25.25
        return p, None
    raise KeyError(var)


def legs(p):
    """judge's column sketch (LEFT): two legs outside the ear tips, ear shelves, strut to the boss (STAT_ parts)"""
    B = G.box
    return {
        "STAT_leg_back": np.concatenate([B(34.4, 43.5, 13.8, 19.5, -82.0, -30.0, 0.3), B(31.5, 34.4, 13.8, 19.5, -82.0, -48.0, 0.3)]),
        "STAT_leg_front": np.concatenate([B(34.4, 43.0, -24.0, -19.2, -82.0, -44.5, 0.3), B(33.0, 34.4, -24.0, -19.2, -82.0, -48.0, 0.3)]),
        "STAT_shelf_back": B(34.4, 43.5, 9.2, 13.8, -54.3, -51.8, 0.25),
        "STAT_shelf_front": B(34.4, 43.0, -19.2, -14.6, -54.3, -51.8, 0.25),
        "STAT_strut": B(34.4, 38.4, -19.2, -9.0, -44.5, -25.0, 0.3),
    }


import numpy as np  # noqa: E402
_get = get


def get(var):  # noqa: F811
    if var == "K3x":
        p, _ = _get("K3f")
        return p, legs
    return _get(var)


def screws(p):
    """deck screw heads (ISO 7380 M2.5 + DIN 125 washer, z -46.2..-44.3) at the T4 and the K3 relocated positions + insert below"""
    return {"SCR_F3a2_T4": G.tube("z", 30.6, 4.0, 0, 2.35, -46.2, -44.3, 0.2),
            "SCR_F3a2_K3": G.tube("z", 23.0, 11.5, 0, 2.35, -46.2, -44.3, 0.2),
            "INS_F3a2_K3": G.tube("z", 23.0, 11.5, 0, 1.75, -52.2, -48.2, 0.2)}


_get2 = get


def get(var):  # noqa: F811
    if var == "SCR":
        p, _ = _get2("K3f")
        return p, screws
    return _get2(var)


def pocket(p):
    """JUDGE column (LEFT): earless servo in a pocket - back leg + front leg (continuous floor -> boss), inboard web below the
    deck, strut from the front leg over the servo to the boss, floor pad; 2 x D3 steel rods in the legs"""
    B = G.box
    return {
        "STAT_leg_back": np.concatenate([B(34.4, 41.5, 9.2, 15.5, -72.0, -26.0, 0.3), B(31.5, 34.4, 9.2, 15.5, -72.0, -48.5, 0.3)]),
        "STAT_leg_front": np.concatenate([B(34.4, 41.5, -20.0, -14.6, -72.0, -44.5, 0.3), B(32.7, 34.4, -20.0, -14.6, -72.0, -48.5, 0.3)]),
        "STAT_web": B(30.5, 32.65, -14.6, 9.2, -72.0, -48.5, 0.3),
        "STAT_strut": B(34.4, 38.4, -20.0, -9.0, -44.5, -25.0, 0.3),
        "STAT_pad": B(32.65, 44.0, -14.6, 9.2, -69.0, -66.8, 0.3),
    }


_get3 = get


def get(var):  # noqa: F811
    if var == "K3j":
        p, _ = _get3("K3f")
        p["servo"]["ear_span"] = p["servo"]["L"]        # ears cut off
        p["servo"]["ear_ch"] = 0.0
        return p, pocket
    return _get3(var)


def screws2(p):
    out = {}
    for x, y in ((29.5, 4.0), (29.5, -1.0), (29.0, 6.0)):
        out[f"SCR_{x}_{y}"] = G.tube("z", x, y, 0, 2.35, -46.2, -44.3, 0.2)
        out[f"WSH_{x}_{y}"] = G.tube("z", x, y, 0, 3.0, -46.2, -45.7, 0.2)
    return out


_get4 = get


def get(var):  # noqa: F811
    if var == "SCR2":
        p, _ = _get4("K3j")
        return p, screws2
    return _get4(var)


# ------------------------------------------------------------------ B1 (printed gears, screws as shafts, common bearings)
import geo_b1  # noqa: E402


def b1_extra(p):
    d = pocket(p)                 # v2 judge column (earless servo pocket) unchanged
    d.update(geo_b1.parts_b1())   # overrides ROT_V_coupler / shaft / pinion, ROT_A_gear / shaft, BRG_A1 / A2 ; adds shims
    return d


_get5 = get


def get(var):  # noqa: F811
    if var == "B1":
        p, _ = _get5("K3j")       # earless servo, K3j params (B1 MR63, tongue, boss unchanged)
        return p, b1_extra
    return _get5(var)
