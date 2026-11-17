"""NOVA mini - T4 torso: the assembly sequence as data (used by checks_bl.py K7 and by the assembly documents).

Each step:
  id, text      label / what happens
  move          parts that travel together along the path (rest-pose geometry, rigid)
  legs          WITHDRAWAL path: list of (direction, distance mm); the mounting motion is the reverse.  Directions are axis strings
                "+x" .. "-z" in the B frame, or in the pan-stage frame when frame = "stage" (then turned by `pan`)
  pan           pan angle of the stage (groups P / L and the finished collar disc / neck) during the step
  ctx           parts present: "before" = everything mounted by the earlier main steps; or an explicit list (bench steps)
  bench         True: sub-assembly on the bench (its parts enter the torso with a later main step)
  hardware      [(part, withdrawal direction)]: inserts / magnets / pins fitted in this step - the mouth must be open
  screws        [(screw, tool direction)]: driven in this step - straight D4.5 tool channel from the head
  fits          [(regex moving, regex static)]: declared sliding / press fits that are not collisions
  with_parts    flexible or pre-fitted parts that arrive with the step without being swept (FPC, leads, tapes, foam)
"""
FRONT = ["T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "skrutka_led_1", "skrutka_led_2", "tesnenie_repro", "reproduktor",
         "T_drziak_repro", "skrutka_repro_1", "skrutka_repro_2", "skrutka_repro_3"]
FLEX = ["fpc_pan", "kabel_zdvih", "vyvod_led", "vyvod_repro", "kabel"]      # flexible / reserved space: never swept, never an obstacle
STAGE = ["P_sachta", "P_koleso", "kolik_kolesa_1", "kolik_kolesa_2", "kolik_dorazu", "vl_F10_1", "vl_F10_2", "spoj_zdvih",
         "ptfe_pas_capu"] + [f"ptfe_pasik_{i}" for i in range(1, 9)]
LIFT_UNIT = ["servo_zdvih", "P_drziak_serva", "P_kluka", "cap_kluky", "skr_kluky", "skr_F11"]
TURNS_WITH_PAN = ["golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica", "kabel"]     # finished parts on the stage

