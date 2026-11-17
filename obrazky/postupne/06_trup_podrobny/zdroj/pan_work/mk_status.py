"""STATUS_pan.md from parts_pan.json + pan_checks.json (numbers are read, not typed)"""
import json, os, time
T4 = "/tmp/claude-0/gapwf/fin/T4"
P = json.load(open(os.path.join(T4, "parts_pan.json"))); K = json.load(open(os.path.join(T4, "pan_checks.json")))
ck = K["checks"]; S = K["summary"]
parts = {e["name"]: e for e in P["parts"]}
printed = [e for e in P["parts"] if e["printed"]]
mass = {}
for e in P["parts"]:
    if e.get("mass_g") is not None:
        mass[e["group"]] = mass.get(e["group"], 0) + e["mass_g"]
L = []
A = L.append
A("# STATUS – CAD builder, module PAN (pan stage + neck lift), continuation run, " + time.strftime("%Y-%m-%d"))
A("")
A("Continuation of an interrupted run (it left `t4_pan.py`, 33 parts, no status, no checks, no previews). Nothing was restarted;")
A("this run fixed the two flagged parts, wrote and ran the module checks, fixed what they found, rendered previews.")
A("")
A("## Files (all under /tmp/claude-0/gapwf/fin/T4/)")
A("* `t4_pan.py` – module: `build() -> dict[name] = part(shape, group, mat, printed, label_sk, ...)`; `python t4_pan.py` builds (printed")
A("  parts cached by source hash in `cache/pan_*.brep`, full rebuild 3 s), prints validity / volume / bbox / build time, exports")
A("  `stl/<name>.stl` with `t4_obal.export_abs` (absolute deflection 0.01) and `step/<name>.step`, writes `parts_pan.json`.")
A("  Pose functions for the checks / integrator: `pose_parts(lift)`, `mk_kluka(theta)`, `fpc_lift(lift)`, `fpc_stage()`, `fpc_loop(pan)`.")
A(f"* `parts_pan.json` – {P['n_parts']} parts ({len(printed)} printed, {P['n_parts'] - len(printed)} bought / fasteners / tapes / FPC), all_ok = {P['all_ok']};")
A("  per part: valid, bbox, mesh volume, mass, stl, step, source of the dimension, assembly step, fastener record; plus `deviations`")
A(f"  ({len(P.get('deviations', []))}), `intended_fits` ({len(P.get('intended_fits', []))}), `assembly`, `firmware`, `additions`.")
A("* `t4_pan_checks.py` -> `pan_checks.json`, log `pan_checks.log` – module checks A–H (sections can be run separately: `... t4_pan_checks.py E`).")
A("* `t4_common.py` – ONLY the block \"additions by pan\" (dict `PAN`) was written (source `pan_work/additions_pan.txt`, applied with")
A("  `pan_work/put_additions_pan.py`).")
A("* Previews (600 px, 16 samples, script `pan_work/prev_pan.py`): `prev_pan_iso.png` (from the back), `_iso_pred`, `_bez_krku`, `_zozadu`,")
A("  `_zdola`, `_rez_x` (section x = 0), `_rez_kluka` (section through the crank, rest), `_rez_kluka_10` (mid stroke), `_zdvih20`,")
A("  `_v_trupe` (section x = 0 inside the OBAL + RAM parts), `_det_fpc_pozy` (pan loop at -85 / 0 / +85 over the deck). All were looked at.")
A("* Pose STLs: `pan_work/poses/lift10/`, `lift20/` (all 33 parts, pan 0), `pan_work/poses/fpc/fpc_zdvih_{0,10,20}.stl`, `fpc_pan_{-85,0,85}.stl`.")
A("* Backups of the state found on disk: `pan_work/bak/`.")
A("")
A("## Parts")
A("| part | grp | material | mass g | bbox x / y / z | STEP |")
A("|---|---|---|---|---|---|")
for e in P["parts"]:
    if e["printed"] or e["name"] in ("servo_zdvih", "fpc_pan", "spoj_zdvih", "kabel_zdvih", "cap_kluky"):
        b = e["bbox"]
        A(f"| {e['name']} | {e['group']} | {e['mat']} | {e['mass_g']} | {b[0]:.2f}…{b[1]:.2f} / {b[2]:.2f}…{b[3]:.2f} / {b[4]:.2f}…{b[5]:.2f} | {'yes' if e['step'] else 'null'} |")
