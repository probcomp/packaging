#!/bin/bash

set -ex

docker build -t bayeslite .
docker run -p 8888 -t bayeslite
