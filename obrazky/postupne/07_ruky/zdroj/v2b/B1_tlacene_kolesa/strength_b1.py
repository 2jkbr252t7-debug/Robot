"""B1 hand strength checks of the drive parts (printed Elegoo Tough, allowable 8.5 MPa long-term; 6 MPa used as the target for
cyclic tooth loads; short-term rare overloads compared with UTS ~29-32 MPa).  Torques are ARM torques (N.m); the pinion side
sees T/1.5.  Load levels:  need 0.004 (gravity, arm horizontal)  run 0.008 (gravity + acceleration)  slip 0.012..0.016 (clutch
window after calibration)  slipmax 0.0165 (coin-test upper bound 0.0160 + arm-weight uncertainty).  Writes strength_b1.json"""
import json, math
import gears as G

R = json.load(open("gear_chosen.json"))
gear = R["chosen"]
LV = dict(need=0.004, run=0.008, slip_lo=0.0136, slip_hi=0.0160, slipmax=0.0165)
out = {"levels": LV, "rows": []}


def row(part, case, value, unit, limit, note=""):
    ok = value <= limit
    out["rows"].append(dict(part=part, case=case, value=round(value, 3), unit=unit, limit=limit, ok=ok, note=note))
    print(f"{part:34s} {case:12s} {value:9.3f} {unit:5s} (limit {limit}) {'OK' if ok else '!!'}  {note}")


# 1 gear teeth (Lewis on the generated tooth, bevel mean section) + Kf
for k, T in LV.items():
    s = G.sigma(gear, T)
    lim = 6.0 if k in ("need", "run") else 8.5
    row("pinion 12T root (Lewis)", k, s["pin"], "MPa", lim)
    row("pinion 12T root (Lewis x Kf)", k, s["pin_Kf"], "MPa", lim if k in ("need", "run") else 8.5,
        "Kf 1.40 (AGMA 908, fillet 0.24)")
    row("gear 18T root (Lewis x Kf)", k, s["gear_Kf"], "MPa", lim)
# Hertz contact at the pitch point of the virtual pair (information: resin contact allowable unknown)
E, nu = 2000.0, 0.35
a = math.radians(25.0)
rho1 = gear["m_mean"] * gear["zv1"] / 2 * math.sin(a); rho2 = gear["m_mean"] * gear["zv2"] / 2 * math.sin(a)
for k in ("run", "slip_hi"):
    Ft = LV[k] * 1000 / gear["rm2"]
    sH = math.sqrt(Ft * (1 / rho1 + 1 / rho2) / (math.pi * gear["b"] * math.cos(a) * 2 * (1 - nu ** 2) / E))
    row("tooth contact (Hertz, E 2 GPa)", k, sH, "MPa", 40.0, "polymer-gear range 20-60 (POM); no resin data")
# 2 pinion D-key (D2.5, flat at 0.95 from the axis, 2.9 long) and vertical shaft torsion
Tp = LV["slipmax"] / 1.5 * 1000          # N.mm at the pinion
F_flat = Tp / (0.75 * 1.25)
w_flat = 2 * math.sqrt(1.25 ** 2 - 0.95 ** 2)
row("pinion D-key bearing", "slipmax", F_flat / (w_flat * 2.9), "MPa", 8.5)
row("vertical shaft D2.5 torsion", "slipmax", 1.25 * 16 * Tp / (math.pi * 2.5 ** 3), "MPa", 8.5, "x1.25 for the D-flat")
row("vertical shaft D3 torsion", "slipmax", 16 * Tp / (math.pi * 3.0 ** 3), "MPa", 8.5)
# radial/axial mesh forces on the pinion -> shaft bending between MR63 (z -25.1) and the coupler (z -37.9)
Ft = LV["slipmax"] * 1000 / gear["rm2"]
Fr_p = Ft * math.tan(a) * math.cos(math.radians(33.69)); Fa_p = Ft * math.tan(a) * math.sin(math.radians(33.69))
M_over = math.hypot(Ft, Fr_p) * 2.3 + Fa_p * 3.0     # overhang of the mean section above the MR63 centre, axial-force lever
row("vertical shaft bending at MR63", "slipmax", 32 * M_over / (math.pi * 3.0 ** 3), "MPa", 8.5, f"M {M_over:.1f} N.mm")
# 3 coupler: hex 4 AF key, horn in the printed cup (2 filed flats AF 6.2) + 2K epoxy
row("coupler hex 4AF bearing", "slipmax", Tp / (3 * 1.6) / (1.6 * 3.5), "MPa", 8.5, "3 flats carry, lever 1.6")
row("horn flats in the cup (bearing)", "slipmax", Tp / (2 * 2.6) / (3.0 * 2.0), "MPa", 8.5, "plastic horn, 2 flats")
A_bond_horn = math.pi * 7.4 * 3.5
row("horn epoxy bond (shear, torque only)", "slipmax", Tp / (3.7 * A_bond_horn), "MPa", 2.0, "epoxy-PA/PP bond weak: flats carry")
# 4 arm shaft = DIN 912 M4x20 (8.8, minor d3 3.14): torsion, mesh bending, and the tilt couple the magnet-held friction face
#   can pass when the arm is pushed sideways (M <= F_mag * r_out ; F_mag 9 N with 8 x 5x2 N38, r_out 10.5)
T = LV["slipmax"] * 1000
d3 = 3.141
row("M4 shaft torsion (steel)", "slipmax", 16 * T / (math.pi * d3 ** 3), "MPa", 300.0, "8.8: yield 640")
Fa_g = Ft * math.tan(a) * math.sin(math.radians(56.31)); Fr_g = Ft * math.tan(a) * math.cos(math.radians(56.31))
M_g = math.hypot(Ft, Fr_g) * 1.9 + Fa_g * 4.8
M_tilt = 9.0 * 10.5
row("M4 shaft bending, face tilt couple", "side push", 32 * (M_tilt + M_g) / (math.pi * d3 ** 3), "MPa", 300.0,
    f"M {M_tilt + M_g:.0f} N.mm; a printed D4 tube would see {32 * (M_tilt + M_g) / (math.pi * (4 ** 4 - 2.1 ** 4) / 4):.1f} MPa")
