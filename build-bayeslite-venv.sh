#!/bin/sh
home=`dirname $0`
exec python $home/build_venv.py $@
