#!/bin/bash
# usage: fitall.sh v1 v2 ...   -> out/fit_<v>.json + one summary line per variant
cd /tmp/claude-0/gapwf/fin/R4/tvar
for v in "$@"; do
  /opt/venv/cad/bin/python -B /tmp/claude-0/gapwf/fin/R3/mech/fit.py variants_b.py $v M2b --json out/fit_$v.json --quiet
  /opt/venv/cad/bin/python -c "
import json; r=json.load(open('out/fit_$v.json')); p=r['parts']
d=p['DRV_unasac']
lo=sorted(((v['margin_out'],k) for k,v in p.items()))[:3]; li=sorted(((v['margin_in'],k) for k,v in p.items()))[:2]
print('$v fits',r['fits'],'T %.2f'%r['thickness'],'| DRV out %.3f in %.3f @out %s'%(d['wall_out'],d['wall_in'],d['at_out']['local']),'| low out',lo,'| low in',li)"
done
