import os
import re
import requests
import json

class ClusterObject():
    name: str
    replicas: int
    available_replicas: int
    unavailable_replicas: int
    ready_replicas: int
    status: str
    image: str
    ingress_paths: list[str]
    type: str
    
    def __init__(self, name, type, replicas, available_replicas, unavailable_replicas, ready_replicas, image, ingress_paths):
        self.name = name
        self.type = type
        self.replicas = replicas
        self.unavailable_replicas = unavailable_replicas
        self.available_replicas = available_replicas 
        self.ready_replicas = ready_replicas
        self.image = image
        self.ingress_paths = ingress_paths
        self.calculate_status()

    def calculate_status(self):
        if self.replicas == 0:
            self.status = "DISABLED"
        elif self.unavailable_replicas != 0 or self.available_replicas == 0:
            self.status = f"NOK (%d/%d)" % (self.available_replicas, self.replicas)
        elif self.available_replicas == self.replicas:
                self.status = "OK"
        else:
            self.status = f"NOK ?"

monitoredNamespace = os.getenv('monitoredNamespace')
appVersion = os.getenv('appVersion')
chartInfo = os.getenv('chartInfo')
# export APISERVER=https://kubernetes.default.svc && export SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount && export NAMESPACE=$(cat ${SERVICEACCOUNT}/namespace) && export TOKEN=$(cat ${SERVICEACCOUNT}/token) && export CACERT=${SERVICEACCOUNT}/ca.crt
apiserver = "https://kubernetes.default.svc"
ca_cert_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
token = open("/var/run/secrets/kubernetes.io/serviceaccount/token").read()

def fetchObjects() -> []:
    unsortedObjects = []
    # curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" -X GET ${APISERVER}/apis/apps/v1/deployments | jq -r '.items[] | .metadata.name, .status.replicas, .status.availableReplicas, .status.unavailableReplicas, .status.readyReplicas, .spec.template.spec.containers[0].image'

    # # test only
    # f = open('deploymentList.json')
    # deployment_objects = json.load(f)
    # i = open('ingressList.json')
    # ingress_objects = json.load(i)

    deployment_request = requests.get(f"{apiserver}/apis/apps/v1/namespaces/{monitoredNamespace}/deployments", verify=f"{ca_cert_path}", headers={"Authorization" : f"Bearer {token}"})
    statefulset_request = requests.get(f"{apiserver}/apis/apps/v1/namespaces/{monitoredNamespace}/statefulsets", verify=f"{ca_cert_path}", headers={"Authorization" : f"Bearer {token}"})

    deployment_objects = json.loads(deployment_request.text)
    statefulset_objects = json.loads(statefulset_request.text)
    
    for item in deployment_objects['items']:
        name = item['metadata'].get("name","empty_name")
        replicas = int(item['status'].get("replicas","0"))
        available_replicas = int(item['status'].get("availableReplicas","0"))
        unavialable_replicas = int(item['status'].get("unavailableReplicas","0"))
        ready_replicas = int(item['status'].get("readyReplicas","0"))
        image = item['spec']['template']['spec']['containers'][0].get("image","empty_image")
        ingress_paths = getIngressPaths(name)
        unsortedObjects.append(ClusterObject(name, "deployment", replicas, available_replicas, unavialable_replicas, ready_replicas,image, ingress_paths))
        
    for item in statefulset_objects['items']:
        name = item['metadata'].get("name","empty_name")
        replicas = int(item['status'].get("replicas","0"))
        available_replicas = int(item['status'].get("availableReplicas","0"))
        unavialable_replicas = int(item['status'].get("unavailableReplicas","0"))
        ready_replicas = int(item['status'].get("readyReplicas","0"))
        image = item['spec']['template']['spec']['containers'][0].get("image","empty_image")
        ingress_paths = getIngressPaths(name)
        unsortedObjects.append(ClusterObject(name, "deployment", replicas, available_replicas, unavialable_replicas, ready_replicas,image, ingress_paths))

    return sortObjects(unsortedObjects)

def sortObjects(objects_not_sorted) -> []:
    objects_sorted = []
    for object in objects_not_sorted:
        if re.search('^NOK.*', object.status):
            objects_sorted.append(object)
        elif re.search('^DISABLED.*', object.status):
            objects_sorted.insert(0,object)
    for object in objects_not_sorted:
        if re.search('^OK$', object.status):
            objects_sorted.append(object)
    return objects_sorted

