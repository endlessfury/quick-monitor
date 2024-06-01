from kubernetes import client, config
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
    ingressPaths: list[str]
    type: str
    
    def __init__(self, name, type, replicas, available_replicas, unavailable_replicas, ready_replicas, image):
        self.name = name
        self.type = type
        self.replicas = replicas
        self.unavailable_replicas = unavailable_replicas if unavailable_replicas is not None else 0
        self.available_replicas = available_replicas if available_replicas is not None else self.replicas - self.unavailable_replicas
        self.ready_replicas = ready_replicas
        self.image = image
        self.status()

    def status(self):
        if self.replicas == 0:
            self.status = "DISABLED"
        elif self.unavailable_replicas != 0:
            self.status = f"NOK (%d/%d)" % (self.available_replicas, self.replicas)
        elif self.available_replicas == self.replicas:
                self.status = "OK"

monitoredNamespace = os.getenv('monitoredNamespace')
appVersion = os.getenv('appVersion')
chartInfo = os.getenv('chartInfo')
apiserver = os.getenv('APISERVER')
ca_cert_path = os.getenv('CACERT')
token = os.getenv('TOKEN')

# https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md
# config.load_incluster_config()

def fetchObjects() -> []:
    unsortedObjects = []
    # curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" -X GET ${APISERVER}/apis/apps/v1/deployments | jq -r '.items[] | .metadata.name, .status.replicas, .status.availableReplicas, .status.unavailableReplicas, .status.readyReplicas, .spec.template.spec.containers[0].image'

    deployment_request = requests.get(f"{apiserver}/apis/apps/v1/namespaces/{monitoredNamespace}/deployments", verify=f"{ca_cert_path}", headers={"Authorization" : f"Bearer {token}"})
    statefulset_request = requests.get(f"{apiserver}/apis/apps/v1/namespaces/{monitoredNamespace}/statefulsets", verify=f"{ca_cert_path}", headers={"Authorization" : f"Bearer {token}"})

    deployment_objects = json.loads(deployment_request.text)
    statefulset_objects = json.loads(statefulset_request.text)
    
    for item in deployment_objects['items']:
        unsortedObjects.append(ClusterObject(item['metadata'].get("name","empty_name"), "deployment", int(item['status'].get("replicas","0")), int(item['status'].get("availableReplicas","0")), int(item['status'].get("unavailableReplicas","0")), int(item['status'].get("readyReplicas","0")),item['spec']['template']['spec']['containers'][0].get("image","empty_image")))
    for item in statefulset_objects['items']:
        unsortedObjects.append(ClusterObject(item['metadata'].get("name","empty_name"), "deployment", int(item['status'].get("replicas","0")), int(item['status'].get("availableReplicas","0")), int(item['status'].get("unavailableReplicas","0")), int(item['status'].get("readyReplicas","0")),item['spec']['template']['spec']['containers'][0].get("image","empty_image")))
    
    return unsortedObjects

def fetchDeploymentsWithStatus() -> []:
    api_instance = client.AppsV1Api()
    deployments = api_instance.list_namespaced_deployment(monitoredNamespace)
    deployments_all = []
    for deployment in deployments.items:
        #print("%s\t%s\t%s" % (deployment.metadata.name, deployment.status.available_replicas, deployment.status.replicas))
        if deployment.status.replicas == 0:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "DISABLED", "image":deployment.spec.template.spec.containers[0].image})
        elif deployment.status.unavailable_replicas == 1 and deployment.status.replicas == 1:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.replicas - deployment.status.unavailable_replicas,"replicas":deployment.status.replicas, "status": "NOK (0/" + str(deployment.status.replicas) +")", "image":deployment.spec.template.spec.containers[0].image})
        elif deployment.status.available_replicas:
            if deployment.status.available_replicas < deployment.status.replicas:
                deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "NOK (" + str(deployment.status.available_replicas) + "/" + str(deployment.status.replicas) +")", "image":deployment.spec.template.spec.containers[0].image})
            elif deployment.status.available_replicas == deployment.status.replicas:
                deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "OK", "image":deployment.spec.template.spec.containers[0].image})
        elif deployment.status.unavailable_replicas:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.replicas - deployment.status.unavailable_replicas,"replicas":deployment.status.replicas, "status": "NOK (" + str(deployment.status.replicas - deployment.status.unavailable_replicas) + "/" + str(deployment.status.replicas) +")", "image":deployment.spec.template.spec.containers[0].image})
        elif deployment.status.available_replicas == deployment.status.replicas:
                deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "OK", "image":deployment.spec.template.spec.containers[0].image})    
    return sortDeployments(deployments_all)

