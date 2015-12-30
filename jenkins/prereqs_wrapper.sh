#!/bin/bash

# Usage: $0 build-venv [dir]
#   Create a venv that others can rely on with the documented prereqs.
# Usage: $0 bayeslite bdbcontrib ./check.sh args
#   Use vanilla crosscat and bayeslite-apsw because they are not listed,
#   but use bayeslite and bdbcontrib at HEAD when running ./check.sh args
HOME=/var/lib/jenkins
venv_dir="$HOME/0.1.3-prereqs-venv"

export PS1="Needed for venv activate."
set -eux

if [ "build-venv" == "$1" ]; then
  if [ -n "$2" ]; then
    venv_dir=$2
  fi
  virtualenv $venv_dir
  . $venv_dir/bin/activate
  # Install these first, because crosscat's setup.py fails if these aren't
  # present beforehand:
  pip install --no-cache-dir cython numpy==1.8.2 matplotlib==1.4.3 scipy
  pip install --no-cache-dir bayeslite-apsw --install-option="fetch" --install-option="--sqlite" --install-option="--version=3.9.2"
  pip install --no-cache-dir bdbcontrib

  pip --no-cache-dir install mock pytest # tests_require
  pip --no-cache-dir install pillow --global-option="build_ext" --global-option="--disable-jpeg" # tests_require
  exit 0
fi

. $venv_dir/bin/activate
WORKSPACE=$HOME/workspace

pythenvs="PYTHONPATH=$venv_dir/lib/python2.7/site-packages:${PYTHONPATH:-}"
while [ -n "$1" ]; do
    if [ "crosscat" == "$1" ]; then
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

$pythenvs $*

