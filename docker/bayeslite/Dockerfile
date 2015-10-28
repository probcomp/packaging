FROM        ubuntu:14.04.3
ENV DEBIAN_FRONTEND noninteractive

MAINTAINER  Richard Tibbetts

RUN         apt-get update
RUN         apt-get install -y cython \
	    	    	    libboost1.54-all-dev \
	    	    	    python2.7-dev \
	    	    	    python-matplotlib \
			    python-pandas \
			    python-pip \
			    python-scipy

# crosscat expects numpy and cython installed before it gets built, it
# doesn't manage to get the dependencies right.
RUN	    pip install crosscat
RUN         pip install bayeslite bdbcontrib

WORKDIR /baysedb
EXPOSE 8888

CMD	bayesdb-demo

