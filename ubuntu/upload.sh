#!/bin/sh

set -Ceux

: ${HOST:=probcomp-1.csail.mit.edu}
: ${WWW:=/afs/csail/proj/probcomp/www}
: ${OS:=ubuntu-prerelease}
: ${DATE:=`date +%Y%m%dT%H%M%SZ`}

if ! [ -f conf/distributions -a -d db -a -d dists -a -d pool ]; then
    printf >&2 'enter reprepro directory first\n'
    exit 1
fi

ssh "$HOST" mkdir "${WWW}/${OS}/${DATE}"
rsync ${1+"$@"} -avzHc --delete --copy-dest=../current . \
    "${HOST}:${WWW}/${OS}/${DATE}"
ssh "$HOST" ln -Tfsv "$DATE" "${WWW}/${OS}/current"
