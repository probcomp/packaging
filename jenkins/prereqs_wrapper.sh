#!/bin/bash

# Usage: $0 bayeslite bdbcontrib ./check.sh args
#   Use vanilla crosscat and bayeslite-apsw because they are not listed,
#   but use bayeslite and bdbcontrib at HEAD when running ./check.sh args
#   Include a venv directory before your command to use that venv.
HOME=/var/lib/jenkins
venv_dir="$HOME/0.1.3-prereqs-venv"

set -eux

WORKSPACE=$HOME/workspace
pythenvs=
while [ -n "$1" ]; do
    if [ -d "$1" -a -e "$1/bin/activate" ]; then
	venv_dir=$1
    elif [ "crosscat" == "$1" ]; then
	pythenvs="$pythenvs $WORKSPACE/crosscat-tests/pythenv.sh"
    elif [ "bayeslite-apsw" == "$1" ]; then
	pythenvs="$pythenvs $WORKSPACE/bayeslite-apsw-master/pythenv.sh"
    elif [ "bayeslite" == "$1" ]; then
	pythenvs="$pythenvs $WORKSPACE/bayeslite-master-crashes/pythenv.sh"
    elif [ "bdbcontrib" == "$1" ]; then
	pythenvs="$pythenvs $WORKSPACE/bdbcontrib-tests/pythenv.sh"
    else
	break
    fi
    shift
done

export PS1="Needed for venv activate."
. $venv_dir/bin/activate

eval $pythenvs $*

