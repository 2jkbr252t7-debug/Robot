"""t02 - MONTAZ / SERVIS / ELEKTRO pristupy na skutocnych STL (Blender BVH).  Nic z T4 sa nemeni.
Spustenie: /opt/venv/bl/bin/python t02_montaz.py  -> t02_montaz.json"""
import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie_montaz")
from om_lib import *

STAGE = ["P_sachta", "P_koleso", "kolik_kolesa_1", "kolik_kolesa_2", "kolik_dorazu", "vl_F10_1", "vl_F10_2", "ptfe_pas_capu"] + \
        [f"ptfe_pasik_{i}" for i in range(1, 9)]
NECK = ["krk_predna_polovica", "krk_zadna_polovica", "L_pata"]
LIFT_UNIT = ["servo_zdvih", "P_drziak_serva", "P_kluka", "cap_kluky", "skr_kluky", "skr_F11"]
FRONT = ["T_svetlovod", "T_mriezka", "T_drziak_led", "DPS_led", "skrutka_led_1", "skrutka_led_2", "tesnenie_repro", "reproduktor",
         "T_drziak_repro", "skrutka_repro_1", "skrutka_repro_2", "skrutka_repro_3"]
TOWER = ["T_spodok", "T_ram", "T_paluba", "cap_pan", "ptfe_podlozka", "servo_J1", "servo_pan", "DPS_riadenie", "menic", "zosilnovac",
         "kondenzator", "skr_F4_1", "skr_F4_2", "T_prichytka_fpc", "skr_fpc", "pastorok_pan", "skr_pastorok_pan"] + \
        [f"skr_F3_{i}" for i in range(1, 5)] + [f"skr_F7_{i}" for i in (1, 2)] + [f"skr_F14_{i}" for i in range(1, 5)]
SHELL = ["T_stred", "T_bok_L", "T_bok_P", "golier_prstenec"] + FRONT + [f"magnet_zarubna_{i}" for i in range(1, 5)]
R = {}


def fmt(col):
    return {f"{a} x {b}": dict(prva=v["prva_draha_mm"], posledna=v["posledna_draha_mm"], hlbka=v["max_hlbka"], bod=v["bod"], n=v["n_poloh"])
            for (a, b), v in col.items()}


def box_group(name, x0, x1, y0, y1, z0, z1):
    V = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
    F = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    g = Group.__new__(Group)
    g.names, g.V, g.F, g.own = [name], V, F, np.zeros(len(F), np.int32)
    g.tree = BVHTree.FromPolygons(V.tolist(), F.tolist(), all_triangles=True, epsilon=0.0)
    return g


# ---------------------------------------------------------------------------------------------------------------- A
say("A stol + krk + pata SPOLU hore cez otvor (alternativne poradie: krk je v sachte uz pri vkladani stola)")
R["A_stol_s_krkom_hore"] = fmt(sweep(STAGE + NECK, ["T_stred", "T_paluba", "cap_pan", "pastorok_pan", "skr_pastorok_pan", "ptfe_podlozka",
                                                    "T_prichytka_fpc", "skr_fpc"], [((0, 0, 1), 60.0)], step=0.5,
    fits=[("P_koleso", "cap_pan", 8.0), ("P_sachta", "cap_pan", 8.0), ("P_koleso", "pastorok_pan", 4.0), ("kolik_dorazu", "T_paluba", 1.5)]))
say(R["A_stol_s_krkom_hore"])
say("A2 krk + pata sam hore zo sachty (stol na mieste, prstenec vlepeny, kotuc na stole)")
R["A2_krk_hore_zo_sachty"] = fmt(sweep(NECK, STAGE + ["golier_kotuc", "golier_prstenec", "T_stred"] + LIFT_UNIT, [((0, 0, 1), 60.0)], step=0.5))
say(R["A2_krk_hore_zo_sachty"])

# ---------------------------------------------------------------------------------------------------------------- B
say("B kotuc goliera po krku: hore (zhora cez hlavovy koniec) a dole (zdola cez patu)")
R["B_kotuc_hore_po_krku"] = fmt(sweep(["golier_kotuc"], NECK, [((0, 0, 1), 70.0)], step=0.5))
R["B_kotuc_dole_cez_patu"] = fmt(sweep(["golier_kotuc"], NECK, [((0, 0, -1), 50.0)], step=0.5))
R["B_prstenec_hore_po_krku"] = fmt(sweep(["golier_prstenec"], NECK, [((0, 0, 1), 70.0)], step=0.5))
say(R["B_kotuc_hore_po_krku"], R["B_kotuc_dole_cez_patu"], R["B_prstenec_hore_po_krku"])
nk = np.concatenate([mesh(n).V for n in NECK[:2]])
R["B_krk_bbox"] = [nk.min(0).round(2).tolist(), nk.max(0).round(2).tolist()]
# sirka krku po vyske (ci sa nahor rozsiruje nad drazku kotuca 45.5 x 20.5)
prof = {}
for z in (-30, -10, 0, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24):
    m = np.abs(nk[:, 2] - z) < 1.0
    if m.any():
        prof[z] = [round(float(np.abs(nk[m, 0]).max()), 2), round(float(np.abs(nk[m, 1]).max()), 2)]
