FROM 		fedora
MAINTAINER 	Nick Brown "ncbrown@engineering.ucsb.edu"

RUN yum -y update
RUN yum -y install python-pip python-devel gcc
RUN yum -y install openssl-devel mysql-devel
RUN mkdir ~/timeclock
RUN pip install django MySQL-python Pillow django-widget-tweaks flup httplib2 requests simplejson wsgiref django-secure django-sslserver
ADD timeclock /timeclock
RUN python /timeclock/manage.py collectstatic --noinput
EXPOSE 8000
