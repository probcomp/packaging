#!/bin/sh

set -Ceu

usage ()
{

    printf 'Usage: %s' "${0##*/}"
    printf ' [-hn]'
    printf ' [-O <objdir>]'
    printf ' [-d <debdir>]'
    printf ' [-r <repo>]'
    printf ' [-t <tag>]'
    printf '\n'
}

usage_exit ()
{

    usage >&2
    exit ${1+"$@"}
}

help ()
{

    usage
    printf '\n'
    printf '  -h                show help\n'
    printf '  -n                dry run\n'
    printf '  -O <objdir>       build <objdir>/foo_1.23.amd64.deb\n'
    printf '  -d <debdir>       use <debdir>/control, default is .\n'
    printf '  -r <repo>         build from Git repository <repo>\n'
    printf '  -t <tag>          build from Git tag <tag>\n'
    exit
}

run ()
{
    echo -n '#'
    for x in "$@"; do
        if ! expr "x$x" : '^x[-_=./a-z0-9A-Z0-9]*$' >/dev/null; then
            x="'$(printf '%s' "$x" | sed -e "s/'/'\"'\"'/g")'"
        fi
        echo -n '' "$x"
    done
    echo
    [ "x$dryrun" = xyes ] && return 0
    "$@"
}

cleanfilevars=

cleanfile ()
{
    for var in ${1+"$@"}; do
        cleanfilevars="${cleanfilevars:+${cleanfilevars} }${var}"
    done
}

clean ()
{
    for var in $cleanfilevars; do
        eval "cleanfile=\$$var"
        [ -z "$cleanfile" ] && continue
        rm -rf -- "$cleanfile" || :
    done
}

trap clean EXIT HUP INT TERM

# Parse arguments.
dryrun=no
objdir=
debdir=.
repo=
tag=
while getopts O:d:hnr:t: flag; do
    case $flag in
        n)      dryrun=yes;;
        O)      objdir=$OPTARG;;
        d)      debdir=$OPTARG;;
        h)      help; exit;;
        r)      repo=$OPTARG;;
        t)      tag=$OPTARG;;
        \?)     usage_exit 1;;
    esac
done
shift $((OPTIND - 1))
errors=0

# No more arguments allowed.
if [ $# -ne 0 ]; then
    errors=$((errors + 1))
fi

# Make sure the requisite arguments were specified.
if [ -z "$objdir" ]; then
    printf >&2 '%s: specify -O <objdir>\n' "${0##*/}"
    errors=$((errors + 1))
fi
if [ -z "$repo" ]; then
    printf >&2 '%s: specify -r <repo>\n' "${0##*/}"
    errors=$((errors + 1))
fi

if [ $errors -gt 0 ]; then
    usage_exit 1
fi

# Make sure we look like we're in a sane environment.
if [ ! -f "${debdir}/changelog" ]; then
    printf >&2 '%s: missing changelog\n' "${0##*/}"
    printf >&2 '%s: wrong -d <debdir>?\n' "${0##*/}"
    exit 1
fi

# Grab the name and version and assemble some filenames.
pkg=`dpkg-parsechangelog --file "${debdir}/changelog" --show-field source`
debversion=`dpkg-parsechangelog --file "${debdir}/changelog" \
    --show-field version`
version="${debversion%-*}"
pkg_ver="${pkg}-${version}"
pkg_tgz="${pkg}_${version}.orig.tar.gz"
builddep_pkg="${pkg}-build-deps"

# If the user provided no tag, default is `v<version>'.
if [ -z "$tag" ]; then
    tag="v${version}"
fi
if ! git -C "$repo" rev-parse --quiet --verify --revs-only "$tag" >/dev/null
then
    printf >&2 '%s: no such tag: %s\n' "${0##*/}" "$tag"
    exit 1
fi
printf '# # Tag: %s\n' "$tag"

# Make sure the objdir exists.
[ -d "$objdir" ] || run mkdir -- "$objdir"

# Make a temporary directory, clean on exit.
tmpdir=
cleanfile tmpdir
tmpdir=`mktemp -d -p "${TMPDIR:-/tmp}" probcomp-build.XXXXXX`

# Check out the repository into the .orig.tar.gz tarball.
git -C "$repo" archive --format=tar --prefix="${pkg_ver}/" -- "$tag" \
| gzip -c -n > "${tmpdir}/${pkg_tgz}"

# Extract the tarball and create the Debian directory.
tar -C "$debdir" -c -f - . \
| (
    set -Ceu
    cd -- "$tmpdir"
    gunzip -c < "./${pkg_tgz}" | tar xf -
    mkdir "./${pkg_ver}/debian"
    tar -C "./${pkg_ver}/debian" -x -f -
)

# Create a build dependencies package.
(
    set -Ceu
    cd -- "$tmpdir"
    run mk-build-deps "./${pkg_ver}/debian/control"
)

# Build the package with pbuilder.
(
    set -Ceu
    cd -- "${tmpdir}/${pkg_ver}"
    run pdebuild --use-pdebuild-internal \
	--debbuildopts -uc --debbuildopts -us --debbuildopts -F \
	--buildresult "$tmpdir" \
	-- --debug
)

# Stash it away.
run mv -- "${tmpdir}/${pkg}_${debversion}_"*.build "${objdir}/."
run mv -- "${tmpdir}/${pkg}_${debversion}_"*.changes "${objdir}/."
run mv -- "${tmpdir}/${pkg}_${debversion}_"*.deb "${objdir}/."

# Stash the build dependencies package away.
run mv -- "${tmpdir}/${builddep_pkg}_${debversion}_"*.deb "${objdir}/."

# Stash the source package too.
run mv -- "${tmpdir}/${pkg}_${debversion}.debian.tar.gz" "${objdir}/."
run mv -- "${tmpdir}/${pkg}_${debversion}.dsc" "${objdir}/."
run mv -- "${tmpdir}/${pkg}_${version}.orig.tar.gz" "${objdir}/."