def getIngressPaths(name) -> []:
    ingresse_request = requests.get(f"{apiserver}/apis/networking.k8s.io/v1/namespaces/{monitoredNamespace}/ingresses", verify=f"{ca_cert_path}", headers={"Authorization" : f"Bearer {token}"})
    ingress_objects = json.loads(ingresse_request.text)

    ingress_paths = []

    for item in ingress_objects['items']:
        if item['metadata']['name'] == name:
            for ingress_path in item['spec']['rules'][0]['http']['paths']:
                ingress_paths.append(ingress_path['path'])
    
    return ingress_paths

def listIngressPaths(ingress_paths) -> str:
    return_string: str = f""
    for path in ingress_paths:
        return_string += "%s<br>" % (path)
    return return_string

def generateHTML(objects) -> str:
    content: str = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>Quick monitor</title>
        <style>
            *
            {{
                margin: 0;
                padding: 0;
                font-size:100%;
                font-family: Arial;
            }}
            body
            {{
                background-color: gray;
            }}
            h1
            {{
                text-align: center;
                font-size: 150%;
                padding-top: 1em;
            }}
            .tableDiv
            {{
                #width: 80%;
                display: grid;
                grid-template-rows: 1fr;
                grid-template-columns: 1fr;
                justify-items:center;
                margin-top: 1em;
                margin-bottom: 1em;
                overflow-x: auto;
                overflow-y: auto;
                border-radius: 25px;
                margin-left: auto;
                margin-right: auto;
            }}

            
            #imageDiv
            {{
                font-size: 70%;
                border: 0px;
                padding: 0;
            }}

            table 
            {{
                grid-row-start: 1;
                grid-row-end: 2;
                grid-column-start: 1;
                grid-column-end: 1;
                border-collapse: collapse;
            }}
            
            table *
            {{
                border: 1px solid black;
                padding: 1em;
                word-break: break-word;
            }}

            table th
            {{
                background-color: darkgray;
            }}
            
            table tr.ok
            {{
                background-color: #98FB98;
            }}

            table tr.nok
            {{
                background-color: #DC143C;
                color: #F0FFFF;
            }}

            table tr.disabled
            {{
                background-color: #FFA500;
            }}
        </style>
    </head>
    <body>
    <div class="tableDiv">
                            <table>
                                <tr>
                                    <th colspan="3">Monitored namespace: """ + monitoredNamespace + """</th>
                                </tr>
                                <tr>
                                    <th>Deployment</th>
                                    <th>ingressPaths</th>
                                    <th>Status</th>
                                </tr>
"""
    
    for object in objects:
        if re.search('^OK$', object.status):
            content +=f"""
                        <tr class="ok">
                            <td>{object.name}<div id="imageDiv">{object.image.split("/")[-1]}</div></td>
                            <td>{listIngressPaths(object.ingress_paths)}</td>
                            <td>{object.status}</td>
                        </tr>""" 
        elif re.search('^NOK.*', object.status):
            content +=f"""
                        <tr class="nok">
                            <td>{object.name}<div id="imageDiv">{object.image.split("/")[-1]}</div></td>
                            <td>{listIngressPaths(object.ingress_paths)}</td>
                            <td>{object.status}</td>
                        </tr>"""
        elif re.search('^DISABLED.*', object.status):
            content +=f"""
                        <tr class="disabled">
                            <td>{object.name}<div id="imageDiv">{object.image.split("/")[-1]}</div></td>
                            <td>{listIngressPaths(object.ingress_paths)}</td>
                            <td>{object.status}</td>
                        </tr>"""

        
        
    content +=f"""
                        </table><br>
                        <div id="imageDiv">Chart version: """ + chartInfo + """, App version: """ + appVersion + """</div><br>
                        Credits: Wojciech Olszewski
                    </div>
                </body>
            </html>"""

    return content


objects = fetchObjects()
output = generateHTML(objects)

input = open(f"/root/deployments.html","w", encoding="UTF-8")
#input = open(f"deployments.html","w", encoding="UTF-8")
input.write(output)
input.close()