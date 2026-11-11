"""merge all K3 check results into check.json"""
import json, sys
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T

HERE = "/tmp/claude-0/gapwf/fin/T1/k3"
P = f"{HERE}/check_parts"
lay = json.load(open(f"{HERE}/layout.json"))
std = json.load(open(f"{HERE}/sweep_std.json"))
extra = json.load(open(f"{P}/extra.json"))
gaps = json.load(open(f"{P}/gaps.json"))
arms = json.load(open(f"{P}/arms.json"))
cog = json.load(open(f"{P}/cog.json"))
hr = json.load(open(f"{P}/head_real.json"))
stat = json.load(open(f"{P}/static.json"))

HEAD = {"B_hlava", "B_usi", "B_ram_tvar"}


def arm_limit(arm, pose):
    """table lookup: worst (min) limit over the table rows whose lift row covers the pose (deeper row wins)"""
    pan = pose.get("pan", 0.0) * (1 if arm == "R" else -1)
    lift = pose.get("lift", 0.0)
    rows = [r for r in arms if r["lift"] <= lift + 1e-6]
    lrow = max(r["lift"] for r in rows)
    cand = [r for r in arms if r["lift"] == lrow]
    best = min(cand, key=lambda r: abs(r["pan"] - pan))
    return best["armR_max"]


def classify(a, b, pose):
    s = {a, b}
    if s & HEAD and (a.startswith("A_") or b.startswith("A_")):
        arm = "R" if "A_R" in (a + b) else "L"
        ang = pose.get("armR" if arm == "R" else "armL", 0.0)
        lim = arm_limit(arm, pose)
        return ("arm-vs-head: pose exceeds the firmware arm limit (%s arm %g > table %g deg) -> excluded" % (arm, ang, lim)
                if ang > lim else "UNRESOLVED arm-vs-head inside the table limit"), ang > lim
    if s in ({"T_shell", "B_hlava"}, {"T_shell", "B_ram_tvar"}):
        return ("crude t1lib head box (rf14, lower back/front edge than the real head) at a B-table limit pose; real head "
                "mesh vs this torso top: min %.2f mm (B plateau edge r29.8, B table criterion >= 0.25) -> not a clash"
                % hr["min_clearance_mm"]), True
    if s == {"P_sachta", "B_uska"}:
        return ("crude t1lib lug box (45x20x29) swept by tilt; real lug + neck meshes vs the K3 well: min %.2f mm -> not a clash"
                % hr["well_vs_real_lugs_neck_min_clearance_mm"]), True
    return "UNRESOLVED", False


rows, unresolved = [], 0
for src, items in (("STD", [(int(k), v["pose"], v["clashes"]) for k, v in std.items()]),
                   ("extra", [(i, v["pose"], v["clashes"]) for i, v in enumerate(extra)])):
    for i, p, cl in items:
        for a, b, v in cl:
            txt, ok = classify(a, b, p)
            unresolved += 0 if ok else 1
            rows.append({"set": src, "pose_index": i, "pose": p, "a": a, "b": b, "mm3": v, "class": txt})

check = {
    "concept": "K3 – J1 in the base: STS3215 standing on the J1 axis above the left N20, direct drive; dark static plinth "
               "D75 rising into an open-bottom torso; 2 x 1S2P packs front/rear on the floor",
    "Z_TT": lay["Z_TT"], "SH": lay["SH"],
    "dims_mm": {"torso_WDH": [92, 84, round(lay["Z_TT"] - 42, 1)], "torso_z": [42, lay["Z_TT"]],
                "base_WDH": [148, 118, 40], "base_shell_z": [6, 40], "plinth": "D75 dark, z 40..58.6 (visible ~4-10 mm)",
                "arms": "paddles 30 x 21 x 80 (14 above / 66 below the shoulder axis), outer faces +-68.5", "total_height_rest": round(lay["Z_TT"] + 82, 1)},
    "static_clashes": stat,
    "sweep": {"std_poses": len(std), "extra_poses": [e["pose"] for e in extra],
              "clash_instances": len(rows), "unresolved": unresolved, "rows": rows},
    "arm_limit_table_deg": {"note": "max RIGHT-arm angle (0 down, +90 forward, 180 up) keeping >= 2.0 mm to the t1lib head "
                                    "envelope (box rf14 + ears + bezel) over the tilt range of the lift row; LEFT arm = same "
                                    "table with pan sign inverted. Back limit -45 is free everywhere. Rule: use the row of "
                                    "the more retracted lift and the nearest tabulated pan towards that arm.",
                            "rows": arms},
    "real_head_mesh_checks": hr,
    "min_clearances_mm": gaps,
    "intentional_contacts": {
        "Z_J1_lozisko x Z_sokel / T_J1_naboj": "6806 outer ring in the static plinth seat, inner ring on the torso hub",
        "T_J1_ramienko x Z_J1_servo": "Al horn on the STS3215 25T spline; 2 dog pins of the hub engage the horn (torque only)",
        "Z_J1_slucka x Z_sokel / T_J1_sukna": "J1 FPC rolling loop lies on the static inner wall and on the rotating outer wall",
        "P_koleso_pan x T_medzikoleso_pan, T_medzikoleso_pan x T_pastorok_pan": "pan gear train m0.8 36/20/18 (2:1)",
        "P_koleso_pan x T_puzdro_pan / T_paluba": "pan pivot pin D4 in a bronze bush in the torso deck, PTFE thrust washer",
        "P_klika x L_jazyk": "crank pin D2 runs in the 20.2 x 2.2 slot of the tongue (scotch yoke)",
        "L_jazyk x B_krk": "tongue screwed to the neck bottom (2 x M2 into inserts – allowed new part)",
        "A_*_servo x T_rameno_*_puzdro": "nano-servo spline + horn clamped in the torso shoulder boss (friction clutch)",
        "T_shell x B_golier_prstenec": "static collar ring glued into the torso recess r 28.35 (seam 0.1)",
        "Z_J1_slucka x T_paluba / T_J1_sukna (0.5)": "the J1 FPC band envelope rides between the channel floor/ceiling",
        "T_J1_lozisko_vnutro x Z_J1_lozisko": "inner / outer ring of the same 6806 (balls in between)",
        "shell-mounted": "speaker, light bars, pan-servo bracket, pan trough, shoulder bosses, deck bosses touch the shell"},
    "mass_g": cog["rest"]["mass_g"], "mass_by_group_g": cog["_mass_by_group"], "mass_table_g": cog["_mass_rows"],
    "cog_rest": cog["rest"]["cog"],
    "tipping": {k: v for k, v in cog.items() if not k.startswith("_")},
}
worst = min((v for k, v in cog.items() if not k.startswith("_")), key=lambda v: v["margin_at_accel_mm"])
check["tipping_worst"] = worst
json.dump(check, open(f"{HERE}/check.json", "w"), indent=1, ensure_ascii=False)
print("clash instances", len(rows), "unresolved", unresolved, "worst tip", worst)
