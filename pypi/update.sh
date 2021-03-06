#!/bin/bash
set -Ceu

cmd=$1
if [ $# != 0 ]; then
    targets=$@
else
    targets="crosscat bayeslite bdbcontrib"
fi

TWINE_CONFIG="$HOME/.gnupg/pypirc"
function ensure_prerequisites() {
    set -Ceu
    for prog in gpg openssl git python perl date grep twine tar; do
        if [ ! -x "`which $prog`" ]; then
            echo "Need $prog to proceed."
            exit 1
        fi
    done
    if [ ! -r "$TWINE_CONFIG" ]; then
        echo "Could not read twine security config file $TWINE_CONFIG."
        exit 1
    fi
}

function ensure_current_copyright() {
    set -Ceu
    # Confirm copyright date has the current year.
    year=`date +%Y`
    copywrong=`git grep -i copyright | grep " MIT " | grep -v "2010-$year" || true`
    if [ -n "$copywrong" ]; then
        echo $copywrong
        echo "Copyright year is out-of-date."
        echo "See http://github.com/probcomp/bayeslite/issues/322"
        exit 1
    fi
}

function git_get_latest_version() {
    # Get the list of annotated tags sorted by their dates
    git for-each-ref --sort='*authordate' --format='%(tag)' refs/tags \
        | tail -1 | sed 's/^v//'
    # Take the last one, and chop off the initial v because it is used elsewhere
    # without it.
}

function git_destructive_update() {
    set -Ceu
    ver=$1
    git reset --hard
    git checkout master
    git pull
    if [ -z "$ver" ]; then
        ver=`git_get_latest_version`
    fi
    git checkout v$ver
}


function forced_update_version_patch() {
    set -Ceu
    version_patch=$1
    gz=dist/$pkg-$ver.tar.gz
    for gzf in $gz.*; do
        newname=`echo "$gzf" | sed "s/-$ver/-$ver$version_patch/"`
        mv -f "$gzf" "$newname"
    done
    wheels=dist/$pkg-$ver-*.whl
    mv -f $gz dist/$pkg-$ver$version_patch.tar.gz
    for whl in $wheels; do
        for whlf in $whl*; do
            newname=`echo "$whlf" | sed "s/-$ver/-$ver$version_patch/"`
            mv -f "$whlf" "$newname"
        done
    done
    ver="$ver$version_patch"
}

function build_package_contents() {
    set -Ceu
    pkg=$1
    ver=$2

    python setup.py sdist
    python setup.py bdist_wheel

    gz=dist/$pkg-$ver.tar.gz
    rm -f $gz.asc || true
    gpg --local-user pypi -a --detach-sign $gz
    rm -f $gz.PKG-INFO || true
    tar xzOf $gz `basename $gz .tar.gz`/PKG-INFO > $gz.PKG-INFO
    rm -f $gz.md5 || true
    openssl dgst -md5 < $gz > $gz.md5

    wheels=dist/$pkg-$ver-*.whl
    for whl in $wheels; do
        rm -f $whl.asc || true
        gpg --local-user pypi -a --detach-sign $whl
        rm -f $whl.md5 || true
        openssl dgst -md5 < $whl > $whl.md5
    done

    # Historical wart. We initially named it in camelcase, then
    # lowercased it in the repo, but cannot change the name on pypi
    # without creating a new project.
    if [ -e "CrossCat" ]; then
        perl -i -p -e 's/^Name: crosscat$/Name: CrossCat/' crosscat-*.PKG-INFO
    fi
}

function upload() {
    set -Ceu
    gz=dist/$pkg-$ver.tar.gz
    wheels=dist/$pkg-$ver-*.whl
    twup="twine upload -s -i pypi --config-file $TWINE_CONFIG"
    test -r $gz.asc -a -s $gz.asc
    $twup $gz $gz.asc
    for whl in $wheels; do
        test -r $whl.asc -a -s $whl.asc
        $twup $whl $whl.asc
    done
}

function deploy() {
    entry=$1
    pkg="${entry%%:*}"
    ver="${entry##*:}"
    if [ "$pkg" = "$ver" ]; then
        # There was no colon.
        ver=
    fi
    test -d "$pkg" || git clone "https://github.com/probcomp/$pkg.git" "$pkg"
    (
        set -Ceu
        cd -- "$pkg"
        git_destructive_update "$ver"
        ensure_current_copyright
        build_package_contents "$pkg" "$ver"
        # forced_update_version_patch ".1"
        upload
    )
}

ensure_prerequisites
if [ 'ensure_current_copyright' = $1 -o \
     'git_destructive_update' = $1 -o \
     'build_package_contents' = $1 -o \
     'upload' = $1 ]; then
    fn=$1
    shift
    $fn $@
else
    for entry in $targets; do
        deploy "$entry"
    done
fi