R["B_krk_polsirka_x_y_po_z"] = prof
say(R["B_krk_bbox"], prof)

# ---------------------------------------------------------------------------------------------------------------- C
say("C kondenzator: -Z zhora do objimky a +X (zacvaknutie)")
ctx = ["T_ram", "T_paluba", "zosilnovac", "skr_F14_3", "skr_F14_4", "T_spodok"]
R["C_kondenzator_hore"] = fmt(sweep(["kondenzator"], ctx, [((0, 0, 1), 40.0)], step=0.5))
R["C_kondenzator_plusX"] = fmt(sweep(["kondenzator"], ctx, [((1, 0, 0), 25.0)], step=0.25))
say(R["C_kondenzator_hore"], R["C_kondenzator_plusX"])

# ---------------------------------------------------------------------------------------------------------------- D
say("D USB-C zastrcka: obalka 12.4 (z) x 6.5 (y) x L od ustia (-24, 19.7, -68) smerom -X")
ASM = TOWER + SHELL + STAGE + LIFT_UNIT + ["golier_kotuc", "L_ucho", "skr_F12"] + NECK + ["T_klb_P", "T_klb_L"]
G_all = Group([n for n in ASM if n != "DPS_riadenie"])
R["D_usb"] = {}
for L in (20.0, 26.0, 32.0, 40.0):
    b = box_group("usb_zastrcka", -24.0 - L, -24.2, 19.7 - 3.25, 19.7 + 3.25, -68.0 - 6.2, -68.0 + 6.2)
    cr = crossings(b, G_all)
    R["D_usb"][f"L{L:.0f}"] = {k[1]: round(v["hlbka"], 2) for k, v in cr.items()}
    say("  L", L, R["D_usb"][f"L{L:.0f}"])
G_noP = Group([n for n in ASM if n not in ("DPS_riadenie", "T_bok_P", "T_klb_P")])
b = box_group("usb_zastrcka", -24.0 - 40.0, -24.2, 19.7 - 3.25, 19.7 + 3.25, -68.0 - 6.2, -68.0 + 6.2)
R["D_usb"]["L40_bez_praveho_boku"] = {k[1]: round(v["hlbka"], 2) for k, v in crossings(b, G_noP).items()}
say("  bez boku", R["D_usb"]["L40_bez_praveho_boku"])
# volna vzdialenost od ustia v smere -X (luce v ploche zastrcky)
dmin = {}
for dy in (-3.0, 0.0, 3.0):
    for dz in (-6.0, 0.0, 6.0):
        h = ray_free(G_all, (-24.3, 19.7 + dy, -68.0 + dz), (-1, 0, 0), 60.0)
        dmin[f"dy{dy:+.0f}_dz{dz:+.0f}"] = h
R["D_usb"]["luce_-X"] = dmin
say("  luce", dmin)

# ---------------------------------------------------------------------------------------------------------------- E
say("E konektory na hornej hrane riadiacej dosky: volna vyska nad hranou (+Z) a pristup od dvierok (+Y)")
G_in = Group([n for n in ASM if n not in ("DPS_riadenie",)] + ["kabel_zdvih", "spoj_zdvih"])
E = {}
for x in (-14.0, -8.0, 0.0, 8.0, 14.0):
    up = [ray_free(G_in, (x, y, -54.9), (0, 0, 1), 60.0) for y in (17.3, 18.5, 19.9)]
    back = [ray_free(G_in, (x, 20.2, z), (0, 1, 0), 60.0) for z in (-58.5, -57.0, -55.5)]
    E[f"x{x:+.0f}"] = dict(nad_hranou_Z=up, od_dvierok_Y=back)
R["E_konektory_horna_hrana"] = E
say(E)
# dolna hrana / +X pole (GH 6p, PH 2p, 5264 3p): volno v smere +Y a -Z
E2 = {}
for x in (5.0, 12.0, 20.0, 23.0):
    E2[f"x{x:+.0f}"] = dict(od_dvierok_Y=[ray_free(G_in, (x, 22.0, z), (0, 1, 0), 60.0) for z in (-75.0, -70.0, -64.0)],
                            pod_hranou_Z=ray_free(G_in, (x, 19.0, -77.1), (0, 0, -1), 30.0))
