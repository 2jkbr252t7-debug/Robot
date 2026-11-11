#!/bin/bash
cd /tmp/claude-0/gapwf/fin/T1/k2
P=/opt/venv/cad/bin/python
$P gen_layout.py > /dev/null
$P check_static.py > static.log 2>&1
$P envelope.py > envelope.log 2>&1
$P j1gap.py > j1gap.log 2>&1
$P gaps2.py > gaps2.log 2>&1
echo CHAIN4_DONE >> gaps2.log
