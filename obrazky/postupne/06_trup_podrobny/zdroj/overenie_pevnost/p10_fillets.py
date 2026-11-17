"""p10 - inside-corner radius at loaded roots (rule Z3.3), measured on the STL: a probe along the corner bisector,
started 1.0 mm out in the empty quadrant; first material hit s -> radius R = (1.0 - s) / (sqrt2 - 1) (0 = sharp)."""
import math, numpy as np, pv_lib as L
log = L.Log("p10_fillets")
rows = []
K = math.sqrt(2) - 1


def corner(name, part, c, b, note):
    """c = corner point (x, y, z), b = unit bisector pointing into the EMPTY quadrant"""
    c = np.array(c, float); b = np.array(b, float); b /= np.linalg.norm(b)
    p0 = c + 1.0 * b
    ch = L.chords(part, p0, -b, lo=0.0, hi=2.0)
    if not ch:
        log("%-55s %-15s no material hit (check the corner coordinates)" % (name, part)); rows.append(dict(corner=name, part=part, R=None, note=note)); return
    s = ch[0][0]
    R = max(0.0, (1.0 - s) / K)
    log("%-55s %-15s first material at s %.3f -> fillet R %.2f   (%s)" % (name, part, s, R, note))
    rows.append(dict(corner=name, part=part, s=round(s, 3), R=round(R, 2), ok=bool(R >= 1.0), ok_min=bool(R >= 0.5), note=note))


