#!/bin/bash
# rerun R3/mech/fit.py (option M2b) on R4/tvar/variants_b.py for each variant -> out/fit_<v>.json
cd /tmp/claude-0/gapwf/fin/R4/overenie_tvar
for v in B0 B1 B2 B3; do
  OMP_NUM_THREADS=1 /opt/venv/cad/bin/python -B /tmp/claude-0/gapwf/fin/R3/mech/fit.py /tmp/claude-0/gapwf/fin/R4/tvar/variants_b.py $v M2b --json out/fit_$v.json --quiet
  echo "$v done $(date +%T)"
done
