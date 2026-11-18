"""NOVA mini - T4 torso REV. 2: the assembly sequence as data (used by checks_bl.py K7 and by the assembly documents).
(rev. 1 copy: rev2_backup/t4_assembly.py.integrator.bak)  Order = T4_spec.md 17.11 + 17.15 (integrator).

Each step:
  id, text      label / what happens
  move          parts that travel together along the path (rest-pose geometry, rigid)
  legs          WITHDRAWAL path: list of (direction, distance mm); the mounting motion is the reverse.  Directions are axis strings
                "+x" .. "-z" in the B frame, or in the pan-stage frame when frame = "stage" (then turned by `pan`)
  pan           pan angle of the stage (groups P / L and the finished collar disc / neck) during the step
  base          parts that are simply present from this step on (the base part of the build)
  remove        (service steps) parts taken out of the present set before the step
  bench         True: sub-assembly on the bench (its parts enter the torso with a later main step)
  service       True: a service row (D6) - it does not change the present set of the main sequence
  hardware      [(part, withdrawal direction)]: inserts / magnets / pins fitted in this step - the mouth must be open
  hardware_with parts (washers) that arrive with the screws of the step (not path-tested on their own)
  screws        [(screw, tool direction)] or [(screw, tool direction, tool diameter)]: straight tool channel from the head
                (default D4.5; a smaller diameter = the named key, e.g. 1.3 hex key through a D2.4 hole)
  fits          [(regex moving, regex static)]: declared sliding / bonded slide fits that are not collisions
  with_parts    flexible or pre-fitted parts that arrive with the step without being swept (FFC, leads, tapes, foam, shims)
  skip_box      {part: (box, why)}: samples of that part inside the box are not swept (flexible lead / plug)
  lowering      True: the plan-clearance test of a straight lowering is applied in addition (T5: T_stred over the tower)
"""
FRONT = ["T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "podlozka_led_1", "podlozka_led_2", "skrutka_led_1", "skrutka_led_2",
         "tesnenie_repro", "reproduktor", "T_drziak_repro", "podlozka_repro_1", "podlozka_repro_2", "podlozka_repro_3",
         "skrutka_repro_1", "skrutka_repro_2", "skrutka_repro_3"]
# flexible / reserved space: never swept, never an obstacle (FFC, leads, wires of B, PORON, PTFE tapes)
FLEX = ["ffc_par", "ffc_A_krk", "ffc_B_krk", "ffc_A_nosic", "ffc_B_nosic", "pigtail_zdvih", "kabel_zdvih", "konektor_zdvih", "usb_predlzovac",
        "vyvod_led", "vyvod_repro", "kabel", "pena_J1_celo", "ptfe_cap", "ptfe_pas_capu"] + [f"ptfe_pasik_{i}" for i in range(1, 8)]
STAGE = ["P_sachta", "koleso_pan", "vl_F10_A", "vl_F10_B", "kolik_F10"]
LIFT_MODULE = ["P_drziak_serva", "servo_zdvih", "rameno_zdvih", "cap_kluky", "skr_ramena", "skr_F11", "podl_F11", "matica_F11", "L_ucho",
               "kolik_F12"]                 # integrator rev2: the F12 dowel is bonded in the ear (slip fit in the foot)
