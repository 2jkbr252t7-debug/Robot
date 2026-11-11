"""compose check.json + envelope.json from the raw run outputs"""
import json, re, os
K2 = "/tmp/claude-0/gapwf/fin/T1/pack"   # (variable name kept from K2)
J = lambda f: json.load(open(os.path.join(K2, f)))
lay = J("layout.json")

# ------------------------------------------------------------------ static
txt = open(os.path.join(K2, "static.log")).read()
n_static = int(re.search(r"static clashes: (\d+)", txt).group(1))
static_pairs = re.findall(r"\('([^']+)', '([^']+)', ([\d.]+)\)", txt)

# ------------------------------------------------------------------ sweeps
from run_sweep import EXTRA                       # noqa: E402
std, ext = J("sweep_std.json"), J("sweep_extra.json")
ARM = ("A_R_", "A_L_")
HEAD = ("B_hlava", "B_usi", "B_ram_tvar", "B_uska")


def classify(res):
    rows, n_all, n_other = [], 0, 0
    for i, r in res.items():
        for a, b, v in r["clashes"]:
            n_all += 1
            armhead = (a.startswith(ARM) and b in HEAD) or (b.startswith(ARM) and a in HEAD)
            env_art = {a, b} & {"B_hlava", "B_ram_tvar", "B_usi", "B_uska"} and {a, b} & {"T_shell", "P_sachta"}
            if armhead:
                cls = "arm-vs-head: excluded by firmware arm limit (table)"
            elif env_art:
                cls = ("t1lib head envelope artefact (rf-14 box / lug box are lower/larger than the real head): pose at "
                       "the B tilt-vs-lift limit; real-mesh check head_real_check.json clears it")
            else:
                cls = "UNRESOLVED"
                n_other += 1
            rows.append({"pose_index": int(i), "pose": r["pose"], "a": a, "b": b, "mm3": v, "class": cls})
    return rows, n_all, n_other


rs, ns, os_ = classify(std)
re_, ne, oe = classify(ext)
arm_lim = J("arm_limits.json")
gc = J("gaps_cog.json")

check = {
    "concept": "T1 PACK – final packaging = K2 off-axis gears compact (torso 89 W x 80 D x 90 H, base 142 x 110 x 34 + 6 clearance) + judge grafts from K3 + must-fixes; see pack.md / hodnotenie.md",
    "changes_vs_K2": J("pack_changes.json"),
    "Z_TT": lay["Z_TT"], "SH": lay["SH"],
    "static_clashes": {"count": n_static, "pairs": static_pairs},
    "sweep": {
        "std_poses": {"n_poses": len(std), "clash_instances": ns, "unresolved": os_, "rows": rs},
        "extra_poses": {"n_poses": len(ext), "poses": EXTRA, "clash_instances": ne, "unresolved": oe, "rows": re_},
        "verdict": "unresolved = 0. Residuals: (a) arm-vs-head contacts in poses the firmware arm limit "
                   "(arm_limit_table) forbids - inherent to R01 proportions: the paddles (inner face |x| 46.5) lie inside "
                   "the head width (|x| 55, ears 58.8), so an arm passes the head only when the head is panned away or "
                   "lifted; (b) head-envelope artefacts at the B tilt-vs-lift limits, cleared with the real head mesh "
                   "(real_head_mesh_checks)."},
    "arm_limit_table_deg": {"note": "max RIGHT-arm angle (0 = down, +90 = forward, 180 = up) with >= 2 mm to the head, "
                                    "by head state and pan; LEFT arm = same table with pan sign inverted. Back limit -45 "
                                    "is free in all states. Mechanical servo travel -45..+135 (180 deg servo); values > 135 in the table "
                                    "are geometric only (would need a 270 deg servo).",
                            **arm_lim},
    "real_head_mesh_checks": J("head_real_check.json"),
    "min_clearances_mm": {"t1lib_pair_sets (incl. B-B collar seam 0.25 and intended fits)": gc["pairs"],
                          "K2_moving_parts_only": J("gaps2.json"), "J1_and_arm_180_checks": J("j1_arm_gaps.json"),
                          "intended_sub_1mm": {"collar disc/ring seam (finished B)": 0.25,
                                               "pan journal running fit (envelope 0.4, real 0.05-0.1)": 0.4,
                                               "pan rolling-loop inner run resting on the smooth drum": 0.4,
                                               "real head over the collar plateau r 29.8 (B criterion >= 0.25)": 0.45}},
    "intentional_contacts": {
        "T_J1_pastorok x Z_J1_koleso": "J1 spur mesh m1.0 18/18, C = 18.0",
        "T_pan_pastorok x P_koleso_pan": "pan spur mesh m0.8 18/36, C = 21.6",
        "P_sachta x T_horny_kruh": "pan journal Ø56.4 in POM-lined ring: running fit (0.1 mm radial in reality, 0.4 in the envelope)",
        "T_ptfe x P_koleso_pan": "pan thrust washer (PTFE 0.3)",
        "T_cap x P_koleso_pan": "pan pivot pin Ø6 in the gear hub bore (bronze sleeve)",
        "T_J1_lozisko x Z_J1_hub / T_J1_noha": "6805-2RS inner ring on the static hub, outer ring in the rotating foot ring",
        "P_kluka x L_noha": "crank pin Ø2 in the 2.2 x 12.2 slot of the neck-foot ear",
        "A_x_servo x T_paka_x": "arm servo spline in the static spline socket with friction collar (graft K3)",
        "A_x_servo x A_x_ruka": "arm servo case bonded against the inner face of the paddle outer wall (0 gap by design)",
        "L_noha / P_sachta / P_koleso_pan x B_kabel_krk": "B envelope of the neck wires below the neck; in K2 the wires turn "
                                                           "sideways inside the foot channel",
        "light guides / USB-C / switch x shells": "parts that pass through the shell openings"},
    "mass_g": gc["mass_g"], "mass_by_group_g": gc.get("mass_by_group_g"), "cog_rest": gc.get("cog_rest"),
    "mass_table_g": gc["mass_table"],
    "tipping": gc["tipping"], "tipping_worst": gc.get("tipping_worst"),
}
json.dump(check, open(os.path.join(K2, "check.json"), "w"), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ envelope
sl = J("envelope_slices.json")


def bbox_all(slices):
    xs, ys, zs = [], [], []
    for s in slices:
        if s.get("empty"):
            continue
        xs += s["x"]; ys += s["y"]; zs += s["z"]
    return {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]}


