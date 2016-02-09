# Dockerfile that builds, installs, and tests bayeslite. It is for development
# only; users should use the python package.

FROM        ubuntu:15.10
RUN         apt-get update -qq

# Installation dependencies:
RUN apt-get install -y -qq python2.7-dev python-pip git apt-utils pkg-config
RUN pip install setuptools virtualenv

# Required Bayeslite dependencies:
RUN apt-get install -y -qq libboost-dev
# Nice-to-have (pip would install them, but this is faster):
RUN apt-get install -y -qq python-matplotlib python-numpy python-scipy python-pandas python-sklearn

WORKDIR /bayesdb
RUN     pip -q install ipython[notebook]==3.2.1 cython
RUN     BOOST_ROOT=/usr/include pip -q install crosscat
RUN     pip -q install bdbcontrib

WORKDIR /bayesdb/demo
RUN         bayesdb-demo fetch
EXPOSE 8888
CMD	ipython notebook --port=8888 --ip=0.0.0.0 --no-browser
