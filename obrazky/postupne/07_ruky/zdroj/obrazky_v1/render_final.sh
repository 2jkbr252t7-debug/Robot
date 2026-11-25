#!/bin/bash
cd /tmp/claude-0/gapwf/fin/R1/img_v1/work
OUT=/tmp/claude-0/gapwf/fin/R1/img_v1/work/final
mkdir -p $OUT
run() { echo "=== $1 $(date +%T)"; timeout 2400 /opt/venv/bl/bin/python v1_scene.py -- --shot $1 --res $2 --samples $3 --out $OUT > $OUT/log_$1.txt 2>&1; grep "SHOT\|rror\|failed" $OUT/log_$1.txt; }
run rez 1100 56
run front_A 1000 48
run front_B 1000 48
run rozlozena 1600 48
run rozsah 1000 40
run hero 1400 56
echo "ALL DONE $(date +%T)"