NECK = ["krk_predna_polovica", "krk_zadna_polovica", "L_pata", "DPS_krk"]
TURNS_WITH_PAN = ["golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica", "kabel"]     # finished parts on the stage
DECK = ["T_paluba", "T_most", "T_cap", "ptfe_podlozka"]
F1_HW = [f"vlozka_stred_{i}" for i in range(1, 5)]
DOOR = ["T_dvere"] + [f"magnet_dvierka_{i}" for i in range(1, 5)]
KEY13 = 1.3                                 # 1.3 hex key (ISO 7380 M2) / ball-end key
SERVICE_T_STRED_OFF = ["T_stred", "T_bok_L", "T_bok_P", "T_klb_L", "T_klb_P"] + DOOR + FRONT + F1_HW \
    + [f"magnet_zarubna_{i}" for i in range(1, 5)] + [f"magnet_klb_{s}{i}" for s in "LP" for i in (1, 2, 3)] \
    + [f"skrutka_klb_{s}{i}" for s in "LP" for i in (1, 2, 3)] + [f"podlozka_klb_{s}{i}" for s in "LP" for i in (1, 2, 3)] \
    + [f"skr_F1_{i}" for i in range(1, 5)] + [f"pd_F1_{i}" for i in range(1, 5)] + ["golier_prstenec", "golier_kotuc"] + STAGE \
    + LIFT_MODULE + NECK + ["skr_F10_A", "skr_F10_B", "podl_F10_A", "podl_F10_B", "skr_F12_1", "skr_F15", "pd_F15", "skr_F4_1", "skr_F4_2"]

