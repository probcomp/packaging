#!/bin/sh

set -Ceu

usage ()
{

    printf >&2 'Usage: %s' "${0##*/}"
    printf >&2 ' [-Pn]'
    printf >&2 ' [-O <objdir>]'
    printf >&2 ' [-d <debdir>]'
    printf >&2 ' [-r <repo>]'
    printf >&2 ' [-t <tag>]'
    printf >&2 '\n'
    exit ${1+"$@"}
}

run ()
{
    echo -n '#'
    for x in "$@"; do
        if ! expr "x$x" : '^x[-=./a-z0-9A-Z0-9]*$' >/dev/null; then
            x="'$(printf '%s' "$x" | sed -e "s/'/'\"'\"'/g")'"
        fi
        echo -n '' "$x"
    done
    echo
    [ "x$dryrun" = xyes ] && return 0
    "$@"
}

cleanfilevars=
cleanpkgvars=

cleanfile ()
{
    for var in ${1+"$@"}; do
        cleanfilevars="${cleanfilevars:+${cleanfilevars} }${var}"
    done
}

cleanpkg ()
{
    for var in ${1+"$@"}; do
        cleanpkgvars="${cleanpkgvars:+${cleanpkgvars} }${var}"
    done
}

clean ()
{
    for var in $cleanfilevars; do
        eval "cleanfile=\$$var"
        [ -z "$cleanfile" ] && continue
        rm -rf -- "$cleanfile" || :
    done
    for var in $cleanpkgvars; do
        eval "cleanpkg=\$$var"
        [ -z "$cleanpkg" ] && continue
        run sudo apt-get remove --auto-remove --purge --yes "$cleanpkg" || :
    done
}

trap clean EXIT HUP INT TERM

# Parse arguments.
pycrap=no
dryrun=no
objdir=
debdir=.
repo=
tag=
while getopts O:Pd:nr:t: flag; do
    case $flag in
        P)      pycrap=yes;;
        n)      dryrun=yes;;
        O)      objdir=$OPTARG;;
        d)      debdir=$OPTARG;;
        r)      repo=$OPTARG;;
        t)      tag=$OPTARG;;
        \?)     usage 1;;
    esac
done
shift $((OPTIND - 1))

# No more arguments allowed.
if [ $# -ne 0 ]; then
    usage 1
fi

# Make sure the requisite arguments were specified.
if [ -z "$objdir" ]; then
    printf >&2 '%s: specify -O <objdir>\n' "${0##*/}"
    usage 1
fi
if [ -z "$repo" ]; then
    printf >&2 '%s: specify -r <repo>\n' "${0##*/}"
    usage 1
fi

# Make sure we look like we're in a sane environment.
if [ ! -f "${debdir}/changelog" ]; then
    printf >&2 '%s: missing changelog\n' "${0##*/}"
    printf >&2 '%s: wrong -d <debdir>?\n' "${0##*/}"
    exit 1
fi

# Make sure the objdir exists.
case $objdir in
    */*)
        objdirp=${objdir%/*}
        objdirn=${objdir##*/}
        (set -Ceu && cd -- "$objdirp" && mkdir -p -- "$objdirn")
        ;;
    *)
        mkdir -p -- "$objdir"
esac

# Grab the name and version and assemble some filenames.
pkg=`dpkg-parsechangelog --file "${debdir}/changelog" --show-field source`
debversion=`dpkg-parsechangelog --file "${debdir}/changelog" \
    --show-field version`
version="${debversion%-*}"
pkg_ver="${pkg}-${version}"
pkg_tgz="${pkg}_${version}.orig.tar.gz"

# If the user provided no tag, default is `v<version>'.
if [ -z "$tag" ]; then
    tag="v${version}"
fi
if ! git -C "$repo" rev-parse --quiet --verify --revs-only "$tag" >/dev/null
then
    printf >&2 '%s: no such tag: %s\n' "${0##*/}" "$tag"
    exit 1
fi

# Make a temporary directory, clean on exit.
tmpdir=
cleanfile tmpdir
tmpdir=`mktemp -d -p "${TMPDIR:-/tmp}" probcomp-build.XXXXXX`

# Determine whether we have to do Python sdist crap.
if [ "x$pycrap" = xyes ]; then
    # Check out the repository, run `python setup.py sdist', and
    # extract the resulting source distribution.
    (
        set -Ceu
        cd -- "$repo"
        git archive --format=tar -- "$tag"
    ) | (
        set -Ceu
        cd -- "$tmpdir"
        mkdir pycrap
        (
            set -Ceu
            cd pycrap
            tar xf -
            python setup.py sdist
            fullname=`python setup.py --fullname | tail -1`
            cd dist
            gunzip -c < "${fullname}.tar.gz" | tar xf -
            mv -- "$fullname" "${tmpdir}/${pkg_ver}"
        )
    )
else
    # Just check out the repository.
    (
        set -Ceu
        cd -- "$repo"
        git archive --format=tar --prefix="${pkg_ver}/" -- "$tag"
    ) | (
        set -Ceu
        cd -- "$tmpdir"
        tar xf -
    )
fi

# Create a debian directory in the source.
(
    set -Ceu
    cd -- "$debdir"
    tar cf - .
) | (
    set -Ceu
    cd -- "$tmpdir"
    mkdir "./${pkg_ver}/debian"
    (
        set -Ceu
        cd "./${pkg_ver}/debian"
        tar xf -
    )
    tar cf - -- "$pkg_ver" | gzip -c > "$pkg_tgz"
)

# Create a build dependencies package.
(
    set -Ceu
    cd -- "$tmpdir"
    run mk-build-deps "./${pkg_ver}/debian/control"
)

# Get ready to clean up the build dependencies package.
builddep="${pkg}-build-deps"
cleanpkg builddep

# Install the build dependencies package install any dependencies.
(
    set -Ceu
    cd -- "$tmpdir"
    run sudo sh -c 'dpkg -i "$1" || :' -- "./${builddep}_${debversion}_all.deb"
    run sudo apt-get install --fix-broken --yes
)

# Finally, build the package.
(
    set -Ceu
    cd -- "$tmpdir"
    cd "./${pkg_ver}"
    run debuild -uc -us
)

# And stash it and its build dependencies away.
run mv -- "${tmpdir}/${builddep}_${debversion}_"* "${objdir}/."
run mv -- "${tmpdir}/${pkg}_${debversion}_"* "${objdir}/."