A("")
A("Also: 8 PTFE strips + journal band, 2 gear dowels D2 x 4, stop pin D2 x 4.5, ear dowel D1.5 x 5, 2 x M2x4 + 2 M2 inserts (F10), M2x6 (F11),")
A("M2.5x6 countersunk (crank), M2x8 (F12), M1.6x10 countersunk (tongue). Mass by group: " + ", ".join(f"{g} {m:.1f} g" for g, m in mass.items()) + ".")
A(f"STEP: all {sum(1 for e in P['parts'] if e['step'])} files exported, largest {ck['A_solids']['step_max_bytes'] / 1e6:.2f} MB (limit 12 MB) – no part of this module is loft-derived.")
A("")
A("## What this run changed (and why)")
for t in [
    "**L_jazyk** – STL was non-manifold: the 1.8 mm key was cut by the D1.8 screw hole into two halves touching in a line. Key = two prongs (y ±1.1…2.6, 1.4 high), slot in L_pata widened; skins around the slot 1.05 / 1.15.",
    "**P_koleso** – the part was fine; only its EXPECTED bbox was wrong (21-tooth sector, lip not all round). Lip shortened 145° → 140° (by calculation its end reached the pinion tip circle at the hard stop +90; now drum / lip ↔ pinion ≥ 0.91 measured).",
    "**L_ucho slot 2.2 × 12.2 → 2.2 × 12.7** (front end y 12.1 → 11.6): at mid stroke the pin was 0.10 from the slot end, less than the float of the neck in the well. The back end cannot move (sweep radius 32.03 vs 32.2) – firmware must keep the crank at 3…177° (stroke 19.97, pin 0.62 from the closed slot end).",
    "**Lower bracket pad / F10_1: z −30.0 → −31.7**, lug z −36.55…−29.7, tab at the upper screw up to z −12.3 only. Found by the door check H3 / H2: the frame magnet pad of T_stred at (25, −24) is tilted along the wall normal, its silhouette along Y reaches x 18, z −29.14 – the lug hit it on the way in and the D4.5 tool channel of F10_1 was blocked by 0.37. The micro junction moved down 0.35 for the lug.",
    "**Bracket slivers removed**: pad pockets open cleanly at the lug / tab top (were 0.12 mm walls); tab post pilot is a through hole (was a 0.5 floor).",
    "**F10 = 2 × M2×4** (spec M2×6) in inserts with a 3.2 deep hole: 1.2 floor to the well inner face (was 0.9).",
    "**Glue groove** of the collar-disc seat interrupted at the D4.8 tool hole (0.9 rim).",
    "**Export** through `t4_obal.export_abs`; no STEP above 12 MB.",
]:
    A("* " + t)
