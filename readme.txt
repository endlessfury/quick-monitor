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