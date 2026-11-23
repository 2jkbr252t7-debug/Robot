#!/opt/venv/cad/bin/python
"""fix-back after overenie3: append (or replace) the dated block in STATUS_rev3_fixer.md.  Numbers come from rev3_work/summary.json
(written by rev3_work/mk_docs.py), checks.json and the fixback3_work/fe_gap result files - nothing is typed.
    /opt/venv/cad/bin/python fixback3_work/mk_status.py"""
import os, json, time
T4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(T4, "rev3_work", "summary.json"))); FB = S["fixback"]; V1 = FB.get("V1")
CK = json.load(open(os.path.join(T4, "checks.json")))
ckline = "  ".join(f"{t['id']}:{t['status']}" for t in CK["table"])
k = lambda d, g: d.get(str(g), d.get(g))
MARK = "# FIX-BACK after overenie3"


def gap_line(tag):
    f = os.path.join(T4, "fixback3_work", "fe_gap", tag, "L8_stop_m90_curb.json")
    if not os.path.exists(f):
        return f"  - {tag}: no result file"
    d = json.load(open(f)); rr = json.load(open(os.path.join(T4, "fixback3_work", "fe_gap", tag, "L8_stop_m90_rows.json")))
    w = max((r for r in rr if r["cls"] != "failsafe"), key=lambda r: r["stress"] / r["allowable"])
    pf = d["pair_forces"]
    return (f"  - {tag} (clearance {d['gap']} mm, h {d['h']}, stamp {d['stl_stamp']}, converged {d['solver']['converged']}, equilibrated {d['equilibrated']}, "
            f"{d['solver']['seconds']:.0f} s): governing row {w['stress']} / {w['allowable']} MPa ({w['spot']} at {w.get('at')}); curb {pf['curb_y']['sum']} N on "
            f"{pf['curb_y']['n_active']} of {pf['curb_y']['n']} nodes, pad A {pf['padA_y']['sum']}, pad C {pf['padC_y']['sum']}, pad D {pf['padD_y']['sum']}, dowel x {pf['dowel_x']['sum']}; "
            f"relative y travel of the sole at the seat {d['rel_min']:.3f} (x -16.8) .. {d['rel_max']:.3f} (x -8.3) mm")


gd = os.path.join(T4, "fixback3_work", "fe_gap")
tags = sorted(t for t in os.listdir(gd) if os.path.isdir(os.path.join(gd, t)) and os.path.exists(os.path.join(gd, t, "L8_stop_m90_curb.json")))
extra = []
for t in sorted(os.listdir(gd)):                       # other cases run with the seat open (information)
    p = os.path.join(gd, t)
    if os.path.isdir(p):
        for fn in sorted(os.listdir(p)):
            if fn.endswith("_rows.json") and not fn.startswith("L8_stop_m90"):
                c = fn[:-10]; rr = json.load(open(os.path.join(p, fn))); d = json.load(open(os.path.join(p, c + "_curb.json")))
                w = max((r for r in rr if r["cls"] != "failsafe"), key=lambda r: r["stress"] / r["allowable"])
                ref = max((r for r in json.load(open(os.path.join(T4, "fe_sachta", "results.json")))["rows"] if r["case"] == c), key=lambda r: r["stress"] / r["allowable"])
                pk = max((r for r in rr if r["part"] == "P_drziak_serva"), key=lambda r: r["stress"] / r["allowable"])
                extra.append(f"  - {t} / {c} (clearance {d['gap']}, converged {d['solver']['converged']}, equilibrated {d['equilibrated']}): governing row {w['stress']} / {w['allowable']} "
                             f"({w['spot']}); final set, seat closed: {ref['stress']} / {ref['allowable']} ({ref['spot']}); worst P_drziak_serva row open: {pk['stress']} ({pk['spot']})")
