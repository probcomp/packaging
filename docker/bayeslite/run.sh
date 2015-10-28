#!/bin/bash

set -ex

docker build -t bayeslite .
# Delete it when it exists, keep it on a terminal and attached.
docker run --rm -i -t -p 8888:8888 bayeslite
