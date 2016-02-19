# Dockerfile that builds, installs, and tests bayeslite. It is for development
# only; users should use the python package.

FROM        ubuntu:15.10
RUN         apt-get update -qq

# Installation dependencies:
RUN apt-get install -y -qq python2.7-dev python-pip git apt-utils pkg-config libfreetype6-dev liblapack-dev gfortran
RUN pip install setuptools virtualenv

# Required Bayeslite dependencies:
RUN apt-get install -y -qq libboost-dev

WORKDIR /bayesdb
RUN     pip -q install ipython[notebook]==3.2.1 cython numpy==1.8.2 matplotlib==1.4.3 scipy pandas
RUN     BOOST_ROOT=/usr/include pip -q install crosscat
RUN     pip -q install bdbcontrib

WORKDIR /bayesdb/demo
RUN     bayesdb-demo fetch
EXPOSE 8888
LABEL version="0.1.7"
CMD	echo 'Notebook URL: http://`docker-machine ip default`:8888/' && \
    ipython notebook --port=8888 --ip=0.0.0.0 --no-browser