STEPS = [
    # ------------------------------------------------------------------------------------------------ bench sub-assemblies
    dict(id="B1", bench=True, text="heat-set inserts into T_ram (F2 from below, F3 from above, F5 from -X through the tool hole, F8 into the shoulder bosses)",
         move=[], ctx=["T_ram"],
         hardware=[(f"vl_F2_{i}", "-z") for i in range(1, 7)] + [(f"vl_F3_{i}", "+z") for i in range(1, 5)] + [("vl_F5", "-x")]
         + [(f"vl_F8_L{i}", "+x") for i in (1, 2, 3)] + [(f"vl_F8_P{i}", "-x") for i in (1, 2, 3)]),
    dict(id="B2", bench=True, text="pivot pin pressed into the deck, PTFE washer over the boss",
         move=[], ctx=["T_paluba"], hardware=[("cap_pan", "+z")]),
    dict(id="B2b", bench=True, text="PTFE washer over the pivot boss", move=["ptfe_podlozka"], legs=[("+z", 12.0)], ctx=["T_paluba", "cap_pan"]),
    dict(id="B3", bench=True, text="J1 pinion onto the STS3215 spline, screw F6", move=["pastorok_J1"], legs=[("-z", 12.0)], ctx=["servo_J1"],
         fits=[("pastorok_J1", "servo_J1")], screws=[("skr_F6", "-z")]),
    dict(id="B4", bench=True, text="glued inserts and frame magnets into T_stred", move=[], ctx=["T_stred"],
         hardware=[(f"vlozka_stred_{i}", "-z") for i in range(1, 5)] + [(f"magnet_zarubna_{i}", "axis:+y") for i in range(1, 5)]),
    dict(id="B5a", bench=True, text="light guide glued into the bar opening (from inside)", move=["T_svetlovod"], legs=[("+y", 20.0)], ctx=["T_stred"]),
    dict(id="B5b", bench=True, text="grille glued into the slot (from inside)", move=["T_mriezka"], legs=[("+y", 20.0)], ctx=["T_stred", "T_svetlovod"]),
    dict(id="B5c", bench=True, text="LED holder with the LED strip onto its 2 bosses", move=["T_drziak_led", "DPS_led"], legs=[("+y", 20.0)],
         ctx=["T_stred", "T_svetlovod", "T_mriezka"], screws=[("skrutka_led_1", "+y"), ("skrutka_led_2", "+y")], with_parts=["vyvod_led"]),
    dict(id="B5d", bench=True, text="speaker gasket (PORON 1.0, compressed to 0.85 by the clamp ring)", move=["tesnenie_repro"], legs=[("+y", 20.0)],
         fits=[("tesnenie_repro", "T_stred")],
         ctx=["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "skrutka_led_1", "skrutka_led_2"]),
    dict(id="B5e", bench=True, text="speaker between the 3 boss scallops", move=["reproduktor"], legs=[("+y", 20.0)],
         ctx=["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "skrutka_led_1", "skrutka_led_2", "tesnenie_repro"],
         with_parts=["vyvod_repro"]),
    dict(id="B5f", bench=True, text="speaker clamp ring, 3 screws", move=["T_drziak_repro"], legs=[("+y", 20.0)],
         ctx=["T_stred", "T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "skrutka_led_1", "skrutka_led_2", "tesnenie_repro", "reproduktor"],
         screws=[("skrutka_repro_1", "+y"), ("skrutka_repro_2", "+y"), ("skrutka_repro_3", "+y")]),
    dict(id="B6", bench=True, text="stage: dowels and stop pin into the gear, inserts into the bracket pads", move=[], ctx=["P_koleso"],
         hardware=[("kolik_kolesa_1", "+z"), ("kolik_kolesa_2", "+z"), ("kolik_dorazu", "-z")]),
    dict(id="B6b", bench=True, text="glued M2 inserts into the bracket pads of the well", move=[], ctx=["P_sachta"],
         hardware=[("vl_F10_1", "+y"), ("vl_F10_2", "+y")]),
    dict(id="B6c", bench=True, text="pan gear bonded under the hub disc of the well (2 dowels)", move=["P_koleso", "kolik_kolesa_1", "kolik_kolesa_2", "kolik_dorazu"],
         legs=[("-z", 12.0)], ctx=["P_sachta"], fits=[("kolik_kolesa_", "P_sachta")]),
    dict(id="B7a", bench=True, text="MG90S into the bracket (+X), screw F11", move=["servo_zdvih"], legs=[("-x", 30.0)], ctx=["P_drziak_serva"],
         skip_box={"servo_zdvih": ((11.3, 16.0, 20.6, 25.8, -18.25, -13.2), "flexible servo lead (reserved bend space above the case end)")},
         screws=[("skr_F11", "-x")]),
    dict(id="B7b", bench=True, text="crank pin pressed into the crank", move=[], ctx=["P_kluka"], hardware=[("cap_kluky", "-x")]),
    dict(id="B7c", bench=True, text="crank onto the spline at servo zero, crank screw", move=["P_kluka", "cap_kluky"], legs=[("-x", 12.0)],
         ctx=["P_drziak_serva", "servo_zdvih", "skr_F11"], fits=[("P_kluka", "servo_zdvih")], screws=[("skr_kluky", "-x")]),
    dict(id="B8L", bench=True, text="bush into the left shoulder joint (from the inner side), 3 magnets", move=["T_puzdro_L"], legs=[("-x", 25.0)],
         ctx=["T_klb_L"], hardware=[(f"magnet_klb_L{i}", "+x") for i in (1, 2, 3)]),
    dict(id="B8P", bench=True, text="bush into the right shoulder joint (from the inner side), 3 magnets", move=["T_puzdro_P"], legs=[("+x", 25.0)],
         ctx=["T_klb_P"], hardware=[(f"magnet_klb_P{i}", "-x") for i in (1, 2, 3)]),
    dict(id="B9", bench=True, text="4 magnets into the door bosses (from the inner side)", move=[], ctx=["T_dvere"],
         hardware=[(f"magnet_dvierka_{i}", "axis:-y") for i in range(1, 5)]),
    # ------------------------------------------------------------------------------------------------ torso
    dict(id="1", text="6805 bearing into the foot ring of T_spodok (from below, CA)", move=["lozisko_6805"], legs=[("-z", 15.0)], ctx=["T_spodok"],
         base=["T_spodok"]),
    dict(id="2", text="T_ram onto T_spodok, 6 x F2 from below", move=["T_ram"], legs=[("+z", 70.0)],
         with_parts=[f"vl_F2_{i}" for i in range(1, 7)] + [f"vl_F3_{i}" for i in range(1, 5)] + ["vl_F5"] + [f"vl_F8_L{i}" for i in (1, 2, 3)]
         + [f"vl_F8_P{i}" for i in (1, 2, 3)],
         screws=[(f"skr_F2_{i}", "-z") for i in range(1, 7)]),
    dict(id="3", text="STS3215 with its pinion (bench) down into the cradle, pinion through the passage", move=["servo_J1", "pastorok_J1", "skr_F6"],
         legs=[("+z", 60.0)], with_parts=["pena_J1_celo"]),
    dict(id="4", text="STS3032 onto its posts, 2 x F4; its bus plug is pushed in afterwards along -X through the window of the +X post",
         move=["servo_pan"], legs=[("+z", 60.0)], screws=[("skr_F4_1", "+z"), ("skr_F4_2", "+z")],
         skip_box={"servo_pan": ((11.76, 18.8, -24.85, -16.75, -72.75, -64.65), "bus plug + cable bend (reserved space), plugged in after the servo is seated")},
         flex_sweep=[("servo_pan", (11.76, 18.8, -24.85, -16.75, -72.75, -64.65), "+x", 12.0, "plug withdrawn along +X through the post window")]),
    dict(id="5", text="foam pad, deck (with pin and washer) onto the cradle, 4 x F3; set screw F5", move=["T_paluba", "cap_pan", "ptfe_podlozka"],
         legs=[("+z", 60.0)], with_parts=["pena_J1"], screws=[(f"skr_F3_{i}", "+z") for i in range(1, 5)] + [("skr_F5", "-x")]),
    dict(id="6a", text="controller onto its standoffs (from the back), 2 x F7", move=["DPS_riadenie"], legs=[("+y", 40.0)],
         screws=[("skr_F7_1", "+y"), ("skr_F7_2", "+y")]),
    dict(id="6b", text="buck converter onto the right column, 2 x F14", move=["menic"], legs=[("-x", 25.0)], screws=[("skr_F14_1", "-x"), ("skr_F14_2", "-x")]),
    dict(id="6c", text="amplifier onto the left column, 2 x F14", move=["zosilnovac"], legs=[("+x", 25.0)], screws=[("skr_F14_3", "+x"), ("skr_F14_4", "+x")]),
    dict(id="6d", text="capacitor snapped into its clip on the left column (from +X)", move=["kondenzator"], legs=[("+x", 25.0)],
         fits=[("kondenzator", "T_ram")], snap=True),
    dict(id="7", text="T_stred with the front stack lowered straight over the tower, 4 x F1 from below",
         move=["T_stred"] + FRONT + [f"vlozka_stred_{i}" for i in range(1, 5)] + [f"magnet_zarubna_{i}" for i in range(1, 5)],
         legs=[("+z", 100.0)], with_parts=["vyvod_led", "vyvod_repro"], screws=[(f"skr_F1_{i}", "-z") for i in range(1, 5)]),
    dict(id="8", text="pan pinion through the collar bore (2 mm off its axis toward the centre: its tip circle reaches r 29.6, the bore is r 28.35), "
                      "then -Y and down onto the STS3032 shaft; screw from above", move=["pastorok_pan"], legs=[("+z", 6.0), ("+y", 2.0), ("+z", 55.0)],
         fits=[("pastorok_pan", "servo_pan")], screws=[("skr_pastorok_pan", "+z")]),
    dict(id="9", text="pan stage (bench) straight down through the collar bore at pan 0", move=STAGE, legs=[("+z", 60.0)], pan=0.0,
         with_parts=["fpc_pan"]),
    dict(id="10", text="FPC clamp through the door into the channel (pan -58.5), clamp screw from above through the D4.8 hole of the stage top",
         move=["T_prichytka_fpc"], legs=[("+z", 13.0), ("+y", 45.0)], pan=-58.5, screws=[("skr_fpc", "+z")]),
    dict(id="11", text="lift unit (MG90S + bracket + crank, bench) through the door onto the 2 pads, 2 x F10", move=LIFT_UNIT, legs=[("+y", 50.0)],
         pan=0.0, with_parts=["kabel_zdvih"], screws=[("skr_F10_1", "+y"), ("skr_F10_2", "+y")]),
    dict(id="12", text="collar ring glued into the bore", move=["golier_prstenec"], legs=[("+z", 20.0)]),
    dict(id="13", text="neck with the bonded foot down into the well (crank at the bottom dead centre)",
         move=["krk_predna_polovica", "krk_zadna_polovica", "L_pata"], legs=[("+z", 50.0)], pan=0.0, with_parts=["kabel"]),
    dict(id="13b", text="collar disc down the neck onto the stage top (glued)", move=["golier_kotuc"], legs=[("+z", 15.0)], pan=0.0),
    dict(id="14", text="tongue through the end window onto the foot (stage turned to the hard stop +90: the window faces the door), M1.6 screw",
         move=["L_jazyk"], legs=[("+x", 45.0)], frame="stage", pan=90.0, screws=[("skr_jazyka", "+x")]),
    dict(id="15", text="ear: onto the crank pin from -X, then -Y onto the dowel; screw F12 through the door",
         move=["L_ucho"], legs=[("+y", 3.5), ("-x", 3.2), ("+y", 45.0)], pan=0.0, fits=[("L_ucho", "kolik_ucha")], screws=[("skr_F12", "+y")],
         hardware=[("kolik_ucha", "+y")],
         note="the ear dowel D1.5 is pressed into the foot back face through the door and the back window AFTER the neck is in the well "
              "(2.0 proud it would not pass the well wall above the window)"),
    dict(id="16L", text="left side cap pushed on along -X", move=["T_bok_L"], legs=[("+x", 35.0)]),
    dict(id="16P", text="right side cap pushed on along +X", move=["T_bok_P"], legs=[("-x", 35.0)]),
    dict(id="17L", text="2 disc springs, left shoulder joint with bush, 3 x F8", move=["T_klb_L", "T_puzdro_L", "magnet_klb_L1", "magnet_klb_L2", "magnet_klb_L3"],
         legs=[("+x", 30.0)], with_parts=["pruzina_klb_L1", "pruzina_klb_L2"], screws=[(f"skrutka_klb_L{i}", "+x") for i in (1, 2, 3)]),
    dict(id="17P", text="2 disc springs, right shoulder joint with bush, 3 x F8", move=["T_klb_P", "T_puzdro_P", "magnet_klb_P1", "magnet_klb_P2", "magnet_klb_P3"],
         legs=[("-x", 30.0)], with_parts=["pruzina_klb_P1", "pruzina_klb_P2"], screws=[(f"skrutka_klb_P{i}", "-x") for i in (1, 2, 3)]),
    dict(id="18", text="door: held open about 35 deg, hooks pushed in under the top edge, bottom swung in (magnets)", move=["T_dvere", "magnet_dvierka_1", "magnet_dvierka_2",
                                                                                              "magnet_dvierka_3", "magnet_dvierka_4"],
         swing=dict(max_deg=40.0, step_deg=0.5, slide=6.0, pull=30.0)),
    dict(id="19", text="torso onto the base hub (here: dummy stand) - modelled as the stand withdrawn downward",
         move=["Z_naboj_test", "Z_koleso_J1", "Z_skrutka_M8", "Z_pruzina_1", "Z_pruzina_2"], legs=[("-z", 40.0)],
         fits=[("Z_naboj_test", "lozisko_6805")], final=True),
]
