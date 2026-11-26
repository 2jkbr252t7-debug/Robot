"""Stand-in arm variants for the joint packaging study (R3/mech).
The approved T3 pebble placed by armgeo (frame B, LEFT arm at rest, dx -1.0) and thinned with armgeo's kt scaling:
the attachment point stays 5 mm inside the INNER surface, so the inner face stays put and the arm gets thinner from
the OUTSIDE (same rule the shape designer uses).  Exposes the variant-module interface that fit.py expects:

    VARIANTS                       ids
    inside_local(vid, P, inset)    analytic point-in-pebble test in the arm LOCAL frame (x thickness, outer +; y width; z down -L)
    to_world(P, vid, dx)           local -> frame B (left arm at rest)
    profile(vid, u)                (half width fore-aft, half thickness lateral) at u in [0, 1]
    thickness(vid)                 real max thickness (mm)

Ids: kt100 (current arm, 23.0), kt085 (19.6), kt070 (16.1), kt057 (13.1); any 'ktNNN' works (NNN/100)."""
import sys
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/home/user/Robot/obrazky/postupne/07_ruky/zdroj/geometria")
import armgeo as A  # noqa: E402

VARIANTS = ["kt100", "kt085", "kt070", "kt057"]


def _kt(vid):
    vid = str(vid)
    if vid.startswith("kt"):
        return float(vid[2:]) / 100.0
    return float(vid)


def inside_local(vid, P, inset=0.0):
    return A.inside_local(np.atleast_2d(P), _kt(vid), 1.0, inset)


def to_world(P, vid, dx=-1.0):
    return A.to_world(P, _kt(vid), dx)


def profile(vid, u):
    return A.prof(u, _kt(vid), 1.0)


def thickness(vid):
    us = np.linspace(0.0, 1.0, 4001)
    return float(2.0 * np.max(profile(vid, us)[1]))
