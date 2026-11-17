"""t06 - DEMONTAZ po zlepeni prstenca goliera: da sa T_stred + prstenec + stol (+ kotuc + krk) zdvihnut ako celok okolo pastorka pan
"klucovou dierkou" (zdvih, posun -Y, zdvih)?  A pristup ku skrutke prichytky FPC cez prazdnu sachtu pri pan 30..55.
Spustenie: /opt/venv/bl/bin/python t06_demontaz.py -> t06_demontaz.json"""
import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie_montaz")
from om_lib import *
STAGE = ["P_sachta", "P_koleso", "kolik_kolesa_1", "kolik_kolesa_2", "kolik_dorazu", "vl_F10_1", "vl_F10_2", "ptfe_pas_capu"] + \
        [f"ptfe_pasik_{i}" for i in range(1, 9)]
FRONT = ["T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "skrutka_led_1", "skrutka_led_2", "tesnenie_repro", "reproduktor",
         "T_drziak_repro", "skrutka_repro_1", "skrutka_repro_2", "skrutka_repro_3"]
STRED = ["T_stred"] + FRONT + [f"vlozka_stred_{i}" for i in range(1, 5)] + [f"magnet_zarubna_{i}" for i in range(1, 5)]
TOWER = ["T_spodok", "T_ram", "T_paluba", "cap_pan", "ptfe_podlozka", "servo_J1", "servo_pan", "DPS_riadenie", "menic", "zosilnovac",
         "kondenzator", "skr_F4_1", "skr_F4_2"] + [f"skr_F3_{i}" for i in range(1, 5)] + ["T_prichytka_fpc", "skr_fpc", "pastorok_pan", "skr_pastorok_pan",
         "skr_F7_1", "skr_F7_2"]
FITS = [("T_stred", "T_spodok", 3.6), ("vlozka", "T_spodok", 1.0), ("P_koleso", "cap_pan", 8.0), ("P_sachta", "cap_pan", 8.0),
        ("P_koleso", "pastorok_pan", 4.0), ("kolik_dorazu", "T_paluba", 1.5), ("P_koleso", "ptfe_podlozka", 0.6)]
MOVE = STRED + ["golier_prstenec"] + STAGE + ["golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica", "L_pata"]
R = {"klucova_dierka": {}}
for z1 in (35.0, 35.2, 35.4):
    for dy in (1.6, 1.8, 2.0, 2.4):
        col = sweep(MOVE, TOWER, [((0, 0, 1), z1), ((0, -1, 0), dy), ((0, 0, 1), 70.0)], step=0.4, fits=FITS)
        key = f"zdvih{z1}_posun-Y{dy}"
        R["klucova_dierka"][key] = {f"{a} x {b}": (v["prva_draha_mm"], v["max_hlbka"], v["bod"]) for (a, b), v in col.items()}
        say(key, R["klucova_dierka"][key])
# pristup ku skrutke prichytky FPC cez prazdnu sachtu (krk vonku), stol otoceny o pan
V = mesh("skr_fpc").V; c = V.mean(0); ztop = V[:, 2].max()
R["skr_fpc_cez_sachtu"] = {}
for pan in (-58.5, 20, 30, 35, 40, 45, 50, 55, 60):
    G = Group(STAGE + ["golier_kotuc"], pan=pan)
    G2 = Group(["T_stred", "golier_prstenec", "T_prichytka_fpc"])
    a = tool_channel(G, (c[0], c[1], ztop + 0.05), (0, 0, 1), 60.0, r=2.0, rings=(0.0, 1.0, 2.0))
    b = tool_channel(G2, (c[0], c[1], ztop + 0.05), (0, 0, 1), 60.0, r=2.0, rings=(0.0, 1.0, 2.0))
    R["skr_fpc_cez_sachtu"][str(pan)] = dict(volny=a["volny"] and b["volny"], blok={**a["blok"], **b["blok"]})
    say("skr_fpc pan", pan, R["skr_fpc_cez_sachtu"][str(pan)])
json.dump(R, open(OUT + "/t06_demontaz.json", "w"), indent=1, ensure_ascii=False, default=str)
say("hotovo")
