FROM        ubuntu:14.04.3
ENV DEBIAN_FRONTEND noninteractive

MAINTAINER  Richard Tibbetts

RUN         apt-get update
RUN         apt-get install -y cython \
	    	    	    libboost1.54-all-dev \
	    	    	    python2.7-dev \
	    	    	    python-matplotlib \
			    python-pandas \
			    python-pip

# Install scipy from source because sklearn-pandas needs it to come in that way.
RUN	    apt-get build-dep -y python-scipy
RUN	    pip install scipy

RUN	    pip install crosscat
RUN         pip install bayeslite
RUN	    pip install bdbcontrib

WORKDIR /baysedb
EXPOSE 8888

CMD	bayesdb-demo fetch && ipython notebook --ip=0.0.0.0

