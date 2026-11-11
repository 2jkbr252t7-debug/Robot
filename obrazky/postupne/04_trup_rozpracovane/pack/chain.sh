#!/bin/bash
cd /tmp/claude-0/gapwf/fin/T1/pack
P=/opt/venv/cad/bin/python
$P check_static.py > static.log 2>&1
$P run_sweep.py std > sweep_std.log 2>&1 &
$P run_sweep.py extra > sweep_extra.log 2>&1
wait
$P run_gaps.py > gaps.log 2>&1
$P j1gap.py > j1gap.log 2>&1
$P gaps2.py > gaps2.log 2>&1
$P fix_checks.py > fix_checks.log 2>&1
$P envelope.py > envelope.log 2>&1
$P cog.py > cog.log 2>&1
$P export_prev.py > export.log 2>&1
echo CHAIN_DONE >> export.log
