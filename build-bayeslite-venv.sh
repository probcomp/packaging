#!/bin/sh -Ceux
args="$@"
home=`dirname $0`
python $home/src/build_venv.py $args
