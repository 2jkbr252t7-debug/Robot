"""interface description of the pan stage for the FE harness (what touches what, in which direction, one- or two-sided).
DESIGNS["rev2"] reproduces sachta_a/fe_cases_v4.py (validation on the rev. 2 STL in rev3_backup/stl).
The current design is read from design.json (written by t4_pan.py at export: t4_pan.fe_design()); when it is missing the
rev. 2 description is used.  All numbers in the stage frame, mm.

keys
  faces   : contact regions on the plane y = 15.1 (pocket plate on the well): dict(name, kind 'both' (clamped by an F10 screw) |
            'neg' (compression only), shape ('circle', cx, cz, r_out, r_in) | ('box', x0, x1, z0, z1), minus=[shapes])
  tongues : list of dict(name, x=(x0, x1), y=(y0, y1), z_up=face the tongue bears on when the module is pulled UP,
            z_lo=face when pushed DOWN)  (z contact, compression only), optional x_ends=(x0, x1) = end faces (x contact)
  dowel   : dict(c=(x, z), r, y=(y0, y1))   pin in a hole: x and z, bilateral
  lug     : dict(cw=az, ccw=az, r=(r0, r1), z=(z0, z1), pin_r)  stop pin = line contact at pin_r, compression only
  axial   : dict(kind='gear_top', r_max)  retention washer on the gear top face  |  dict(kind='well_lip', z, r=(r0, r1))
  lands   : PTFE guide lands (see cases.land_nodes)
  hub     : dict(r=(r0, r1), z_top)  foot landing ring
"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))

REV2 = dict(
    name="rev2",
    faces=[dict(name="padA_y", kind="both", shape=("circle", 7.0, -15.8, 3.65, 2.05)),
           dict(name="padB_y", kind="both", shape=("stadium", 18.4, -38.0, -34.0, 3.25), plus=[("circle", 18.0, -33.3, 3.65, 0.0)],
                minus=[("circle", 18.0, -33.3, 2.05, 0.0), ("circle", 18.4, -38.0, 1.025, 0.0)]),
           dict(name="rail_y", kind="neg", shape=("box", -6.0, 16.0, -41.9, -40.2), plus=[("box", -6.0, 16.0, -35.6, -33.9)],
                minus=[("stadium", 18.4, -38.0, -34.0, 3.25), ("circle", 18.0, -33.3, 3.65, 0.0)])],
    tongues=[dict(name="tongue", x=(-4.3, 14.3), y=(13.4, 15.2), z_up=-36.4, z_lo=-39.4)],
    dowel=dict(c=(18.4, -38.0), r=1.45, y=(11.9, 17.3)),
    lug=dict(cw=118.3, ccw=131.7, r=(27.8, 31.6), z=(-47.3, -44.6), pin_r=30.0),
    axial=dict(kind="gear_top", r_max=4.7),
    lands=dict(front=[(13.0, 17.0), (-17.0, -13.0)], back=[(10.0, 15.0)], back_up=dict(x=(-17.0, -13.0), z_min=-10.2),
               endm=[(4.9, 8.4), (-8.4, -4.9)], endp=[(4.9, 8.4)], yi=11.0, xi=23.5, h=0.70),
    hub=dict(r=(6.6, 12.5), z_top=-40.65),
    keyhole=dict(c=(23.2, -24.2), r=(5.6, 6.6), x=(-8.6, -6.4), lobe=(23.2, -29.8)),
    tab=dict(c=(23.2, -15.85), r=2.6, x=(-4.2, -2.4)),
    pin=dict(x=-18.65, y=23.2, z0=-34.2, rc=10.0),
)
DESIGNS = {"rev2": REV2}


def load(name=None):
    """name 'rev2' | 'current' (design.json) | None = 'current' when design.json exists, else 'rev2'"""
    f = os.path.join(HERE, "design.json")
    if name and name.endswith(".json"):
        f = name
    elif name == "rev2" or (name is None and not os.path.exists(f)):
        return REV2
    d = json.load(open(f))
    out = dict(REV2); out.update(d)
    return out
