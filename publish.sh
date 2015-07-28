#!/bin/sh

set -Ceu

usage ()
{

    printf 'Usage: %s' "${0##*/}"
    printf ' [-n]'
    printf ' [-O <objdir>]'
    printf ' [-b <basedir>]'
    printf ' [-c <codename>]'
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
    printf '  -O <objdir>       publish <objdir>/foo_1.23.amd64.deb\n'
    printf '  -b <basedir>      base of repository to publish to\n'
    printf '  -c <codename>     codename of OS release, e.g. `trusty'\''\n'
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

basedir=
codename=
dryrun=no
objdir=
while getopts O:b:c:hn flag; do
    case $flag in
        b)      basedir=$OPTARG;;
        c)      codename=$OPTARG;;
        n)      dryrun=yes;;
        O)      objdir=$OPTARG;;
        h)      help; exit;;
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
if [ -z "$basedir" ]; then
    printf >&2 '%s: specify -b <basedir>\n' "${0##*/}"
    errors=$((errors + 1))
fi
if [ -z "$codename" ]; then
    printf >&2 '%s: specify -c <codename>\n' "${0##*/}"
    errors=$((errors + 1))
fi

if [ $errors -gt 0 ]; then
    usage_exit 1
fi

for changes in "$objdir"/*.changes; do
    run reprepro -V -b "$basedir" include "$codename" "$changes"
done
for dsc in "$objdir"/*.dsc; do
    run reprepro -V -b "$basedir" includedsc "$codename" "$dsc"
done
for deb in "$objdir"/*.deb; do
    run reprepro -V -b "$basedir" includedeb "$codename" "$deb"
done
