#!/bin/bash
# R4 final renders for v4_ruka_B_zaoblenia.png (sheet 1) and v4_klb_ramena.png (sheet 2): 48 samples, 3 threads
cd /tmp/claude-0/gapwf/fin/R4/img/work
B="/opt/venv/bl/bin/python -B scene_r4.py --"
O=r
echo "=== start $(date +%T)"
$B --shot front   --base 0 --tag u --vids B0,B1,B2,B3 --joint v3 --res 900 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot armlook --vids B0,B1,B2,B3 --ppm 10 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot kfront  --arm B0 --kvids K0,K1,K2,K3 --res 640 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot kp34    --arm B0 --kvids K0,K1,K2,K3 --res 640 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot kp34r   --arm B0 --kvids K0,K1,K2,K3 --res 640 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot front   --base 1 --tag w --vids B0 --joint K0,K1,K2,K3 --res 700 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot hero    --vids B0,B1,B2,B3 --joint v3 --res 900 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
echo "ALL DONE $(date +%T)"
