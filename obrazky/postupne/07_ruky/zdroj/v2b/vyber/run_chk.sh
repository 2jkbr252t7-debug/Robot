#!/bin/bash
cd /tmp/claude-0/gapwf/fin/R2c/vyber/B1c
for s in L R; do /opt/venv/cad/bin/python chk.py B1 $s > J_chk_B1_$s.log 2>&1; /opt/venv/cad/bin/python paths.py B1 $s > J_paths_B1_$s.log 2>&1; done
cd /tmp/claude-0/gapwf/fin/R2c/vyber/B2c
for s in L R; do /opt/venv/cad/bin/python chk.py B2 $s > J_chk_B2_$s.log 2>&1; /opt/venv/cad/bin/python paths.py B2 $s > J_paths_B2_$s.log 2>&1; done
echo done > /tmp/claude-0/gapwf/fin/R2c/vyber/run_chk.done
