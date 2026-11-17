"""t01 - SERVIS: da sa po zlepeni goliera este dostat k servu pan (STS3032), pastorku pan a servu J1 (STS3215)?
Spustenie: /opt/venv/bl/bin/python t01_servis.py"""
import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie_montaz")
from om_lib import *

STAGE = ["P_sachta", "P_koleso", "kolik_kolesa_1", "kolik_kolesa_2", "kolik_dorazu", "vl_F10_1", "vl_F10_2", "ptfe_pas_capu"] + \
        [f"ptfe_pasik_{i}" for i in range(1, 9)]
FRONT = ["T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "skrutka_led_1", "skrutka_led_2", "tesnenie_repro", "reproduktor",
         "T_drziak_repro", "skrutka_repro_1", "skrutka_repro_2", "skrutka_repro_3"]
STRED = ["T_stred"] + FRONT + [f"vlozka_stred_{i}" for i in range(1, 5)] + [f"magnet_zarubna_{i}" for i in range(1, 5)]
TOWER = ["T_spodok", "T_ram", "T_paluba", "cap_pan", "ptfe_podlozka", "servo_J1", "servo_pan", "DPS_riadenie", "menic", "zosilnovac",
         "kondenzator", "skr_F4_1", "skr_F4_2"] + [f"skr_F3_{i}" for i in range(1, 5)] + ["T_prichytka_fpc", "skr_fpc"]
R = {}

say("S1 stol (so zlepenym kotucom) hore cez otvor, prstenec goliera VLEPENY v T_stred")
R["S1_stol_hore_s_prstencom"] = {f"{a} x {b}": v for (a, b), v in
    sweep(STAGE + ["golier_kotuc"], ["T_stred", "golier_prstenec"], [((0, 0, 1), 60.0)], step=0.25).items()}
say(R["S1_stol_hore_s_prstencom"])

say("S1b to iste bez prstenca (= montazny krok 9 v opacnom smere)")
R["S1b_stol_hore_bez_prstenca"] = {f"{a} x {b}": v for (a, b), v in
    sweep(STAGE, ["T_stred", "T_paluba", "cap_pan", "pastorok_pan", "skr_pastorok_pan", "ptfe_podlozka"], [((0, 0, 1), 60.0)], step=0.25,
          fits=[("P_koleso", "cap_pan", 8.0), ("P_sachta", "cap_pan", 8.0), ("P_koleso", "pastorok_pan", 4.0), ("kolik_dorazu", "T_paluba", 1.5)]).items()}
say(R["S1b_stol_hore_bez_prstenca"])

say("S2 T_stred (+ prstenec + predna zostava) hore, stol ostava na cape, pastorok pan na serve; modul zdvihu a krk vybrate")
R["S2_stred_hore_cez_stol"] = {f"{a} x {b}": v for (a, b), v in
    sweep(STRED + ["golier_prstenec"], TOWER + STAGE + ["golier_kotuc", "pastorok_pan", "skr_pastorok_pan"], [((0, 0, 1), 100.0)], step=0.5,
          fits=[("T_stred", "T_spodok", 3.6), ("vlozka", "T_spodok", 1.0)]).items()}
say(R["S2_stred_hore_cez_stol"])

say("S3 T_stred + prstenec + stol (visi na prstenci) spolu hore; pastorok pan ostava")
MOVE3 = STRED + ["golier_prstenec"] + STAGE + ["golier_kotuc"]
R["S3_stred_a_stol_spolu_hore"] = {f"{a} x {b}": v for (a, b), v in
    sweep(MOVE3, TOWER + ["pastorok_pan", "skr_pastorok_pan"], [((0, 0, 1), 100.0)], step=0.5,
          fits=[("T_stred", "T_spodok", 3.6), ("vlozka", "T_spodok", 1.0), ("P_koleso", "cap_pan", 8.0), ("P_sachta", "cap_pan", 8.0),
                ("P_koleso", "pastorok_pan", 4.0), ("kolik_dorazu", "T_paluba", 1.5)]).items()}
say(R["S3_stred_a_stol_spolu_hore"])

say("S3b to iste, ale po 4 mm zdvihu posun celku o dy (hlada sa posun, ktory obide pastorok)")
R["S3b_s_posunom"] = {}
for dy in (0.8, 1.0, 1.3, 1.6, 2.0):
    col = sweep(MOVE3, TOWER + ["pastorok_pan", "skr_pastorok_pan"], [((0, 0, 1), 4.0), ((0, 1, 0), dy), ((0, 0, 1), 96.0)], step=0.5,
                fits=[("T_stred", "T_spodok", 3.6), ("vlozka", "T_spodok", 1.0), ("P_koleso", "cap_pan", 8.0), ("P_sachta", "cap_pan", 8.0),
                      ("P_koleso", "pastorok_pan", 4.0), ("kolik_dorazu", "T_paluba", 1.5)])
    R["S3b_s_posunom"][str(dy)] = {f"{a} x {b}": v for (a, b), v in col.items()}
    say("  dy", dy, {k: (v["prva_draha_mm"], v["max_hlbka"]) for k, v in R["S3b_s_posunom"][str(dy)].items()})

json.dump(R, open(OUT + "/t01_servis.json", "w"), indent=1, ensure_ascii=False)
say("hotovo")
