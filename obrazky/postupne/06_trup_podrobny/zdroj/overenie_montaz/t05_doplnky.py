"""t05 - doplnkove merania: vlozky s vynutenym hostitelom, zahlbenie F2, kablovy kut pri kolíske, parapet dvierok voci doske.
Spustenie: /opt/venv/bl/bin/python t05_doplnky.py -> t05_doplnky.json"""
import sys, json
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie_montaz")
import t04_zavity as Z
from om_lib import *
R = {}
R["vlozky_vynuteny_host"] = [Z.measure(n, host=h) for n, h in
    [(f"vlozka_stred_{i}", "T_stred") for i in (1, 2, 3, 4)] + [(f"vl_F2_{i}", "T_ram") for i in range(1, 7)] +
    [("kolik_dorazu", "P_koleso"), ("skr_F5", "T_ram"), ("cap_kluky", "P_kluka")]]
for m in R["vlozky_vynuteny_host"]:
    say(m["prvok"], m["host"], m["d_prvku"], m["dlzka"], [(q.get("d_otvoru"), q.get("stena_min")) for q in m["rezy"]])

# F2: hrubka dna pod kuzelom hlavy: luc +Z z (x + r, y, -84.6) pre r = 1.5 (v otvore D2.8 je vzduch), 1.9, 2.3, 2.6
G = Group(["T_spodok"])
out = {}
for n in ("skr_F2_1", "skr_F2_3", "skr_F2_5", "skr_F1_1"):
    V = mesh(n).V; c = V.mean(0)
    row = {}
    for r in (1.45, 1.7, 2.0, 2.3, 2.6, 3.2):
        zz = []
        for k in range(8):
            a = 2 * math.pi * k / 8
            p = (c[0] + r * math.cos(a), c[1] + r * math.sin(a), -86.5)
            h1 = G.tree.ray_cast(Vector(p), Vector((0, 0, 1)), 12.0)
            if h1[0] is None:
                zz.append(None); continue
            h2 = G.tree.ray_cast(h1[0] + Vector((0, 0, 0.01)), Vector((0, 0, 1)), 12.0)
            zz.append((round(h1[0].z, 2), round(h2[0].z, 2) if h2[0] is not None else None))
        row[f"r{r}"] = zz[:3]
    out[n] = row
R["F2_F1_dno_pod_hlavou (z_spodok, z_vrch) po polomere"] = out
say(out)

# kablovy kut: volna sirka medzi zadnou stenou kolisky a nabojmi T_stred / stenou, v x = -29, 0, 29 pre z = -80, -76, -72
G2 = Group(["T_stred", "T_ram", "T_spodok", "DPS_riadenie", "T_paluba"])
kab = {}
for x in (-29.0, -24.0, 0.0, 24.0, 29.0):
    for z in (-80.0, -76.0, -72.0, -60.0):
        h = G2.tree.ray_cast(Vector((x, 14.25, z)), Vector((0, 1, 0)), 40.0)
        kab[f"x{x:+.0f}_z{z:.0f}"] = None if h[0] is None else (round(h[3], 2), G2.names[G2.own[h[2]]])
R["kablovy_kut_volno_+Y_od_kolisky_y14.25"] = kab
say(kab)
# medzera medzi koncom kolisky a stlpom (prechod kablov na stlpy), z = -80..-50
kab2 = {}
for s in (-1, 1):
    for z in (-80.0, -70.0, -55.0, -45.0):
        for y in (0.0, 12.0):
            x0 = -31.7 if s < 0 else 23.1
            h = G2.tree.ray_cast(Vector((x0, y, z)), Vector((s, 0, 0)), 30.0)
            kab2[f"s{s:+d}_y{y:.0f}_z{z:.0f}"] = None if h[0] is None else (round(h[3], 2), G2.names[G2.own[h[2]]])
R["prechod_koliska_stlp_volno_X"] = kab2
say(kab2)

# parapet dvierok: z spodnej hrany otvoru v T_stred pri x = 0 (luc -Y zvonka dnu) a horna hrana
G3 = Group(["T_stred"])
sill = {}
for z in (-75.0, -73.0, -72.5, -72.0, -71.0, -12.5, -12.0, -11.5, -11.0):
    h = G3.tree.ray_cast(Vector((0.0, 60.0, z)), Vector((0, -1, 0)), 40.0)
    sill[f"z{z}"] = None if h[0] is None else round(h[0].y, 2)
R["dvierkovy_otvor_x0 (y zasahu zvonka; None = otvor)"] = sill
say(sill)
# skrutky LED / F7 / F4: dlzka zavitu v materiali (vzorky pozdlz osi: polomer otvoru < 1.2 = v pilotnom otvore)
eng = {}
for n, host in (("skrutka_led_1", "T_stred"), ("skrutka_repro_1", "T_stred"), ("skr_F7_1", "T_ram"), ("skr_F4_1", "T_ram"), ("skr_F11", "P_drziak_serva"),
                ("skr_F12", "L_pata"), ("skr_fpc", "T_paluba"), ("skr_F14_1", "T_ram"), ("skr_F10_1", "P_sachta"), ("skr_jazyka", "L_pata"),
                ("skr_kluky", "P_kluka")):
    c, d, t0, t1, V = Z.axis_of(n)
    cnt = 0; N = 60
    for i in range(N):
        t = t0 + (i + 0.5) / N * (t1 - t0)
        rr = [a for a, b in Z.radial(host, c, d, t, nang=12, rmax=3.0) if a is not None]
        if len(rr) >= 10 and np.median(rr) < 1.25:
            cnt += 1
    eng[f"{n} v {host}"] = round(cnt / N * (t1 - t0), 2)
R["dlzka_v_otvore_d<2.5 (zaber zavitu, mm)"] = eng
say(eng)
json.dump(R, open(OUT + "/t05_doplnky.json", "w"), indent=1, ensure_ascii=False, default=str)
say("hotovo")