R["E_konektory_dolne_pole"] = E2
say(E2)
E3 = {"plusX_koniec_dosky": [ray_free(G_in, (24.1, 19.0, z), (1, 0, 0), 40.0) for z in (-75.0, -66.0, -57.0)],
      "minusX_koniec_dosky": [ray_free(G_in, (-24.1, 17.5, z), (-1, 0, 0), 40.0) for z in (-75.0, -57.0)]}
R["E_konce_dosky"] = E3
say(E3)

# ---------------------------------------------------------------------------------------------------------------- F
say("F STS3215: co je nad dnom puzdra v osi hriadela (-18, 0) - miesto pre zadny cap (dvojosove servo)")
G_t = Group(["T_paluba", "pena_J1", "T_ram"])
R["F_nad_servom_J1"] = {f"({x},{y})": ray_free(G_t, (x, y, -48.29), (0, 0, 1), 20.0) for x, y in ((-18.0, 0.0), (-18.0, 3.0), (-14.0, 0.0), (0.0, 0.0), (10.0, 0.0))}
say(R["F_nad_servom_J1"])
# zastrcky STS3215: co je v zone +X konca (x 15.7..27, |y|<=8, z -66.3..-48.3) a kam sa da vytiahnut zastrcka (+X)
G_p = Group([n for n in ASM if n != "servo_J1"])
R["F_zastrcka_J1_luce_+X"] = {f"y{y:+.0f}_z{z:.0f}": ray_free(G_p, (15.8, y, z), (1, 0, 0), 40.0) for y in (-6.0, 0.0, 6.0) for z in (-64.0, -57.0, -50.0)}
say(R["F_zastrcka_J1_luce_+X"])

# ---------------------------------------------------------------------------------------------------------------- G
say("G modul zdvihu von cez dvierka (+Y) v zlozenom trupe, ucho odmontovane / namontovane")
ctxG = TOWER + SHELL + STAGE + NECK + ["golier_kotuc", "L_jazyk", "skr_jazyka", "kolik_ucha"]
R["G_zdvih_von_bez_ucha"] = fmt(sweep(LIFT_UNIT, ctxG, [((0, 1, 0), 50.0)], step=0.5,
                                      fits=[("P_drziak_serva", "vl_F10", 4.0), ("P_drziak_serva", "P_sachta", 0.6)]))
say(R["G_zdvih_von_bez_ucha"])
R["G_zdvih_von_s_uchom"] = fmt(sweep(LIFT_UNIT, ctxG + ["L_ucho", "skr_F12"], [((0, 1, 0), 50.0)], step=0.5,
                                     fits=[("P_drziak_serva", "vl_F10", 4.0), ("P_drziak_serva", "P_sachta", 0.6)]))
say(R["G_zdvih_von_s_uchom"])
# samotne servo MG90S von z drziaka v trupe (-X smer vysuvania je opak +X montaze): ide to bez vybratia drziaka?
R["G_servo_zdvih_minusX_v_trupe"] = fmt(sweep(["servo_zdvih", "P_kluka", "cap_kluky", "skr_kluky"], ctxG + ["P_drziak_serva"], [((-1, 0, 0), 30.0)], step=0.5))
say(R["G_servo_zdvih_minusX_v_trupe"])

# ---------------------------------------------------------------------------------------------------------------- H
say("H kanaly naradia D4.5: F2 / F1 zospodu (pod suknou), F5 z -X v zlozenom stave")
G_b = Group(["T_spodok", "lozisko_6805", "T_stred", "T_bok_L", "T_bok_P", "pastorok_J1", "skr_F6"])
H = {}
for n in [f"skr_F2_{i}" for i in range(1, 7)] + [f"skr_F1_{i}" for i in range(1, 5)]:
    V = mesh(n).V
    c = V.mean(0); z0 = V[:, 2].min()
    H[n] = dict(r_od_osi=round(float(np.hypot(c[0], c[1])), 2), **tool_channel(G_b, (c[0], c[1], z0 - 0.05), (0, 0, -1), 40.0, r=2.25))
R["H_naradie_zospodu"] = H
say({k: (v["r_od_osi"], v["volny"], v["blok"]) for k, v in H.items()})
G_c = Group([n for n in ASM if n not in ("skr_F5",)])
V = mesh("skr_F5").V
R["H_F5_naradie_-X"] = tool_channel(G_c, (V[:, 0].min() - 0.05, 0.0, -74.0), (-1, 0, 0), 40.0, r=1.2)
G_c2 = Group([n for n in ASM if n not in ("skr_F5", "T_bok_P", "T_klb_P")])
R["H_F5_naradie_-X_bez_boku"] = tool_channel(G_c2, (V[:, 0].min() - 0.05, 0.0, -74.0), (-1, 0, 0), 40.0, r=1.2)
say(R["H_F5_naradie_-X"], R["H_F5_naradie_-X_bez_boku"])

json.dump(R, open(OUT + "/t02_montaz.json", "w"), indent=1, ensure_ascii=False, default=str)
say("hotovo")
