#!/bin/bash
cd /usr/sbin/
./nginx

APISERVER=https://kubernetes.default.svc && SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount && NAMESPACE=$(cat ${SERVICEACCOUNT}/namespace) && TOKEN=$(cat ${SERVICEACCOUNT}/token) && CACERT=${SERVICEACCOUNT}/ca.crt

while :
do
    curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" -X GET ${APISERVER}/apis/apps/v1/namespaces/$monitoredNamespace/deployments | jq -r '[(.items[] | { name: .metadata.name, replicas: .status.replicas, availableReplicas: .status.availableReplicas })]' > /root/deployments.json 
	python3 /root/generatehtml.py
	cp -f /root/deployments.html /var/www/html/index.html	
	sleep 30
done
