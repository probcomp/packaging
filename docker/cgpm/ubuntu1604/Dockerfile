FROM            ubuntu:16.04
MAINTAINER      MIT Probabilistic Computing Project

RUN		apt-get update -qq
RUN             apt-get install -qq git
RUN             apt-get install -qq python-matplotlib
RUN             apt-get install -qq python-numpy
RUN             apt-get install -qq python-pandas
RUN             apt-get install -qq python-pytest
RUN             apt-get install -qq python-scipy
RUN             apt-get install -qq python-sklearn

ADD             . /cgpm
WORKDIR         /cgpm
RUN             ./check.sh