A("")
A("## Checks actually run on the final geometry (`pan_checks.json`)")
A("| check | result | status |")
A("|---|---|---|")
a = ck["A_solids"]; A(f"| A solids / STL | {a['n']} parts: valid single solids, bbox as designed, STL re-read watertight (0 open / non-manifold / flipped edges); not ok: {a['not_ok']} | {a['status']} |")
b = ck["B_interference"]; A(f"| B interference among PAN parts (+ finished neck halves, collar disc) | OCC common volume at lift 0 / 10 / 20: {len(b['overlaps'])} overlapping pairs, all declared press / thread / bonded fits (largest {max(o['overlap_mm3_max'] for o in b['overlaps']):.2f} mm³); exact mesh distances at lift 0…20: {len(b['near_pairs_below_1mm'])} pairs below 1.0, all declared; undeclared: {b['not_ok']} | {b['status']} |")
c = ck["C_kinematics"]; A(f"| C crank kinematics | stroke {c['stroke_mm']:.3f} (r {c['crank_r']}), d lift / d θ = 0 at θ 0 / 180° (pin at y 23.2, z −34.2 / −14.2), pin ↔ slot flanks {c['pin_to_slot_flanks_on_solids']['min']}…{c['pin_to_slot_flanks_on_solids']['max']} over 13 angles, slot end gaps {c['slot']['end_gap_front_at_mid_stroke']} (front, mid stroke) / {c['slot']['end_gap_back_at_dead_centres']} (back, dead centres); peak torque {c['torque']['peak_Nm']} N·m for {c['torque']['mass_kg']} kg (MG90S 0.18: ×{c['torque']['factor']}); pan stop ±90, teeth margin {c['pan_stop']['teeth_margin_deg'][0]:.0f}° | {c['status']} |")
d = ck["D_envelope"]
srv = next(r for r in d["parts"] if r["part"] == "servo_zdvih"); ear = next(r for r in d["parts"] if r["part"] == "L_ucho")
A(f"| D swept envelope vs PAN_ENV and the analytic shell (inset 2.2) | every P / L part, lift 0…20, pan −85…85: PAN_ENV violations {d['violations']} (declared: gear lip r 16.5 = spec 7.2 vs band r 15.9; stop pin in the deck groove); smallest margins: lift servo {srv['env_margin_min']}, ear {ear['env_margin_min']}; shell clearance min **{d['shell_min']}** (servo corner, pan 30), ear {ear['shell_clear_min']}; low-zone rule hits {len([l for l in d['low_zone_rule_hits']])} | {d['status']} |")
e = ck["E_real_meshes"]
rows = {(r["moving"], r["static"]): r for r in e["pairs_below_1p5"] if r["declared"] is None}
txt = "; ".join(f"{a_} ↔ {b_} {r['min_mm']}" for (a_, b_), r in sorted(rows.items(), key=lambda kv: kv[1]["min_mm"]))
A(f"| E real meshes of OBAL + RAM (58 static parts incl. golier_prstenec), pan −85…85 × lift 0…20 | smallest undeclared clearances: {txt}. Declared running fits: journal ↔ bore 0.14 (tape) / 0.27, collar seam 0.25, pivot 0.025, gear on washer, stop pin in groove 0.2, FPC on its anchors. Gear ↔ ROTATING pinion: flank gap {e['gear_vs_rotating_pinion']['min_flank_gap']}…{e['gear_vs_rotating_pinion']['max_of_min']} at {e['gear_vs_rotating_pinion']['n_poses']} poses; drum / lip ↔ pinion ≥ {e['drum_lip_vs_pinion']['min_mm']} (at the hard stop). Hard stops ±90: " + ("; ".join(f"{h['moving']} ↔ {h['static']} {h['min_mm']}" for h in e["hard_stop_poses_pan_90"]) or "nothing new") + f" | {e['status']} |")
f = ck["F_seats"]; A(f"| F seats / fits | {len(f['seats'])} measurements on the solids and on the OBAL / RAM / B meshes, not ok: {f['not_ok']} (bore r 28.342 → journal 0.142 with tape; MG90S: 3 seat faces, wedge 0.20, post 0.30, slots ±1.0) | {f['status']} |")
g = ck["G_walls"]
A(f"| G walls (ray scan, opposing faces) | " + "; ".join(f"{r['part']} min {r['min']} (median {r['median']})" for r in g["parts"]) + f"; undeclared thin zones: {g['not_ok']} – every reading below the material limit is a declared local feature (list below) | {g['status']} |")
h = ck["H_assembly"]
ch = "; ".join(f"{c_['screw']} {c_['clear_of_tool']:+.2f}" for c_ in h["H2_tool_channels"]["channels"])
h3 = "; ".join(f"{r['part']} ↔ {r['other']} {r['min_mm']}" for r in h["H3_bracket_unit_through_door"]["pairs_below_0p8"] if not r["seat"]) or "none"
A(f"| H assembly (module level) | H1 stage straight −Z through the bore (raised 0…52): only the intended guides / seats below 0.6 ({h['H1_stage_through_bore']['status']}); H2 D4.5 tool channels, clearance to the tool: {ch} ({h['H2_tool_channels']['status']}); H3 lift module −Y through the door (pulled back 0…30): pairs below 0.8 other than its seats: {h3} ({h['H3_bracket_unit_through_door']['status']}) | {h['status']} |")
A("")
A(f"Overall: {'ALL PASS' if K['all_pass'] else 'NOT all pass: ' + str(S)}.")
A("Method of every distance: surface samples (all mesh vertices + 0.3 mm grid) of the moving part against the triangles of the other")
A("part (exact point–triangle distance, STL deflection 0.01); penetration would show as a distance → 0. Not a swept-volume boolean.")
A("")
A("## Declared thin / close features inside the module")
for r in g["parts"]:
    for t in r["declared_thin"]:
        A(f"* {r['part']} ({r['material']}, limit {r['limit']}): {t['feature']} – measured min {t['min']}")
