#!/bin/bash

set -eu

if [ -z "$1" -o -d "$1" ]; then
    echo "Usage: $0 new_venv_dir"
    echo "That new virtualenv directory cannot already exist. It will be built."
    echo "You must already have python2.7, pip, and virtualenv."
    echo "The new virtualenv will not be relocatable (or renameable), "
    echo "  so put it where you will want it now."
    exit 1
fi

venv_dir=$1

echo "Building a virtual env at [$1]"

virtualenv $venv_dir
export PS1="Virtualenv activate needs a PS1 (prompt string) to munge."
. $venv_dir/bin/activate
# Install these first, because crosscat's setup.py fails if these aren't
# present beforehand:
pip install --no-cache-dir cython numpy==1.8.2 matplotlib==1.4.3 scipy
pip install --no-cache-dir bayeslite-apsw --install-option="fetch" --install-option="--sqlite" --install-option="--version=3.9.2"
pip install --no-cache-dir bdbcontrib

# Requirements for testing.
pip --no-cache-dir install mock pytest # tests_require
pip --no-cache-dir install pillow --global-option="build_ext" --global-option="--disable-jpeg" # tests_require
pip --no-cache-dir install jupyter ipython[notebook]

echo "Installed into $venv_dir!"
echo ""
echo "Next steps:"
echo "  source $venv_dir/bin/activate"
echo "Then you can run the demo:"
echo "  (mkdir bayesdb-demo; cd bayesdb-demo; bayesdb-demo)"
echo "Or start a notebook, and import bayeslite or bdbcontrib."
echo
echo "NOTE: This new virtualenv will not work if you move or rename it."
echo "Please also subscribe to bayesdb-community@lists.csail.mit.edu. Thanks!"
