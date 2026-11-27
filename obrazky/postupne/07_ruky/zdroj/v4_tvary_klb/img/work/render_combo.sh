#!/bin/bash
# R4 final renders for v4_odporucanie.png: recommended B1 + K3 (today's B0 + K0 close-ups come from render_final.sh, same cameras)
cd /tmp/claude-0/gapwf/fin/R4/img/work
B="/opt/venv/bl/bin/python -B scene_r4.py --"
O=r
echo "=== start $(date +%T)"
$B --shot r01    --vids B1 --joint K3 --deg 0 --pan 15 --res 1100 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot front  --base 1 --tag x --vids B1 --joint K3 --res 800 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot kp34r  --arm B1 --kvids K3 --res 640 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
$B --shot kp34   --arm B1 --kvids K3 --res 640 --samples 48 --exposure -0.3 --out $O 2>&1 | grep -E "SHOT|rror|Traceback"
echo "ALL DONE $(date +%T)"