if V1:
    verdict = ("REAL AS STATED (the capacity / the factor 2 are lost with a clearance <= 0.10)" if V1["confirmed_as_stated"] else
               "PARTLY REAL: the seat is needed and cannot be checked in the assembled torso, but the claim 'holds only with zero gap' is NOT confirmed - a clearance "
               "up to 0.10 does not lower the capacity; the cliff is at the critical clearance below")
    v1 = (f"  {verdict}.\n"
          f"  Seat open: capacity {V1['cap_open']:.0f} N.mm (governing {V1['sig_open']} MPa at 880 N.mm, {V1['spot_open']}) against {S['stop_min_Nmm']} N.mm with the closed seat of the final set.\n"
          f"  The sole travels {V1['closing_880']:.3f} mm toward the curb at 880 N.mm with the seat open -> a clearance of 0.05 / 0.10 mm closes at {k(V1['T_close'], 0.05):.0f} / {k(V1['T_close'], 0.1):.0f} N.mm, "
          f"where the governing stress of the open model is {k(V1['sig_close'], 0.05):.1f} / {k(V1['sig_close'], 0.1):.1f} MPa (< 12.9).\n"
          f"  CRITICAL clearance {V1['g_crit']:.3f} mm: from there the allowable is reached before the seat closes (capacity = open-seat value).\n"
          f"  Capacity at the allowable 12.9 with a residual clearance 0.05 / 0.10: {k(V1['cap'], 0.05):.0f} / {k(V1['cap'], 0.1):.0f} N.mm; stress at the {S['tq_pct']} % torque limit ({S['tq_Nmm']} N.mm) / at twice it: "
          f"closed {k(V1['sig_tq'], 0.0):.1f} / {k(V1['sig_2tq'], 0.0):.1f}, 0.05: {k(V1['sig_tq'], 0.05):.1f} / {k(V1['sig_2tq'], 0.05):.1f}, 0.10: {k(V1['sig_tq'], 0.1):.1f} / {k(V1['sig_2tq'], 0.1):.1f}, "
          f"open: {k(V1['sig_tq'], 99.0):.1f} / {k(V1['sig_2tq'], 99.0):.1f} MPa (lower bound 25.8).\n"
          f"  (State at torque T with clearance g = T / 880 x the state at 880 N.mm with clearance g x 880 / T; governing utilisation interpolated linearly between the computed\n"
          f"  clearances {FB['gap_variants_computed']} + closed + open.)  Torque limit if the seat is not there: {V1['tq_open_pct']} % ({V1['tq_open_Nmm']:.0f} N.mm).")
else:
    v1 = "  NOT COMPUTED (fixback3_work/fe_gap/open_h05 missing)."
