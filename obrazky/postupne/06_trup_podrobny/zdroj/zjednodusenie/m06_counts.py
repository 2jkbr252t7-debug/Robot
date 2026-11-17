"""m06 - part / fastener / screw-kind counts before and after the recommended architecture, computed from parts.json
by applying the deltas of zjednodusenie.md (list below). Run: /opt/venv/cad/bin/python m06_counts.py"""
import json, re
from zj_lib import T4, dump, say

P = [p["name"] for p in json.load(open(T4 + "/parts.json"))["parts"]]
printed = {p["name"] for p in json.load(open(T4 + "/parts.json"))["parts"] if p.get("printed")}

removed = {
    "T_ram": "merged into T_spodok (P03)",
    "T_prichytka_fpc": "FFC anchored in a deck slot (P02)",
    "P_kluka": "supplied MG90S horn is the crank (P05)",
    "L_jazyk": "FFC enters the neck-board ZIF, no tongue (P02)",
    "T_puzdro_L": "deferred to the arm round (P08)", "T_puzdro_P": "deferred to the arm round (P08)",
    "fpc_pan": "2 x stock FFC (P02)", "spoj_zdvih": "neck board takes the lift servo (P02)",
    "skr_F5": "J1 mesh set by shims (P06)", "vl_F5": "J1 mesh set by shims (P06)",
    "skr_fpc": "clamp gone (P02)", "skr_kluky": "horn screw supplied with the servo (P05)",
    "skr_jazyka": "tongue gone (P02)", "kolik_ucha": "printed key on the ear flange (P12)",
    "kolik_dorazu": "replaced by 2 deck pins (P09)",
}
removed.update({f"skr_F2_{i}": "F2 gone with the merge (P03)" for i in range(1, 7)})
removed.update({f"vl_F2_{i}": "F2 gone with the merge (P03)" for i in range(1, 7)})
removed.update({n: "springs go with the bush (P08)" for n in P if n.startswith("pruzina_klb")})
added = {
    "fpc_A (stock FFC 0.5 mm 5p 200 mm)": "P02", "fpc_B (stock FFC 0.5 mm 5p 200 mm)": "P02",
    "DPS_krk (neck board, rigid 0.8, 2 ZIF + JST-SH 3p)": "P02",
    "lift-servo pigtail 3 x AWG30 + inline JST/Dupont 1x3": "P02",
    "pivot sleeve D6 x 3.1": "P01", "pivot screw M2.5x8 ISO 7380": "P01", "washer DIN 9021 M2.5": "P01",
    "insert M2.5 (pivot boss)": "P01",
    "stop pin D2 #1": "P09", "stop pin D2 #2": "P09",
    "square nut DIN 562 M2 (F4) #1": "P04", "square nut DIN 562 M2 (F4) #2": "P04",
    "square nut DIN 562 M2 (F11)": "P04", "square nut DIN 562 M2 (F12)": "P04",
    "insert M2 (F7) #1": "P04", "insert M2 (F7) #2": "P04",
}
missing = [n for n in removed if n not in P]
after = [n for n in P if n not in removed] + list(added)
pr_after = sorted((printed - set(removed)))
res = dict(before=dict(parts=len(P), printed=len(printed)),
           removed=len(removed), added=len(added), missing_names=missing,
           after=dict(parts=len(after), printed=len(pr_after), printed_list=pr_after,
                      printed_if_front_bracket_merge=len(pr_after) - 1))
# screw kinds after (P04 family) - listed, not derived
res["screw_kinds_after"] = ["M2x6 ISO 7380", "M2x10 ISO 7380", "M2.5x6 ISO 7380", "M2.5x8 ISO 7380",
                            "M2x6 thread-forming for plastics (F13, F14 one-time joints)",
                            "M3x8 ISO 10642 (J1 pinion, bought-part joint)",
                            "screws supplied with the servos (pan pinion, MG90S horn)"]
res["insert_nut_kinds_after"] = ["brass knurled insert M2 OD 3.2 x 3.0 (bonded)",
                                 "brass knurled insert M2.5 OD 3.5 x 3.5..4.0 (bonded)", "square nut DIN 562 M2"]
dump("m06_counts.json", res)
say(res["before"], "->", {k: v for k, v in res["after"].items() if k != "printed_list"}, "missing", missing)
say(pr_after)
