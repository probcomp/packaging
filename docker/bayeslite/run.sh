#!/bin/bash

set -ex

docker build -t bayeslite .
notebook_url="http://`docker-machine ip default`:8888/"
if [ -n "$BROWSER" ]; then
    $BROWSER "$notebook_url"
elif [ "Darwin" == "`uname -s`" ]; then
    open "$notebook_url"
elif which python > /dev/null; then
    python -mwebbrowser "$notebook_url"
else
    echo "The notebook will be available at $notebook_url"
fi
# Delete it when it exists, keep it on a terminal and attached.
docker run --rm -i -t --net=host bayeslite
