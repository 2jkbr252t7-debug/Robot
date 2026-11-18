"""hand calculations for the pivot stack under the well: F15 thread in T_most, DIN 9021 washer on the gear, T_cap (crush, creep,
root, bond), T_most, and the journal band / collar glue land.  All geometry from the STL (g02_measure.json) or spec 17.1."""
import json, math
g = json.load(open("g02_measure.json"))
out = {}
# ---------------- F15: M3 x 6 ISO 7380 into the tapped 2.0 aluminium bridge
P = 0.5; d = 3.0
Le_nom = g["F15_engagement_in_T_most"]                    # 0.80 measured (tip -47.0, bridge top -46.2)
# internal-thread stripping area per mm of engagement (FED-STD-H28 / Machinery's Handbook): A = pi n Le Ds_min [1/(2n) + 0.57735 (Ds_min - En_max)]
n = 1 / P; Ds_min = 2.874; En_max = 2.675 + 0.100            # M3 6g major min, 6H pitch max (ISO 965 tables, typical)
a_per_mm = math.pi * n * Ds_min * (1 / (2 * n) + 0.57735 * (Ds_min - En_max))
tau = {"5754-H22 (Rm 220)": 0.6 * 220, "6061-T6 (Rm 290)": 0.6 * 290}
# effective full-thread engagement: tip of ISO 7380 (rolled / chamfered end, ISO 4753): incomplete thread ~1 P..2 P; hole entry chamfer ~0.15
cases = {"nominal 0.80": Le_nom, "tip chamfer 1P + entry 0.15 -> 0.15": max(0.0, Le_nom - 1 * P - 0.15),
         "tip incomplete 0.5 P + entry 0.1 -> 0.45": Le_nom - 0.5 * P - 0.1}
pre = 0.10 / (0.2 * d * 1e-3)                              # N at the 0.10 N.m fingertip design case, K 0.2
out["F15"] = dict(engaged_nominal_mm=round(Le_nom, 3), pitches=round(Le_nom / P, 2), shear_area_per_mm=round(a_per_mm, 3), preload_0p10Nm=round(pre, 1),
                  strip_N={f"{k} / {m}": round(a_per_mm * Le * t, 0) for k, Le in cases.items() for m, t in tau.items()},
                  torque_to_strip_Nm={f"{k} / {m}": round(a_per_mm * Le * t * 0.2 * d * 1e-3, 3) for k, Le in cases.items() for m, t in tau.items()})
# proposed: M3 x 8 shortened to 7.0 (tip -48.0, 0.20 above the bridge underside -48.2, 0.30 above the STS3215 top -48.3)
Le7 = 1.8
out["F15_fix_M3x7"] = dict(engaged=Le7, strip_N_5754=round(a_per_mm * (Le7 - 0.5 * P - 0.1) * tau["5754-H22 (Rm 220)"], 0),
                           torque_to_strip_Nm_5754=round(a_per_mm * (Le7 - 0.5 * P - 0.1) * tau["5754-H22 (Rm 220)"] * 0.2 * d * 1e-3, 3))
# ---------------- DIN 9021 M3 washer (3.2 x 9.0 x 0.8) on the gear top face r 4.0 .. 4.5, L1 x 2 = 30 N
F1 = 30.0
rb = g["gear_bore_r"]; ro = g["washer_r_out"]
for ch in (0.0, 0.2, 0.3, 0.4):
    A = math.pi * (ro ** 2 - (rb + ch) ** 2)
    out.setdefault("washer_on_gear", {})[f"bore chamfer {ch}"] = dict(overlap=round(ro - rb - ch, 3), area=round(A, 2), p_MPa=round(F1 / A, 2) if A > 0 else None)
# washer bending: annular plate, load ring at r_l, held under the head r_h = 2.85 (dk 5.7): strip estimate
rl = (ro + rb) / 2; rh = 2.85; t = 0.8
q = F1 / (2 * math.pi * rl)
out["washer_bending_MPa"] = round(6 * q * (rl - rh) / t ** 2, 1)
# ---------------- T_cap (D7.70 x 4.40, hole D3.4, root flare to r 4.45), resin
Ac = math.pi * (3.85 ** 2 - 1.7 ** 2)
out["T_cap"] = dict(area_under_washer=round(Ac, 2), crush_MPa=round(pre / Ac, 2), allow_short=25.8, sustained_limit=4.3)
k_c = 1600 * Ac / 4.4; k_b = 200000 * math.pi * 1.25 ** 2 / 6.0
out["T_cap"]["k_cap_N_per_mm"] = round(k_c); out["T_cap"]["elastic_shortening_mm"] = round(pre / k_c, 4)
for cm in (0.5, 0.3):     # creep modulus as a fraction of E (assumption: no creep data for Elegoo Tough)
    eps = pre / Ac / (cm * 1600)
    out["T_cap"][f"creep_shortening_if_Ec={cm}E_mm"] = round((eps - pre / Ac / 1600) * 4.4, 4)
out["T_cap"]["note_creep_direction"] = "T_cap shortening lowers the washer onto the gear: it REDUCES the 0.10 axial play (K12 TQ F15 says 'adds')"
# root bending + bond under a radial pivot force F at the bore centre z -43.9 (lever 2.3 to the bridge top -46.2)
Z = math.pi * (7.7 ** 4 - 3.4 ** 4) / (32 * 7.7)
Ab = math.pi * (4.45 ** 2 - 1.7 ** 2); Zb = math.pi * (4.45 ** 4 - 1.7 ** 4) / (4 * 4.45)
def tcap(F):
    M = F * 2.3
    return dict(F=F, M=round(M, 1), root_nominal=round(M / Z, 2), root_Kt1p7=round(1.7 * M / Z, 2), bond_peel=round(M / Zb, 2), bond_shear=round(F / Ab, 2))
out["T_cap_root_Z"] = round(Z, 2); out["T_cap_bond_A"] = round(Ab, 2); out["T_cap_bond_Z"] = round(Zb, 2)
out["T_cap_radial"] = {k: tcap(F) for k, F in (("L8 65 N", 65.0), ("L3 44 N", 44.0))}
json.dump(out, open("h01_pivot.json", "w"), indent=1)
print(json.dumps(out, indent=1))