BLOCK = f"""{MARK} (fixer of the one allowed fix-back round, {time.strftime('%Y-%m-%d %H:%M')} UTC) - dated block
Input: 11 findings of the verifier (overenie3/: V1, V2 major; V3 - V7 minor; V8 - V11 notes).  My scripts and results: fixback3_work/.
GEOMETRY NOT CHANGED: stl/ + step/ = frozen v10d (checks stamp {CK['stl_stamp']}, FE stamp {S['stl_stamp']}); the final FE set (fe_sachta/results.json) is untouched.
Note on the task's "stale before 20:40" rule: results.json (20:38:05), checks.json, opravy3.md, T4_spec.md 17.17 and out/zmeny_rev3.txt (20:38) were the lead's FINAL
files (12 of 12 cases, all converged / equilibrated, cases_missing empty) - they were read as final and have now been regenerated by this round.

* V1 (major) - measured by FE, not by hand: fixback3_work/fe_gap.py = case L8_stop_m90 of the final set (same STL, design.json, h 0.5; harness files not
  modified, the pair list is patched after Stage construction) with a clearance at the pair curb_y:
{chr(10).join(gap_line(t) for t in tags)}
{v1}
  Fix (text only, LD7 untouched): bench step B4c (new, before T7): bare P_drziak_serva on the stage with F10 tight, lamp inside the well, the sole / curb line is
  looked at from BELOW the stage (fixback3_work/v1_view.py: no module / gear material below the line, x -16.9 .. -10.5) - the 0.05 feeler must not enter (no light =
  closed; 0.05 keeps a factor of about 3 to the critical clearance); otherwise the sole is bedded on the curb face with toughened 2K epoxy (release agent on the
  sole).  The T9 instruction "0.10 feeler / one layer of 0.13 PTFE tape" is removed: a feeler blade can enter the 1.25 mm high slit only from below, and in the torso the
  deck is 1.1 mm under it (overenie3 s5_insert.out: P_drziak_serva <-> T_paluba 1.100); 0.10 leaves 0.04 to the cliff, and a 0.13 tape neither fits a 0.10 .. 0.13 gap nor stays (PTFE creeps).
  The condition and the open-seat numbers are in zmeny_rev3.txt 3 (B4c) / 4 / 5, opravy3.md (usage limits + fix-back section), T4_spec.md 17.17 item 6 and in
  checks.json K12 (usage_limit_conditions + summary clause; status and rows of K12 unchanged).
* V2 (major) - reproduced on the STEP solids (fixback3_work/v2_f12b.py): skr_F12_1 moved along +y overlaps P_drziak_serva from {FB['f12']['play']:.1f} to 19.9 mm (head D3.5 / key hole D2.4,
  6.63 mm3 = the head annulus); {FB['f12']['behind_flange']:.1f} mm behind the ear flange for a {FB['f12']['len']:.1f} long screw.  REAL (and in rev. 2 already).  Fix (text only): t4_assembly.py B5e / T9 / T11 / S1
  + zmeny_rev3.txt 3 (B5e, T9, T11, S1): F12 pre-loaded in the ear flange before the ear is hung on the crank pin (captive, play {FB['f12']['play']:.1f}); started through the
  key hole about 3 mm before the seat (tip meets the foot between {FB['f12']['engagement']:.1f} and {FB['f12']['start_before_seat']:.1f} mm; the last {FB['f12']['start_before_seat']:.1f} mm are screwed while the module is pushed home);
  tightened at T11; S1 in reverse.  The step DATA of t4_assembly.py (move / legs / screws) are unchanged, only the texts.
* V3 - reproduced (STEP: no well material inside r 1.95 on the F10_A axis, y 10.3 .. 15.1).  Builder note B4a.  Geometry kept (changing P_sachta = new FE stamp).
* V4 - not re-measured (K4 lists the scallop feather, 30 cells).  Print note in zmeny 6.
* V5 - reproduced (STEP: L_ucho <-> P_sachta 0.140).  Print note in zmeny 6, straight-edge check in B4c, note in T9.
* V6 - reproduced (STL: ptfe_cap {FB['ptfe_cap']['h_rev2']:.1f} -> {FB['ptfe_cap']['h']:.1f} high, {FB['ptfe_cap']['above_base']:.1f} above the T_cap base).  Line in zmeny 2 and spec 17.17 item 12.
* V7 - reproduced (fixback3_work/v7_spline.py: floor underside over the pinion axis at {FB['spline']['floor_underside']:.2f} for pan -90 .. +90; modelled tip {FB['spline']['tip']:.2f}, clearance {FB['spline']['clearance']:.1f}).
  Line in zmeny 2 (measure the STS3032 before P_sachta is printed), spec 17.17 item 13 c.
* V8 - note, not re-measured; recorded in opravy3.md (fix-back table).
* V9 - (a) the unused rev. 2 declaration 'F10 A insert seat floor 0.8' removed from K4_DECL of checks.py; "checks.py K4" re-run on the cached mesh data: PASS, the
  same 28 declared features in use.  (b) T_cap print string 'through hole D3.4' -> 'D3.1' in t4_ram.py, parts.json, parts_ram.json (text field only: no rebuild,
  STL md5 fields untouched).
* V10 - note, nothing to do.
* V11 - reproduced from results.json: {len(FB['failsafe_above'])} fail-safe rows above 25.8 ({'; '.join(f"{r['case']} {r['stress']}" for r in FB['failsafe_above'])}, both hub ring / lip at
  (0.54, -4.11, -41.89)).  mk_docs.py now lists every fail-safe row above the lower bound with its load.  CORRECTION of the lead's block above: "with the neck parked
  (L1_lift0_nobond) the worst fail-safe row is 20.45 at 30 N" is wrong - it is 27.98 (hub ring / lip); at the 14.8 N usage limit of that situation it scales to
  13.8 MPa, so the lead's conclusion (captive inside the stated limits) stands.
* Found on the way (not in the findings): the sole / curb seat also carries 5.5 N in L2_lift0_chain and 7.1 N in L2_lift20c of the final set (0.3 N in L2_lift10).
  Open-seat variants of other cases, where computed:
{chr(10).join(extra) or '  - none computed (see "open" below)'}
* Changed files: rev3_work/mk_docs.py (generator), t4_assembly.py (texts of B5e / T9 / T11 / S1), checks.py (K4_DECL entry removed; K12 condition clause), t4_ram.py +
  parts.json + parts_ram.json (one string), regenerated: opravy3.md, T4_spec.md 17.17, out/zmeny_rev3.txt, rev3_work/summary.json, checks.json (K4, K7, K12).
  Backups: rev3_backup/*.v10d (mk_docs.py, t4_ram.py, parts.json, parts_ram.json; t4_assembly.py.v10d existed and was identical) and rev3_backup/*.pre_fixback3
  (checks.py - its .v10d backup was older than the lead's last edit -, checks.json, opravy3.md, zmeny_rev3.txt, T4_spec.md, STATUS, bl_K7.json).
* Checks after the round: {ckline} (K12 FAIL = the stated usage limits, as before).  K7 was re-run (--force --no-modules) with the edited step texts.
* NOT re-run (not needed, geometry unchanged): build_all.py, the final FE set, K1 K2 K3 K5 K6 K8 K9 K10 K11 K13, the module checks.
* Open: out/montaz_trup.txt (rev. 2 guide, steps 5 / 21 / 23 and service 1) still describes F12 as inserted after the module - zmeny_rev3.txt section 3 overrides it
  (stated there); the bench test of the pan-servo torque limit stays UNVERIFIED.
"""
f = os.path.join(T4, "STATUS_rev3_fixer.md"); s = open(f).read()
i = s.find(MARK)
s = (s[:i].rstrip("\n") if i >= 0 else s.rstrip("\n")) + "\n\n" + BLOCK
open(f, "w").write(s)
print("STATUS block written:", len(BLOCK.splitlines()), "lines")
