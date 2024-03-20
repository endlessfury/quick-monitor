#!/bin/bash
cd /usr/sbin/
./nginx

APISERVER=https://kubernetes.default.svc && SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount && NAMESPACE=$(cat ${SERVICEACCOUNT}/namespace) && TOKEN=$(cat ${SERVICEACCOUNT}/token) && CACERT=${SERVICEACCOUNT}/ca.crt

while :
do
	python3 /root/script.py
	cp -f /root/deployments.html /var/www/html/index.html	
	sleep ${CYCLE_SLEEP}
done