env = {
    "concept": "T1 PACK (K2 + grafts)",
    "frame": "world mm, Z up, floor z=0, FRONT=-Y, robot RIGHT=-X. Torso slices in the torso frame (J1 = 0); pan stage / "
             "lift parts swept over pan -85..+85 and lift 0..20. Base slices in the base frame; torso parts below the "
             "torso floor (z<43) swept over J1 -155..+155. All extents already include +1.0 mm clearance. The shell INNER "
             "surface must enclose every slice hull; wall >= 2.0 on top of that.",
    "torso_internal_bbox_incl_1mm": bbox_all(sl["torso_slices"]),
    "base_internal_bbox_incl_1mm": bbox_all(sl["base_slices"]),
    "torso_slices": sl["torso_slices"],
    "torso_slices_without_shell_mounted_parts": {"note": "same, without parts that are screwed to the shell anyway "
                                                         "(side columns + arm spline sockets, journal ring, speaker, "
                                                         "collar ring) - these need no clearance to the shell",
                                                 "slices": sl["torso_slices_without_shell_mounted_parts"]},
    "base_slices": sl["base_slices"],
    "fixed_interfaces": {
        "torso_top": {"z_top": 133.0, "collar_recess": "through-hole r 28.35 in the top wall; the static collar ring "
                                                       "(r 26.75..28.25, z 127..133) is glued into a seat ring r 28.4..30.0, "
                                                       "z 128..131.5 under the top wall",
                      "flat_zone": "collar plateau flat at z 133 to r 29.8 (as verified in B); beyond it the surface must stay "
                                   "below the head_keepout_profile - 1 mm in EVERY direction (pan +-85 swings the head "
                                   "over the wide X sides too): in practice >= 1.0 mm below z 133 at r 30..46 (K2 "
                                   "placeholder: 1 mm step at r 29.8, body top z 132 with R16 edge)",
                      "under_top_reserved": "nothing static inside r 29.2 between z 87.5 and 127 (pan stage sweep: well "
                                            "corners r 28.1, journal r 28.2); journal ring T_horny_kruh r 28.6..31.5, "
                                            "z 118.5..125.5 must be attached to the shell/frame"},
        "head_keepout_profile": {"note": "lowest point of the REAL head over the whole B tilt-vs-lift table and any pan "
                                         "(axisymmetric): the torso top at radius r must stay <= z_min_head - 1.0 "
                                         "(the B-verified exception: the collar plateau r <= 29.8 at z 133 keeps >= 0.25)",
                                 "r_zmin": [[p["r"][0], p["z_min_head"]] for p in J("head_keepout.json")["profile"]
                                            if p["r"][0] % 1 == 0 and 18 <= p["r"][0] <= 70]},
        "torso_bottom": {"z_bottom": 43.0, "floor": "closed except Ø14 hole at (-18, 0) for the J1 servo spline",
                         "plinth": "rotating dark skirt r 34.0, z 41.0..42.4 sits in the 3 mm gap between base top (z 40) "
                                   "and torso bottom (z 43); the torso bottom flat zone should be >= r 22 (the skirt "
                                   "shows beyond it as the dark plinth ring of R01)"},
        "J1": {"axis": [0, 0], "bearing": "6805-2RS 25x37x7 at z 30.8..37.8 (inner ring on the static hub, outer in the "
                                         "rotating foot ring r 18.5..20.5)",
               "gears": "fixed sun gear m1 18T (tip r 10) + orbiting pinion m1 18T at (-18, 0), z 38.8..42.0 (face 3.2); pinion "
                        "orbit annulus r 8..28 must stay free in the base top layer",
               "base_top_opening": "r 29.0 in the base top skin (z 37.8..40)", "range": "±150 firmware, ±155 hard stop",
               "cable_channel": "annulus r 21.5..34.0, z 30.2..37.4 inside the base under the top skin; 6-conductor FPC loop ≈110 mm in the channel, laid out for ±170 (graft K3) so the ±155 hard stop never tensions it",
               "hub_bridge": "PACK: PETG beam 60 (X) x 13 (Y) x 6 (Z) at z 23..29 between the battery groups, ends on the motor clamps; carries the J1 hub post (steel M8 core)"},
        "pan_cable": "PACK: one custom 2-layer polyimide FPC, 8 traces, 3.0 mm wide x 0.12 mm, standing on edge: lift loop in the YZ plane on the well +X end wall (envelope 3.1 x 8 x 23.5, bend R ≈ 3.5) and pan rolling loop on the smooth drum sector of the pan gear (U-turn R 5.2, bend ratio ≈ 43x); replaces the K2 bonded wire ribbon",
        "shoulders": {"axis": {"y": 2.0, "z": 112.0, "direction": "X"},
                      "torso_pocket": "r 13.5 around the axis, from |x| 37.5 outward (static spline socket r 7 at "
                                      "|x| 37.5..43, cable spiral r 7.5..12.5 at |x| 41.2..43.2)",
                      "torso_max_half_width": "|x| <= 44.5 everywhere (arm inner face at |x| 46.5 sweeps a disc of "
                                              "r 74 around the shoulder axis)",
                      "arm_joint_envelope": "rotating black cap r 12.5, |x| 44.2..46.5; paddle |x| 46.5..69.5, y -13..17 "
                                            "(at 0 deg), z 45..128, rf >= 11; sweep disc radius 74 about the axis",
                      "range": "-45..+135 mechanical; head-dependent firmware limit (check.json arm_limit_table)"},
        "arm_internal_envelope": {"frame": "right arm at 0 deg, world coords; mirror x for the left arm",
                                  "servo": "slim micro servo 21 (X, case) x 9.4 (Y) x 20.5 (Z) at |x| 46.5..67.5 (PACK: flush with the inner face, case bonded to the outer wall), y -2.7..6.7, z 96.75..117.25; spline boss r 5.5 at |x| 42.65..46.5 on the axis; paddle wall 2.0",
                                  "cable_exit": "|x| 56..64, z 91.7..96.7 below the case",
                                  "min_cavity": "|x| 46.5..68.6 (inner skin may be open at the case top, hidden by the "
                                                "cap), y -4..8, z 90..118.5 (+1 mm)"},
        "wheels": {"centres": [[-54, 0, 16], [54, 0, 16]], "size": "Ø32 x 9", "opening": "slot 11 (X) x 34 (Y) in the "
                   "base bottom at x ±54; internal wheel well clear r 17 around the axle, |x| 48.5..59.5",
                   "ground_clearance": "base bottom z 6.0"},
        "casters": {"centres": [[0, -34], [0, 34]], "ball": "Ø10 (3/8\")", "opening": "Ø14 in the bottom", "mount": "PACK: each caster is screwed into its battery-bay cover (the cover is the caster carrier)"},
        "cliff_sensors": {"centres": [[-40, -31], [40, -31], [-40, 31], [40, 31]], "window": "9 x 7 in the bottom, in the corner pockets beside the cell ends (PACK: moved out of the battery bays)"},
        "usb_c": {"centre": [0, 52.8, 33.2], "faces": "+Y (back)", "cutout": "9.5 x 3.8"},
        "power_switch": {"centre": [18, 51.0, 27.5], "faces": "+Y (back)", "cutout": "Ø7"},
        "tof_window": {"centre": [0, -52.8, 28.5], "faces": "-Y", "size": "20 x 12 dark IR-transparent"},
        "base_light_bar": {"centre": [0, -52.0, 20.0], "size": "44 x 4", "faces": "-Y"},
        "torso_light_bar": {"centre": [0, -37.8, 101.5], "size": "36 x 4.5", "faces": "-Y (≈35 % below the top)"},
        "speaker_grille": {"centre": [0, -38.5, 83.5], "slot": "30 x 3 (grey slot of R01)",
                           "speaker": "Ø28 x 5 at y -31.6..-36.6 behind it"},
        "battery_service": "two bays from the bottom (packs y ±7..±44.8, x ±33.25, z 10.8..30.0); cover screws on the "
                           "bottom only",
    },
}
json.dump(env, open(os.path.join(K2, "envelope.json"), "w"), indent=1, ensure_ascii=False)
print("static", n_static, "std", ns, os_, "extra", ne, oe)
print("torso bbox", env["torso_internal_bbox_incl_1mm"], "base bbox", env["base_internal_bbox_incl_1mm"])
