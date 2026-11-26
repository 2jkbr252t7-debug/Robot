#!/bin/bash
# final renders for the R3 comparison sheets (3 threads, <= 64 samples, <= 1400 px wide sheets)
cd /tmp/claude-0/gapwf/fin/R3/img/work
B="/opt/venv/bl/bin/python -B scene_v3.py --"
echo "=== start $(date +%T)"
$B --shot front    --res 700  --samples 48 --exposure -0.3 --out r 2>&1 | grep -E "SHOT|rror|failed"
$B --shot armfront --res 560  --samples 48 --exposure -0.3 --out r 2>&1 | grep -E "SHOT|rror|failed"
$B --shot armonly  --ppm 14   --samples 48 --exposure -0.3 --out r 2>&1 | grep -E "SHOT|rror|failed"
OUT=r PPM=22 SAMP=48 EXPO=-0.2 ./run_rez.sh
$B --shot hero     --res 1000 --samples 48 --exposure -0.3 --out r 2>&1 | grep -E "SHOT|rror|failed"
echo "ALL DONE $(date +%T)"
