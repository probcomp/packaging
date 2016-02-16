#!/bin/bash

if [ -z "`which virtualenv`" ]; then
    echo "We need pip and virtualenv already installed."
    echo "See https://pip.pypa.io/en/stable/installing/ for pip."
    echo "Once you have that, 'pip install virtualenv' should work."
    exit 1
fi

venv_dir=$1
install_version=$2

if [ -d "$venv_dir" -a ! -r "$venv_dir/bin/activate" ]; then
    echo "$venv_dir exists, but does not seem to be a virtualenv."
    echo "  Please choose a different path, move it out of the way, or"
    echo "  create it with virtualenv."
    exit 1
fi

if [ ! -d "$venv_dir" ]; then
    echo "Building a virtualenv directory at [$1]"
    virtualenv $venv_dir
fi

if [ -z "`$venv_dir/bin/python -V 2>&1 | grep ' 2.7'`" ]; then
    echo "Although we've started to look at Python 3, BayesDB is not yet"
    echo "Python 3 compatible. Please use a Python 2.7 instead."
    exit 1
fi


set -eu

export PS1="Virtualenv activate needs a PS1 (prompt string) to munge."
. $venv_dir/bin/activate
# Install these first, because crosscat's setup.py fails if these aren't
# present beforehand:
pip install --no-cache-dir cython numpy==1.8.2 matplotlib==1.4.3 scipy pandas
pip install ipython==3.2.1
pip install --no-cache-dir bayeslite-apsw --install-option="fetch" --install-option="--sqlite" --install-option="--version=3.9.2"
if [ "" = "$install_version" -o "latest" = "$install_version" ]; then
    pip install --no-cache-dir bdbcontrib
elif [ "head" = "$install_version" -o "HEAD" = "$install_version" ]; then
    mkdir -p $venv_dir/sources/
    for repo in crosscat bayeslite bdbcontrib; do
        git clone http://github.com/probcomp/$repo $venv_dir/sources/$repo
        ( cd -- $venv_dir/sources/$repo && pip install . )
    done
else
    pip install --no-cache-dir bdbcontrib==$install_version
fi

# Requirements for testing.
pip --no-cache-dir install mock pytest flaky # tests_require
pip --no-cache-dir install pillow --global-option="build_ext" --global-option="--disable-jpeg" # tests_require
pip --no-cache-dir install jupyter ipython[notebook] runipy

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