def sortDeployments(deployments_not_sorted) -> []:
    deployments_sorted = []
    for deployment in deployments_not_sorted:
        if re.search('^NOK.*', deployment['status']):
            deployments_sorted.append(deployment)
        elif re.search('^DISABLED.*', deployment['status']):
            deployments_sorted.append(deployment)
    for deployment in deployments_not_sorted:
        if re.search('^OK$', deployment['status']):
            deployments_sorted.append(deployment)
    return deployments_sorted

def fetchIngressPaths() -> []:
    api_instance = client.NetworkingV1Api() # client.<api_group>
    ingresses = api_instance.list_namespaced_ingress(monitoredNamespace)
    ingresses_all = []
    for ingress in ingresses.items:
        #print("Service: %s\tIngressPaths: %s" % (ingress.metadata.name,listPathOfIngresses(ingress.metadata.name)))
        ingresses_all.append({"service": ingress.metadata.name, "ingressPaths": listPathOfIngresses(ingress.metadata.name)})
    return ingresses_all

def listPathOfIngresses(name) -> []:
    api_instance = client.NetworkingV1Api() # client.<api_group>
    ingress = api_instance.read_namespaced_ingress(name, monitoredNamespace)
    paths_all = []
    for path in ingress.spec.rules[0].http.paths:
        #print("%s" % (path.path))
        paths_all.append(path.path)
    return paths_all

def listPathsOfService(name, ingresses) -> str:
    return_string: str = f""
    for deployment in ingresses:
        if name == deployment['service']:
            for path in deployment['ingressPaths']:
                #print("%s<br>" % (path))
                return_string += "%s<br>" % (path)
    return return_string

def generateHTML(deployments, ingresses) -> str:
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
    
    for deployment in deployments:
        if re.search('^OK$', deployment['status']):
            content +=f"""
                        <tr class="ok">
                            <td>{deployment['name']}<div id="imageDiv">{deployment['image'].split("/")[-1]}</div></td>
                            <td>{listPathsOfService(deployment['name'], ingresses)}</td>
                            <td>{deployment['status']}</td>
                        </tr>""" 
        elif re.search('^NOK.*', deployment['status']):
            content +=f"""
                        <tr class="nok">
                            <td>{deployment['name']}<div id="imageDiv">{deployment['image'].split("/")[-1]}</div></td>
                            <td>{listPathsOfService(deployment['name'], ingresses)}</td>
                            <td>{deployment['status']}</td>
                        </tr>"""
        elif re.search('^DISABLED.*', deployment['status']):
            content +=f"""
                        <tr class="disabled">
                            <td>{deployment['name']}<div id="imageDiv">{deployment['image'].split("/")[-1]}</div></td>
                            <td>{listPathsOfService(deployment['name'], ingresses)}</td>
                            <td>{deployment['status']}</td>
                        </tr>"""

        
        
    content +=f"""
                        </table><br>
                        <div id="imageDiv">Chart version: """ + chartInfo + """, App version: """ + appVersion + """</div><br>
                        Credits: Wojciech Olszewski
                    </div>
                </body>
            </html>"""

    return content

# deployments=fetchDeploymentsWithStatus()
# ingresses=fetchIngressPaths()
# #print(listPathsOfService("asinventoryservices", ingresses))

# output = generateHTML(deployments,ingresses)

# input = open(f"/root/deployments.html","w", encoding="UTF-8")
# input.write(output)
# input.close()