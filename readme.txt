minikube kubectl -- apply -n quick -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: quick-monitor
EOF

kubectl apply -n quick -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: quick-monitor-token
  annotations:
    kubernetes.io/service-account.name: quick-monitor
type: kubernetes.io/service-account-token
EOF

kubectl apply -n quick -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: quick-monitor
rules:
  - verbs:
      - '*'
    apiGroups:
      - ''
    resources:
      - pods
      - events
      - "pods/portforward"
  - verbs:
      - 'create'
    apiGroups:
      - ''
    resources:
      - pods/exec
  - verbs:
      - '*'
    apiGroups:
      - ''
    resources:
      - pods/log
  - verbs:
      - get
      - watch
      - list
    apiGroups:
      - apps
    resources:
      - '*'
  - verbs:
      - get
      - watch
      - list
    apiGroups:
      - ''
    resources:
      - configmaps
      - jobs
      - services
      - persistentvolumes
      - persistentvolumeclaims
  - verbs:
      - get
      - watch
      - list
    apiGroups:
      - networking.k8s.io
    resources:
      - ingresses
EOF

kubectl apply -n quick -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: quick-monitor
subjects:
- kind: ServiceAccount
  name: quick-monitor
roleRef:
  kind: Role
  name: quick-monitor
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl get secret quick-monitor-token -o jsonpath='{.data.*}' -n quick | base64 -d 2>/dev/null > /tmp/quick-ca.cert

export KUBE_API_TOKEN=$(kubectl get secret quick-monitor-token -o jsonpath='{.data.token}' -n quick | base64 -d)
export KUBECONFIG=/tmp/quick_monitor_kubeconfig
kubectl config set-cluster quick-cluster --server=https://127.0.0.1:32769 --certificate-authority=/tmp/quick-ca.cert --embed-certs=true
kubectl config set-credentials quick-user --token=$KUBE_API_TOKEN
kubectl config set-context quick --cluster=quick-cluster --namespace=quick --user=quick-user
kubectl config use-context quick


APISERVER=https://kubernetes.default.svc && SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount && NAMESPACE=$(cat ${SERVICEACCOUNT}/namespace) && TOKEN=$(cat ${SERVICEACCOUNT}/token) && CACERT=${SERVICEACCOUNT}/ca.crt

curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" -X GET ${APISERVER}/api/v1/namespaces/kube-system/pods
curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" -X GET ${APISERVER}/api

kubectl auth can-i get pods --as=system:serviceaccount:quick:quick-monitor -n kube-system

curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" -X GET ${APISERVER}/api/v1/namespaces/$monitoredNamespace/deployments

from kubernetes import client, config

# Configs can be set in Configuration class directly or using helper utility
config.load_incluster_config()

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_pod_for_all_namespaces(watch=False)
for i in ret.items:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

git clone --recursive https://github.com/kubernetes-client/python.git
cd python
python setup.py install

https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md

from kubernetes import client, config
import os

monitoredNamespace = os.getenv('monitoredNamespace')

# Configs can be set in Configuration class directly or using helper utility
config.load_incluster_config()

deployments_all = []

v1 = client.AppsV1Api()
print("Listing deployments:")
deployments = v1.list_namespaced_deployment(monitoredNamespace)
for deployment in deployments.items:
    print("%s\t%s\t%s" % (deployment.metadata.name, deployment.status.available_replicas, deployment.status.replicas))
    if deployment.status.replicas == 0:
        deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "DISABLED"})
    elif deployment.status.unavailable_replicas == 1 and deployment.status.replicas == 1:
        deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.replicas - deployment.status.unavailable_replicas,"replicas":deployment.status.replicas, "status": "NOK"})
    elif deployment.status.available_replicas:
        if deployment.status.available_replicas < deployment.status.replicas:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "NOK (" + str(deployment.status.available_replicas) + "/" + str(deployment.status.replicas) +")"})
        elif deployment.status.available_replicas == deployment.status.replicas:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "OK"})
    elif deployment.status.unavailable_replicas:
        deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.replicas - deployment.status.unavailable_replicas,"replicas":deployment.status.replicas, "status": "NOK (" + str(deployment.status.replicas - deployment.status.unavailable_replicas) + "/" + str(deployment.status.replicas) +")"})
    elif deployment.status.available_replicas == deployment.status.replicas:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "OK"})
    print(deployments_all)