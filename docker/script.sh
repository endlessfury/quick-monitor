#!/bin/bash

cd /usr/sbin/
./nginx

while :
do
	python3 /root/script.py
	cp -f /root/deployments.html /var/www/html/index.html	
	sleep ${CYCLE_SLEEP}
done
