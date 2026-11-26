#!/bin/bash
cd /tmp/claude-0/gapwf/fin/R1/img_v2/work
B=/opt/venv/bl/bin/python
run() { echo "=== $1 $(date +%T)"; $B v2_scene.py -- --shot $1 --res $2 --samples $3 --exposure $4 --out final 2>&1 | grep -E "SHOT|closest|failed|Error|error" ; }
run rez 1400 40 -0.2
run front 1500 48 -0.3
run detail 800 48 -0.3
run vnutro 1600 64 0.0
run rozlozene 1800 48 0.0
run hero 1400 64 -0.3
echo "ALL DONE $(date +%T)"