STEPS = [
    # ------------------------------------------------------------------------------------------------ bench sub-assemblies
    dict(id="B1", bench=True, text="T_spodok: bonded inserts F3a / F3b (from above), F7 (from the door side), F8 (into the shoulder bosses), "
                                   "stop pins (bonded 8.4 deep in the D3.05 x 8.7 holes - flush the blind holes with IPA first, 24 h), DIN 562 nuts of F4 into the post slots (from +X); fixer rev2: dry-fit T_stred on the bare T_spodok BEFORE bonding and sand stop post 1 / the spigot where they rub",
         move=[], ctx=["T_spodok"],
         hardware=[("vl_F3a_1", "+z"), ("vl_F3a_2", "+z"), ("vl_F3b_1", "+z"), ("vl_F3b_2", "+z"), ("vl_F7_1", "+y"), ("vl_F7_2", "+y")]
         + [(f"vl_F8_L{i}", "+x") for i in (1, 2, 3)] + [(f"vl_F8_P{i}", "-x") for i in (1, 2, 3)]
         + [("kolik_dorazu_1", "+z"), ("kolik_dorazu_2", "+z"), ("mat_F4_1", "+x"), ("mat_F4_2", "+x")]),
    dict(id="B1b", bench=True, text="6805 into the D37.15 seat from below (slide fit + epoxy)", move=["lozisko_6805"], legs=[("-z", 15.0)],
         ctx=["T_spodok"], fits=[("lozisko_6805", "T_spodok")]),
    dict(id="B2", bench=True, text="T_cap bonded on T_most (centred by a temporary M3 screw), PTFE tape on T_cap", move=["T_cap"], legs=[("+z", 10.0)],
         ctx=["T_most"], with_parts=["ptfe_cap"], fits=[("T_cap", "T_most")]),
    dict(id="B3a", bench=True, text="T_stred: bonded M2.5 inserts into the F1 bosses (from below), door-frame magnets", move=[], ctx=["T_stred"],
         hardware=[(f"vlozka_stred_{i}", "-z") for i in range(1, 5)] + [(f"magnet_zarubna_{i}", "axis:+y") for i in range(1, 5)]),
    dict(id="B3b", bench=True, text="light guide glued into the bar opening (from inside)", move=["T_svetlovod"], legs=[("+y", 20.0)], ctx=["T_stred"]),
    dict(id="B3c", bench=True, text="grille glued into the slot (from inside)", move=["T_mriezka"], legs=[("+y", 20.0)], ctx=["T_stred", "T_svetlovod"]),
    dict(id="B3d", bench=True, text="LED holder with the LED strip onto its 2 bosses, 2 x F13 + DIN 125",
         move=["T_drziak_led", "DPS_led", "podlozka_led_1", "podlozka_led_2"], legs=[("+y", 20.0)], ctx=["T_stred", "T_svetlovod", "T_mriezka"],
         screws=[("skrutka_led_1", "+y"), ("skrutka_led_2", "+y")], with_parts=["vyvod_led"]),
    dict(id="B3e", bench=True, text="speaker gasket, speaker", move=["tesnenie_repro", "reproduktor"], legs=[("+y", 20.0)], fits=[("tesnenie_repro", "T_stred")],
         ctx=["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "podlozka_led_1", "podlozka_led_2", "skrutka_led_1", "skrutka_led_2"],
         with_parts=["vyvod_repro"]),
    dict(id="B3f", bench=True, text="speaker clamp ring (closed, 2.0), 3 x F13 + DIN 125",
         move=["T_drziak_repro", "podlozka_repro_1", "podlozka_repro_2", "podlozka_repro_3"], legs=[("+y", 20.0)],
         ctx=["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "podlozka_led_1", "podlozka_led_2", "skrutka_led_1", "skrutka_led_2",
              "tesnenie_repro", "reproduktor"],
         screws=[("skrutka_repro_1", "+y"), ("skrutka_repro_2", "+y"), ("skrutka_repro_3", "+y")]),
    dict(id="B4a", bench=True, text="stage: bonded M2 inserts F10 A / B and the F10 dowel into the back-wall pads", move=[], ctx=["P_sachta"],
         hardware=[("vl_F10_A", "+y"), ("vl_F10_B", "+y"), ("kolik_F10", "+y")]),
    dict(id="B4b", bench=True, text="36T brass gear bonded under the hub disc (tips centred in the drum shroud); PTFE tapes; FFC pair bonded",
         move=["koleso_pan"], legs=[("-z", 12.0)], ctx=["P_sachta", "vl_F10_A", "vl_F10_B", "kolik_F10"],
         with_parts=["ptfe_pas_capu"] + [f"ptfe_pasik_{i}" for i in range(1, 8)] + ["ffc_par"]),
    dict(id="B5a", bench=True, text="MG90S into the pocket along -X (turret through the closed keyhole)", move=["servo_zdvih"], legs=[("+x", 30.0)],
         ctx=["P_drziak_serva"], with_parts=["kabel_zdvih"],
         skip_box={"servo_zdvih": ((11.3, 16.0, 20.6, 25.8, -18.25, -13.2), "flexible servo lead (reserved bend space above the case end)")}),
    dict(id="B5b", bench=True, text="DIN 562 nut into the F11 block, F11 ISO 7380 M2x6 + DIN 125 from +X (1.3 hex key, long leg along the axis)", move=[], ctx=["P_drziak_serva", "servo_zdvih"],
         hardware=[("matica_F11", "+y")], screws=[("skr_F11", "+x", KEY13)], hardware_with=["podl_F11"]),
    dict(id="B5c", bench=True, text="crank pin pressed + Loctite 638 into the Al arm (metal-metal)", move=[], ctx=["rameno_zdvih"], hardware=[("cap_kluky", "-x")]),
    dict(id="B5d", bench=True, text="Al arm onto the MG90S spline at BDC, arm screw", move=["rameno_zdvih", "cap_kluky"], legs=[("-x", 12.0)],
         ctx=["P_drziak_serva", "servo_zdvih", "skr_F11", "podl_F11", "matica_F11"], fits=[("rameno_zdvih", "servo_zdvih")],
         screws=[("skr_ramena", "-x", 2.0)]),
    dict(id="B5e", bench=True, text="F12 dowel bonded (Loctite 638) into the D2.05 ear-flange hole, 3.0 protruding toward the foot (-Y)",
         move=[], ctx=["L_ucho"], hardware=[("kolik_F12", "-y")]),
    dict(id="B6", bench=True, text="neck (B 1-8): Al foot bonded to the FRONT half, DPS_krk bonded into the foot slot (no dowel: slip hole D2.05)",
         move=[], ctx=["L_pata", "krk_predna_polovica"], with_parts=["kabel"]),
    dict(id="B7", bench=True, text="J1 pinion slid over the STS3215 spline + Loctite 638 (24 h)", move=["pastorok_J1"], legs=[("-z", 12.0)], ctx=["servo_J1"],
         fits=[("pastorok_J1", "servo_J1")]),
    dict(id="B7b", bench=True, text="fixer rev2 (B1): pan pinion slid over the STS3032 spline + Loctite 638 (24 h) ON THE BENCH - T_stred now "
                                    "passes the pinion (lip relief r 8.35 about the pinion axis), so no in-situ bond / cure in the torso",
         move=["pastorok_pan"], legs=[("+z", 12.0)], ctx=["servo_pan"], fits=[("pastorok_pan", "servo_pan")]),
    dict(id="B8", bench=True, text="3 + 3 magnets into the shoulder joints, 4 magnets into the door bosses", move=[], ctx=["T_klb_L", "T_klb_P", "T_dvere"],
         hardware=[(f"magnet_klb_L{i}", "+x") for i in (1, 2, 3)] + [(f"magnet_klb_P{i}", "-x") for i in (1, 2, 3)]
         + [(f"magnet_dvierka_{i}", "axis:-y") for i in range(1, 5)]),
    # ------------------------------------------------------------------------------------------------ torso (17.11 T1 .. T16)
    dict(id="T0", text="T_spodok (bench B1, B1b) on the bench (assembly support under the cap rim; the base hub / dummy stand only at T15: "
                       "F16 and F1 are driven from below)", move=[],
         base=["T_spodok", "lozisko_6805"],
         with_parts=["vl_F3a_1", "vl_F3a_2", "vl_F3b_1", "vl_F3b_2", "vl_F7_1", "vl_F7_2", "kolik_dorazu_1", "kolik_dorazu_2", "mat_F4_1", "mat_F4_2"]
         + [f"vl_F8_{s}{i}" for s in "LP" for i in (1, 2, 3)]),
    dict(id="T1", text="STS3215 + pinion into the cradle (pinion through J1_PASS); C shim; F16 x 2 from below", move=["servo_J1", "pastorok_J1"],
         legs=[("+z", 60.0)], with_parts=["podlozka_C_J1", "pena_J1_celo"],
         screws=[("skr_F16_1", "-z"), ("skr_F16_2", "-z")], hardware_with=["pd_F16_1", "pd_F16_2"]),
    dict(id="T2", text="STS3032 WITH its bonded pinion (B7b) lowered 5.5 in front of its seat, slid +Y (tabs into the front-wall slots, +X tab "
                       "under the F3b boss), down 0.2 onto the posts; F4 x 2 loose (F4_1 sits partly under the pinion: 1.3 ball-end key tilted "
                       "28 deg toward +Y); bus plug pushed in afterwards along -X through the +X post window",
         move=["servo_pan", "pastorok_pan"], legs=[("+z", 0.2), ("-y", 5.5), ("+z", 60.0)],
         screws=[("skr_F4_1", (0.06, 0.47, 0.88), KEY13), ("skr_F4_2", "+z", KEY13)], fits=[("pastorok_pan", "servo_pan")],
         skip_box={"servo_pan": ((11.76, 18.8, -24.85, -16.75, -72.75, -64.15), "bus plug + cable bend (reserved space), plugged in after the servo is seated")},
         flex_sweep=[("servo_pan", (11.76, 18.8, -24.85, -16.75, -72.75, -64.15), "+x", 12.0, "plug withdrawn along +X through the post window")]),
    dict(id="T3", text="shim strips on the STS3215; T_paluba, T_most + T_cap into its slot, PTFE washer; F3a x 2, F3b x 2",
         move=DECK, legs=[("+z", 60.0)], with_parts=["podlozka_J1_1", "podlozka_J1_2", "ptfe_cap"],
         screws=[("skr_F3a_1", "+z"), ("skr_F3a_2", "+z"), ("skr_F3b_1", "+z"), ("skr_F3b_2", "+z")], hardware_with=["pd_F3a_1", "pd_F3a_2"]),
    dict(id="T3b", transient=True, text="fixer rev2 (M4 + S3): PAN BACKLASH with the gears in mesh - the bare 36T gear (not yet bonded, B4b comes "
                                        "after) on the taped T_cap; 0.05 paper strip in the mesh, STS3032 pushed along C, F4 tightened (F4_2 1.3 key "
                                        "straight, F4_1 1.3 ball-end key tilted 28 deg toward +Y past the pinion); then the F4 slots are filled with "
                                        "epoxy around the WAXED shanks (positive C lock, S3) and the gear is lifted off again",
         move=["koleso_pan"], legs=[("+z", 40.0)], fits=[("koleso_pan", "(T_cap|ptfe_podlozka|pastorok_pan|ptfe_cap)$")],
         screws=[("skr_F4_1", (0.06, 0.47, 0.88), KEY13), ("skr_F4_2", "+z", KEY13)]),
    dict(id="T4a", text="capacitor in from the back (door side) above the spigot, then 6 down onto its pedestal (cable tie)", move=["kondenzator"],
         legs=[("+z", 6.0), ("+y", 20.0)]),
    dict(id="T4b", text="carrier onto its standoffs + rest pad (from the door side), F7 x 2 flush countersunk (FFC tails NOT yet: they come "
                        "down the bore at T7, M6)", move=["DPS_riadenie"],
         legs=[("+y", 40.0)], screws=[("skr_F7_1", "+y"), ("skr_F7_2", "+y")]),
    dict(id="T4c", text="buck converter onto the right column, F14 x 2", move=["menic"], legs=[("-x", 25.0)],
         screws=[("skr_F14_1", "-x"), ("skr_F14_2", "-x")], hardware_with=["pd_F14_1", "pd_F14_2"]),
    dict(id="T4d", text="amplifier onto the left column, F14 x 2", move=["zosilnovac"], legs=[("+x", 25.0)],
         screws=[("skr_F14_3", "+x"), ("skr_F14_4", "+x")], hardware_with=["pd_F14_3", "pd_F14_4"]),
    dict(id="T5", text="T_stred with the front stack (bench B3) lowered straight down over the tower; F1 x 4 from below (loose)",
         move=["T_stred"] + FRONT + F1_HW + [f"magnet_zarubna_{i}" for i in range(1, 5)], legs=[("+z", 110.0)],
         with_parts=["vyvod_led", "vyvod_repro"], screws=[(f"skr_F1_{i}", "-z") for i in range(1, 5)], hardware_with=[f"pd_F1_{i}" for i in range(1, 5)],
         lowering=True),
    dict(id="T5c", text="fixer rev2 (M1): USB-C FPC extension - slim male end into the ESP32-S3-Zero mouth (+X side, along -X, by hand "
                        "through the door), FPC laid toward the door, female end parked (Kapton) in the door zone",
         move=["usb_predlzovac"], legs=[("+x", 6.7)], with_parts=[]),
    dict(id="T6", text="collar ring glued on the bore shoulder z -2", move=["golier_prstenec"], legs=[("+z", 20.0)]),
    dict(id="T7", text="stage (bench B4) held above the torso: both carrier tails of the FFC pair fed down the EMPTY bore -> deck slot (r 22.4..23.6, "
                       "B az 26..34, visible from above) -> cradle-wall slot (exit above the carrier top) -> ZIFs J_PAN_A / B through the door; "
                       "Kapton static anchor through the bore; then the stage straight down through the glued ring onto T_cap / PTFE at pan 0 "
                       "(fixer rev2 M6: the stage is never tethered to the deck while T_stred / the ring go on); F15 + DIN 9021 through the empty well",
         move=STAGE, legs=[("+z", 60.0)], pan=0.0, with_parts=["ptfe_pas_capu"] + [f"ptfe_pasik_{i}" for i in range(1, 8)] + ["ffc_par", "ffc_A_nosic", "ffc_B_nosic"],
         fits=[("koleso_pan", "(T_cap|ptfe_podlozka|pastorok_pan)$"), ("P_sachta", "T_stred")],
         screws=[("skr_F15", "+z", 3.0)], hardware_with=["pd_F15"]),
    dict(id="T8", text="neck with the foot, F12 dowel and DPS_krk (bench B6) from above into the well at pan 0, held at the lift-0 height (the lift module is not in yet: the F12 dowel along Y must enter the ear hole from the side)", move=NECK, legs=[("+z", 60.0)], pan=0.0,
         with_parts=["kabel", "pigtail_zdvih", "ffc_A_krk", "ffc_B_krk"], fits=[("(krk_|L_pata)", "ptfe_pasik_")]),
    dict(id="T9", text="lift module (bench B5, ear hung on the crank pin, crank at BDC) through the door along -Y onto the rail / pads (F10 dowel); the ear hole slides over the F12 dowel of the foot; F10 A / B",
         move=LIFT_MODULE, legs=[("+y", 50.0)], pan=0.0, with_parts=["kabel_zdvih", "konektor_zdvih"],
         fits=[("P_drziak_serva", "(P_sachta|kolik_F10)$")],
         skip_box={"servo_zdvih": ((11.3, 16.0, 20.6, 25.8, -18.25, -13.2), "flexible servo lead")},
         screws=[("skr_F10_A", "+y"), ("skr_F10_B", "+y", KEY13)], hardware_with=["podl_F10_A", "podl_F10_B"]),
    dict(id="T11", text="F12 ear -> foot with a 1.3 hex key through the D2.4 hole of the stop bridge (pan 0)", move=[], pan=0.0,
         screws=[("skr_F12_1", "+y", KEY13)]),
    dict(id="T12", text="collar disc (B 10) down the neck onto the stage top (glued)", move=["golier_kotuc"], legs=[("+z", 15.0)], pan=0.0),
    dict(id="T13L", text="left side cap along -X", move=["T_bok_L"], legs=[("+x", 35.0)]),
    dict(id="T13Lb", text="left shoulder joint (magnets bonded, B8), F8 x 3 + ISO 7092 in the D4.7 counterbores (1.3 hex precision screwdriver, ISO 7380 M2; fingertips only, head seated + 1/8 turn)",
         move=["T_klb_L", "magnet_klb_L1", "magnet_klb_L2", "magnet_klb_L3"], legs=[("+x", 30.0)],
         screws=[(f"skrutka_klb_L{i}", "+x", 3.0) for i in (1, 2, 3)], hardware_with=[f"podlozka_klb_L{i}" for i in (1, 2, 3)]),
    dict(id="T13P", text="right side cap along +X", move=["T_bok_P"], legs=[("-x", 35.0)]),
    dict(id="T13Pb", text="right shoulder joint, F8 x 3", move=["T_klb_P", "magnet_klb_P1", "magnet_klb_P2", "magnet_klb_P3"],
         legs=[("-x", 30.0)], screws=[(f"skrutka_klb_P{i}", "-x", 3.0) for i in (1, 2, 3)], hardware_with=[f"podlozka_klb_P{i}" for i in (1, 2, 3)]),
    # ------------------------------------------------------------------------------------------------ service rows (D6, K7 new)
    dict(id="S1", service=True, text="SERVICE lift module OUT through the door (ear on the pin, PicoBlade unplugged) at pan 0 - neck in place",
         move=LIFT_MODULE, legs=[("+y", 50.0)], pan=0.0, remove=DOOR + ["skr_F10_A", "skr_F10_B", "podl_F10_A", "podl_F10_B", "skr_F12_1"],
         fits=[("P_drziak_serva", "(P_sachta|kolik_F10)$")], skip_box={"servo_zdvih": ((11.3, 16.0, 20.6, 25.8, -18.25, -13.2), "flexible servo lead")}),
    dict(id="S2", service=True, text="SERVICE neck + foot + DPS_krk up through the glued collar disc (head off, F12 out, ZIFs open, lift module out first = S1: the F12 dowel along Y holds the foot in the ear)", move=NECK,
         legs=[("+z", 60.0)], pan=0.0, remove=DOOR + ["skr_F12_1"] + LIFT_MODULE + ["skr_F10_A", "skr_F10_B", "podl_F10_A", "podl_F10_B"],
         fits=[("(krk_|L_pata)", "ptfe_pasik_")]),
    dict(id="S3", service=True, text="SERVICE stage + gear + collar disc up through the glued ring (neck and lift module out, F15 out)",
         move=STAGE + ["golier_kotuc"], legs=[("+z", 60.0)], pan=0.0,
         remove=DOOR + NECK + LIFT_MODULE + ["skr_F10_A", "skr_F10_B", "podl_F10_A", "podl_F10_B", "skr_F12_1", "skr_F15", "pd_F15"],
         fits=[("koleso_pan", "(T_cap|ptfe_podlozka|pastorok_pan)$"), ("P_sachta", "T_stred")]),
    dict(id="S4", service=True, text="SERVICE pivot screw F15 reached through the empty well (neck out), hex 2.0", move=[], pan=0.0,
         remove=NECK + ["skr_F12_1"], screws=[("skr_F15", "+z", 3.0)]),
    dict(id="S5a", service=True, text="fixer rev2 (B1): SERVICE T_stred (+ front stack, F1 inserts, frame magnets, glued collar ring) lifted STRAIGHT UP "
                                       "with the STS3032 and its bonded pinion in place (stage, neck, lift module out = S1..S3; side caps, joints, door, "
                                       "F1 x 4 out; USB FPC male end and LED / speaker plugs unplugged; deck stays on)",
         move=["T_stred"] + FRONT + F1_HW + [f"magnet_zarubna_{i}" for i in range(1, 5)] + ["golier_prstenec"], legs=[("+z", 110.0)],
         remove=[n for n in SERVICE_T_STRED_OFF if n not in (["T_stred"] + FRONT + F1_HW + [f"magnet_zarubna_{i}" for i in range(1, 5)] + ["golier_prstenec"])]),
    dict(id="S5", service=True, text="SERVICE pan servo with T_stred, side caps, joints, stage, lift module, neck and deck (F3a / F3b) off: bus plug out, F4 out, servo + pinion up 0.2, 5.5 forward (-Y), up",
         move=["servo_pan", "pastorok_pan"], legs=[("+z", 0.2), ("-y", 5.5), ("+z", 60.0)],
         remove=SERVICE_T_STRED_OFF + DECK + ["skr_F3a_1", "skr_F3a_2", "skr_F3b_1", "skr_F3b_2", "pd_F3a_1", "pd_F3a_2", "ptfe_cap"],
         skip_box={"servo_pan": ((11.76, 18.8, -24.85, -16.75, -72.75, -64.15), "bus plug unplugged first (along +X through the post window)")}),
    dict(id="S6", service=True, text="SERVICE carrier out (fixer rev2: with T_stred off = S5a; the 49.8 wide board cannot pass the 41.5 door "
                                      "opening): F7 x 2, ZIFs / plugs / USB FPC open, carrier +Y out of the open tower",
         move=["DPS_riadenie"], legs=[("+y", 40.0)], remove=SERVICE_T_STRED_OFF + ["skr_F7_1", "skr_F7_2"]),
    dict(id="T15", text="torso onto the base hub (here: the dummy stand withdrawn downward)",
         move=["Z_naboj_test", "Z_koleso_J1", "Z_skrutka_M8", "Z_pruzina_1", "Z_pruzina_2"], legs=[("-z", 40.0)],
         fits=[("Z_naboj_test", "lozisko_6805"), ("Z_koleso_J1", "pastorok_J1")], final=True),
    dict(id="T14", text="door straight in along -Y onto the ledge (no hooks; 4 magnet pairs) - fixer rev2: AFTER the torso is on the base and the base FFC is plugged into J_J1 through the door (m7)", move=DOOR, legs=[("+y", 30.0)]),
]