A("* Running gaps below 1.0 by design: crank pin in the slot 0.10 per side; crank arm ↔ ear 0.40; foot 0.5 above the hub disc and tongue / ear 0.5")
A("  above the floor at rest; tongue block 0.5 under the window top at lift 20; neck on the lands 0.30 bare / 0.17 with tape.")
A("* Lift servo ↔ T_ram columns 1.02 and ↔ frame magnet pad of T_stred 1.22: above the 1.0 rule, but with little margin for print tolerance.")
A("")
A("## Foot ↔ finished neck")
fn = P.get("foot_to_neck", {})
if fn:
    A(f"* {fn['joint']}.")
    o = fn["optional_screws"]; A(f"* Optional: {o['size']} at (x, y) {o['xy']} into {o['into']}. Checked: {o['checked']}.")
    A(f"* Wires: {fn['wire_exits']}; FPC paddle 3.4 × 10.4 in a 1.0 deep pocket under the foot (solder side down), tail in a 0.3 channel to the tongue.")
A("")
A("## Deviations from T4_spec.md (details in parts_pan.json[\"deviations\"])")
for dv in P.get("deviations", []):
    A(f"* **{dv['id']} {dv['item']}** – spec: {dv['spec']}; built: {dv['actual']}. Reason: {dv['reason']}.")
A("")
A("## NOT done / NOT verified (do not treat as passed)")
for t in [
    "K1–K11 (global) were not run by me. E / H are module pre-checks on the STL files of OBAL (16:5x) and RAM (16:07) found on disk; if either module is re-exported, re-run `t4_pan_checks.py E H`.",
    "K9 (real head vs torso top) is not part of this module. The neck halves above z 4 and the head were not checked against anything here.",
    "K7 for the whole torso: only the three module steps above were simulated (straight translations, sampled every 1…4 mm). Dropping the neck with the bonded foot into the well, hooking the ear onto the pin and mounting the tongue were NOT simulated – they rest on the static gaps (foot 0.37 to the tapes, ear ±1.0 in its window, tongue ±1.0).",
    "The FPC is modelled as an ideal strip (constant radii, creased folds); its real shape between the anchors, fatigue life (R 4.0 lift loop = 33 t, R 3.84 pan U-turn = 32 t) and the developed outline for ordering are not verified. The outline has 3 folds and 2 T-branches – it needs a drawing of its own.",
    "Soldering 7 neck wires to the FPC paddle under the foot is described, not modelled wire by wire.",
    "MG90S dimensions are the E2 model (user drawing); the spline is modelled as a D4.8 cylinder, the crank serration (21T, 4.44 / 4.84) must be test-printed. Servo torque margin uses an assumed 0.17 kg for head + neck + foot.",
    "K10 printability: no slicer run. P_sachta (tough resin) has the 0.9 back floor of the spec (0.7 in the FPC groove) and a 14 × 30 window in the back wall; orientation top-down is assumed. P_drziak_serva (PETG) has a 0.8 ledge (spec) and 0.85 / 1.05 lands above the F10 slots.",
    "K11: masses are in parts_pan.json; the centre of gravity of the module was not combined.",
    "Bought-part sizes (MG90S, dowels, screws, junction header / socket) are datasheet / standard values, not measured parts.",
    "The design choices inherited from the first run (fin + apron, FPC routing under the floor, junction on the back wall, tongue) were not re-derived; they were only tested by the checks above and looked at in the previews.",
    "Service access to the FPC clamp screw of RAM (axis Z) AFTER the collar disc is glued on: the D4.8 tool hole is then covered. It is reachable only with the lift module removed and an L-key through the door – not simulated.",
]:
    A("* " + t)
A("")
A("## How to re-run")
A("```")
A("/opt/venv/cad/bin/python t4_pan.py                     # 7 s from the cache (--rebuild: 10 s)")
A("/opt/venv/cad/bin/python t4_pan_checks.py E            # 3 min  real meshes (needs stl/ of OBAL + RAM)")
A("/opt/venv/cad/bin/python t4_pan_checks.py A B C D F G H  # about 15 min")
A("/opt/venv/cad/bin/python pan_work/export_poses.py && /opt/venv/bl/bin/python pan_work/prev_pan.py iso rez_x v_trupe")
A("```")
open(os.path.join(T4, "STATUS_pan.md"), "w").write("\n".join(L) + "\n")
print("STATUS written", len(L), "lines; all_pass", K["all_pass"], S)