r2 = 1 / math.sqrt(2)
# ear: plate (x -19.9..-17.4) / flange (y 9.8..12.4, x to -7.5): corner at (x -17.4, y 12.4), along z
corner("L_ucho plate / flange root (x -17.4, y 12.4)", "L_ucho", (-17.4, 12.4, -38.0), (r2, r2, 0), "carries the L1/L2 ear moment")
corner("L_ucho plate top / flange (y 12.4, z -36.5) at x -18.65", "L_ucho", (-18.65, 12.4, -31.9 - 0.0), (0, r2, r2), "plate top edge is free - n/a")
# bracket ledge root (y 17.1, z -41.1) along x
corner("P_drziak_serva ledge root (y 17.1, z -41.1)", "P_drziak_serva", (5.0, 17.1, -41.1), (0, r2, r2), "servo support under L2")
corner("P_drziak_serva post underside root (y 17.1, z -18.0)", "P_drziak_serva", (2.5, 17.1, -18.0), (0, r2, -r2), "F11 post")
# P_sachta pad root: pad r 3 about (19.5, -31.7) axis y, wall outer face y 12.6 -> corner at (22.5, 12.6, -31.7)
corner("P_sachta lower bracket pad root (r 3.0 on the back wall)", "P_sachta", (22.5, 12.6, -31.7), (r2, r2, 0), "F10 shear + moment")
corner("P_sachta upper bracket pad root", "P_sachta", (11.0, 12.6, -14.5), (r2, r2, 0), "F10")
# crank hub / arm: tangent arcs; arm face x -14.5 meets the hub (x -14.5..-12.8, r 3.6): corner at (x -14.5, y 23.2, z -24.2-3.6)
corner("P_kluka arm face / hub step (x -14.5, r 3.6)", "P_kluka", (-14.5, 23.2, -27.8), (r2, 0, -r2), "crank torque")
# column foot: web x 34.4..36.4 above z -78, foot x 34.4..37.6 below -> corner (36.4, -78)  -- read the faces first
log("T_ram column at y 3: chords along x at z -77.0:", L.chords("T_ram", (30, 3, -77.0), (1, 0, 0)))
log("T_ram column at y 3: chords along x at z -79.0:", L.chords("T_ram", (30, 3, -79.0), (1, 0, 0)))
log("T_ram column at y -8: chords along x at z -70.0:", L.chords("T_ram", (30, -8, -70.0), (1, 0, 0)))
# column boss: boss disc x 34.4..38.4, r 11.6 about (y 3, z -17); web below it: corner where the web meets the boss underside
log("T_ram chords along z at x 35.4, y -5:", L.chords("T_ram", (35.4, -5.0, -40), (0, 0, 1)))
log("T_ram chords along z at x 39.5, y 3:", L.chords("T_ram", (39.5, 3.0, -40), (0, 0, 1)))
# T_klb neck / body step (x 40.6, r 11.0 -> 13.5): corner at (40.6, 3, -17 - 11.0) bisector (-x, -z)
corner("T_klb_L neck / body step (x 40.6, r 11.0, az 0)", "T_klb_L", (40.6, 14.0, -17.0), (-r2, r2, 0), "L5 bending, L6 knock")
corner("T_klb_L neck / body step (x 40.6, r 11.0, az 90)", "T_klb_L", (40.6, 3.0, -6.0), (-r2, 0, r2), "L5 bending, L6 knock")
corner("T_klb_L body / end step (x 50.956, r 11.4, az 0)", "T_klb_L", (50.956, 14.4, -17.0), (r2, r2, 0), "arm journal root")
# stop lug root at z -98, x +1.25, y 19.75
corner("T_spodok J1 stop lug root (x 1.25, z -98.0)", "T_spodok", (1.25, 19.75, -98.0), (r2, 0, -r2), "L4 stop force")
# door hook root: find the faces at x 16
log("T_dvere chords along y at x 16, z -11.0:", L.chords("T_dvere", (16, 20, -11.0), (0, 1, 0)))
log("T_dvere chords along y at x 16, z -13.0:", L.chords("T_dvere", (16, 20, -13.0), (0, 1, 0)))
log("T_dvere chords along y at x 16, z -16.0:", L.chords("T_dvere", (16, 20, -16.0), (0, 1, 0)))
log("T_dvere chords along z at x 16, y 31.6:", L.chords("T_dvere", (16, 31.6, -20.0), (0, 0, 1)))
log("T_dvere chords along z at x 16, y 32.4:", L.chords("T_dvere", (16, 32.4, -20.0), (0, 0, 1)))
# pan servo post root under the shelf: post shelf z -61.6..-58, cradle front wall at y -14.15..-12.55
log("T_ram chords along y at x 14, z -60:", L.chords("T_ram", (14, -40, -60.0), (0, 1, 0)))
# J1 cradle wall / floor frame (y 14.15 outer, z -80.3?) - read the faces
log("T_ram chords along z at x 0, y 13.35 (cradle wall):", L.chords("T_ram", (0, 13.35, -90), (0, 0, 1)))
log("T_ram chords along y at x 0, z -81.5:", L.chords("T_ram", (0, 0, -81.5), (0, 1, 0)))
log("T_ram chords along y at x 0, z -79.0:", L.chords("T_ram", (0, 0, -79.0), (0, 1, 0)))
corner("T_dvere hook tab / root (y 31.18, z -12.0) at x 16", "T_dvere", (16.0, 31.18, -12.0), (0, r2, r2), "door pull L7")
corner("T_dvere hook tab / root at x -16", "T_dvere", (-16.0, 31.18, -12.0), (0, r2, r2), "door pull L7")
# column boss underside meets the U-channel web: web x 34.4..36.4 at y -5; boss r 11.6 about (3, -17) -> underside at z -17-sqrt(11.6^2-8^2)
zb = -17 - math.sqrt(11.6 ** 2 - 8.0 ** 2)
log("T_ram chords along y at x 35.4, z %.2f - 0.3:" % zb, L.chords("T_ram", (35.4, -20, zb - 0.3), (0, 1, 0)))
log("T_ram chords along x at y 14.0, z -40:", L.chords("T_ram", (30, 14.0, -40), (1, 0, 0)))
log("T_ram chords along x at y -8.0, z -40:", L.chords("T_ram", (30, -8.0, -40), (1, 0, 0)))
log("T_ram chords along x at y 3.0, z -40:", L.chords("T_ram", (30, 3.0, -40), (1, 0, 0)))
corner("T_ram column rib (x 42) / boss face (x 38.4)? rib-to-web corner at (36.4, y -9 rib?)", "T_ram", (36.4, -7.4, -40.0), (r2, r2, 0), "column web / rib")
# T_stred screw boss (r 3.2 at (29, 19)), web 2.0: boss meets the shell; skip (shell surface curved)
log.rows = rows; log.save("p10_fillets")
