"""rewrites the two generated sections of STATUS_obal.md (check results, printed parts) from checks_obal.json / parts_obal.json"""
import json
T4 = "/tmp/claude-0/gapwf/fin/T4"
d = json.load(open(T4 + "/checks_obal.json")); p = json.load(open(T4 + "/parts_obal.json"))
m2 = d["M2_wall"]; m3 = d["M3_exterior"]; o2 = d["O2_interference"]; o3 = d["O3_zones"]; s1 = d["S1_seam_backing"]; x1 = d["X1_vs_ram"]; f1 = d["F1_fits_measured"]
x2 = d["X2_lowering_vs_ram_meshes"]; x3 = d["X3_cap_slide_vs_meshes"]
S = {s["feature"]: s for s in d["O4_seats"]["seats"]}


def sm(key, k):
    for f, s in S.items():
        if f.startswith(key):
            return s["measured"][k]


def st(ok):
    return "PASS" if ok else "FAIL"


rows = [
    ("O1 / M1 solids", f"{p['n_parts']} parts: all valid single solids, volume > 0, bounding boxes as expected, all STL watertight (0 open / "
                       f"non-manifold / flipped edges)", st(d["summary"]["O1"] and d["summary"]["M1"])),
    ("O2 interference", f"{o2['pairs_tested']} bbox-overlapping pairs, BVH overlap + parity sampling: {len(o2['not_intended'])} unintended; intended: "
                        f"{sum(1 for t in o2['touching'] if t['intended'])} thread-forming screws in their pilots (3.3–3.8 mm³ each)", st(o2["all_ok"])),
    ("O3 zones", f"static vs RAM envelopes: min {o3['static_min_not_declared']} (not declared); pan −85…85 × lift 0…20 vs PAN / LIFT envelopes: min "
                 f"{o3['pan_min']}; lowering of T_stred over the tower envelopes: min {o3['lowering_min']} (= TOWER_CLEAR); PAN_ENV + 1.0: "
                 f"{len(o3['pan_env_exceptions'])} formal exception(s) ({', '.join(e['part'] for e in o3['pan_env_exceptions'])}), ≥ 1.0 by the direct sweep",
     st(o3["ok"])),
    ("O4 seats", f"{len(d['O4_seats']['seats'])} seats listed with part / seat / clearance / tolerance; measured: bore r {sm('collar ring', 'bore_r_min')}, "
                 f"speaker seat r {sm('speaker D28', 'seat_r_min')}, socket gap {sm('joint body', 'gap')}, neck gap {sm('joint neck', 'gap')}, lip relief wall "
                 f"{sm('front lip relief', 'remaining_wall_normal_approx')} normal / {sm('front lip relief', 'remaining_wall_horizontal')} horizontal",
     st(d["O4_seats"]["all_ok"])),
    ("O5 inside", "every internal part ≥ 0 from the inner surface (2 declared: LED screw tips in their boss pilots); shells ≤ 0.004 outside the exterior",
     st(d["O5_inside"]["all_ok"])),
    ("M2 walls", f"{m2['points']} through-wall rays: median {m2['median']}, 1st percentile {m2['p01']}, min {m2['min']} (LED boss pilots, declared); below 2.0 "
                 f"outside declared spots: {m2['n_below_2p0_not_declared']}; below 1.2: {m2['n_below_1p2']}; socket rim wedge min "
                 f"{m2['socket_rim_wedge']['min_beyond_0p6']} (declared, not counted)", st(m2["ok"])),
    ("M3 exterior", f"{m3['grid_points']} grid points (0.45 mm): deviation {m3['dev_min']} … {m3['dev_max']} mm, {m3['n_dev_over_0p05_outside_declared']} over "
                    f"0.05; {m3['uncovered_total']} uncovered points, all in declared gaps ({m3['uncovered_in_declared']['socket']} in the sockets); seam "
                    f"widths measured: x seams {m3['seam_widths_measured']['seam_x, width along x (16 stations)']}, door "
                    f"{m3['seam_widths_measured']['door seam sides, width along x (6 stations)']}", st(m3["ok"])),
    ("S1 seam backing", f"lines of sight inside the gap planes: see-through {s1['see_through_total']}; open to the interior only in the 2 declared zones: " +
     "; ".join(f"{k.split(' (')[0]} {v['open']}/{v['rays']} rays" for k, v in s1["declared_open"].items()), st(s1["ok"])),
    ("F1 fits measured", "; ".join(f"{k.split(' (')[0].split(':')[0]} {v['min']}" for k, v in f1.items()
                                    if k.startswith(("door hooks", "frame magnets", "door boss", "cap seam lip", "cap edge", "joint body", "joint neck",
                                                     "light guide plug", "grille plug", "speaker <-> its", "bush"))), "info"),
    ("X1 vs RAM meshes", f"{len(x1['overlaps'])} touching pairs, none with volume (contacts only); cap socket tube ↔ column rib "
                         f"{x1['ram_column_gap']['T_bok_L: T_ram beyond the stop-ring face (ribs, spigot, clip)']['min_dist']} mm", "info"),
    ("X2 lowering vs RAM meshes", f"{x2['tower_parts']} tower parts, {x2['pairs']} pairs: min plan gap {x2['min_plan_gap']} (required 0.5)",
     "info, ok" if x2["ok"] else "info, NOT ok"),
    ("X3 cap slide vs meshes", f"{x3['pairs']} pairs, {len(x3['closest'])} closer than required + 0.6", "info, ok" if x3["ok"] else "info, NOT ok"),
]
tab = "## Check results (final geometry, from checks_obal.json)\n\n| check | result | status |\n|---|---|---|\n" + \
      "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows) + "\n"
tab += "\n## Printed parts\n\n| part | material | mass g | bbox x / y / z | STEP |\n|---|---|---|---|---|\n"
for r in p["parts"]:
    if r["printed"]:
        b = r["bbox"]
        tab += f"| {r['name']} | {r['mat']} | {r['mass_g']} | {b[0]:.2f}…{b[1]:.2f} / {b[2]:.2f}…{b[3]:.2f} / {b[4]:.2f}…{b[5]:.2f} | {'yes' if r.get('step') else 'null'} |\n"
tab += f"\nPrinted mass {p['mass_printed_g']} g, bought parts of the module {p['mass_bought_g']} g.\n"
s = open(T4 + "/STATUS_obal.md").read()
a = s.index("## Check results (")
b = s.index("## Declared, not fixed (inside the OBAL module)")
open(T4 + "/STATUS_obal.md", "w").write(s[:a] + tab + "\n" + s[b:])
print(d["summary"]); print(o3["pan_env_exceptions"])
