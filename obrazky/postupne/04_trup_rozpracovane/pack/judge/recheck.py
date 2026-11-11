import sys, json, time
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1"); import t1lib as T
lay = sys.argv[1]; out = sys.argv[2]
L = T.Layout(lay)
t0 = time.time()
res = {"layout": lay}
res["static"] = L.clashes({})
print("static", res["static"], round(time.time()-t0), flush=True)
sw = L.sweep(T.STD_POSES)
res["sweep_std"] = sw
print("sweep", json.dumps(sw), round(time.time()-t0), flush=True)
tp = {}
for nm, p in [("rest", {}), ("std17", T.STD_POSES[17]),
              ("arms100_lift20_tilt40", {"armR": 100, "armL": 100, "lift": 20, "tilt": 40}),
              ("arms90_lift20_tilt40", {"armR": 90, "armL": 90, "lift": 20, "tilt": 40}),
              ("armsback_lift20_tiltm40", {"armR": -45, "armL": -45, "lift": 20, "tilt": -40}),
              ("j1_45_pan85_lift20_tilt40_arms100", {"j1": 45, "pan": 85, "lift": 20, "tilt": 40, "armR": 100, "armL": 100})]:
    tp[nm] = L.tipping(p, accel_g=0.15)
    print(nm, tp[nm], flush=True)
res["tipping"] = tp
json.dump(res, open(out, "w"), indent=1)
print("done", round(time.time()-t0))