A_gear_bond = math.pi * 4.0 * 3.1
row("gear epoxy bond on the M4 thread", "slipmax", T / 2.0 / A_gear_bond, "MPa", 2.0, "torque only; thrust is contact")
row("MR74 inner races, Loctite 638 on thread", "radial", (M_tilt / 8.05) / (math.pi * 4.0 * 2.5), "MPa", 5.0,
    "radial force of the tilt couple over the A1-A2 span, as bond shear (conservative)")
# drive hub on the M4 head: printed hex key 3 AF (2.5 deep) + press fit on the knurled head D7 (2.6 long)
row("drive hub hex key 3AF in the head socket", "slipmax", T / (3 * 1.3) / (1.5 * 2.5), "MPa", 8.5, "3 flats carry")
row("drive hub pocket on the head (tilt couple)", "side push", M_tilt / (7.0 * 4.0 * 4.0 / 6), "MPa", 8.5,
    "couple as edge pressure on the pocket bore (D7 x 4.0 = full head length, linear distribution)")
# press fit of the printed pocket on the knurled M4 head: thin ring D9.0/D7.0, diametral interference 0.03..0.08
for di in (0.03, 0.05, 0.08):
    p_c = 2000 * di / (2 * 7.0) * (1 - (7.0 / 9.0) ** 2)
    F_off = 0.3 * p_c * math.pi * 7.0 * 4.0
    out["rows"].append(dict(part="drive hub press-off force (fresh)", case=f"interference {di}", value=round(F_off, 1),
                            unit="N", limit=None, ok=None, note="relaxes to ~30-50 % over months (resin, estimate)"))
    print(f"drive hub press-off force (fresh)  interf {di}: {F_off:.0f} N  (long-term ~{0.3 * F_off:.0f}-{0.5 * F_off:.0f} N)")
for case, Fpull in (("lift robot", 11.0), ("yank 30 N", 30.0)):
    row("arm pull vs long-term press fit", case, Fpull, "N", 15.0, "magnets 6-9 N + press fit; above that the arm pops off (breakaway)")
# 6 clutch face pressure and homing stop
row("clutch face pressure", "8 magnets", 12.3 / (math.pi * (10.5 ** 2 - 5.5 ** 2)), "MPa", 1.0)
A_stop = 1.1 * 2.0; r_stop = 6.05
for case, Tarm in (("homing slip", LV["slipmax"]), ("push 3 N tip", 3 * 0.072), ("push 10 N tip", 0.72)):
    row("homing stop contact (rib/lug)", case, Tarm * 1000 / r_stop / A_stop, "MPa", 20.0 if "push" in case else 8.5,
        "short-term bearing ~20 MPa assumed for pushes")
row("homing lug root shear", "push 3 N tip", 3 * 0.072 * 1000 / r_stop / (4.5 * 2.5), "MPa", 8.5)
# 7 plug ring / seat under L5 (0.72 N.m couple from the arm)
Z_seat = math.pi * (10 ** 4 - 5.0 ** 4) / (32 * 10)
row("plug seat D10/D5.0 (x 55.1..55.5)", "L5 0.72Nm", 720 / Z_seat, "MPa", 8.5, "Kt~1.2 at the A2 end -> x1.2 = %.1f" % (1.2 * 720 / Z_seat))
Z_ring = math.pi * (13 ** 4 - 7 ** 4) / (32 * 13)
row("plug ring D13/D7 root", "L5 0.72Nm", 1.3 * 720 / Z_ring, "MPa", 8.5, "Kt 1.3")
# 8 column (column_b1.json)
C = json.load(open("column_b1.json"))
for r in C["cases"]:
    if r["steel"].startswith("B1") or (r["z"] >= -33 and r["steel"] == "resin only"):
        row(f"column z {r['z']} ({r['where'][:18]})", "L5", r["sigma_resin_MPa"], "MPa", 8.5, r["steel"])
json.dump(out, open("strength_b1.json", "w"), indent=1)
