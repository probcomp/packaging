#!/bin/bash

set -Ceux

version=${1:-WilyWerewolf}
file=${2:-Dockerfile}
name=${3:-bayeslite-on-15-10}

if [ "$version" == "LTS" ]; then
    name=bayeslite-on-14-04
    file=LTS-Dockerfile
fi

# Build it, or open a terminal on it to help debug why it didn't build.
docker build -t $name -f $file . || docker run -it `docker images | head -2 | tail -1 | awk '{print $3}'` /bin/bash -il

: ${BROWSER:=""}

notebook_url="http://`docker-machine ip default`:8888/"
if [ -n "$BROWSER" ]; then
    $BROWSER "$notebook_url" &
elif [ "Darwin" == "`uname -s`" ]; then
    open "$notebook_url"
else
    echo "The notebook will be available at $notebook_url"
fi

# Keep it on a terminal and attached.
# Do not delete because you might've done work there
#   (or might want to debug a failure).

docker run -it --net=host $name
