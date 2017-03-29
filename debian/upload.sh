#!/bin/sh

set -Ceu

: ${HOST:=probcomp-1.csail.mit.edu}
: ${WWW:=/afs/csail/proj/probcomp/www}
: ${OS:=ubuntu}
: ${SUITE:=trusty}
: ${DATE:=`date +%Y%m%d`}

rsync ${1+"$@"} -avzHc --delete --copy-dest=../current . \
    "${HOST}:${WWW}/${OS}/${SUITE}/${DATE}"
ssh "$HOST" ln -Tfsv "$DATE" "${WWW}/${OS}/${SUITE}/current"
