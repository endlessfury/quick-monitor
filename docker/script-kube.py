from kubernetes import client, config
import os
import re

monitoredNamespace = "cfhd"
appVersion = "x.x.x"
chartInfo = "dsada x.x.x"

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

def fetchDeploymentsWithStatus() -> []:
    api_instance = client.AppsV1Api()
    deployments = api_instance.list_namespaced_deployment(monitoredNamespace)
    deployments_all = []
    for deployment in deployments.items:
        #print("%s\t%s\t%s" % (deployment.metadata.name, deployment.status.available_replicas, deployment.status.replicas))
        if deployment.status.replicas == 0:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "DISABLED"})
        elif deployment.status.unavailable_replicas == 1 and deployment.status.replicas == 1:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.replicas - deployment.status.unavailable_replicas,"replicas":deployment.status.replicas, "status": "NOK (0/" + str(deployment.status.replicas) +")"})
        elif deployment.status.available_replicas:
            if deployment.status.available_replicas < deployment.status.replicas:
                deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "NOK (" + str(deployment.status.available_replicas) + "/" + str(deployment.status.replicas) +")"})
            elif deployment.status.available_replicas == deployment.status.replicas:
                deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "OK"})
        elif deployment.status.unavailable_replicas:
            deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.replicas - deployment.status.unavailable_replicas,"replicas":deployment.status.replicas, "status": "NOK (" + str(deployment.status.replicas - deployment.status.unavailable_replicas) + "/" + str(deployment.status.replicas) +")"})
        elif deployment.status.available_replicas == deployment.status.replicas:
                deployments_all.append({"name":deployment.metadata.name,"areplicas":deployment.status.available_replicas,"replicas":deployment.status.replicas, "status": "OK"})
    return deployments_all

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
                                    <th colspan="3">Quick Monitor - Chart version: """ + chartInfo + """, App version: """ + appVersion + """</th>
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
                            <td>{deployment['name']}</td>
                            <td>{listPathsOfService(deployment['name'], ingresses)}</td>
                            <td>{deployment['status']}</td>
                        </tr>""" 
        elif re.search('^NOK.*', deployment['status']):
            content +=f"""
                        <tr class="nok">
                            <td>{deployment['name']}</td>
                            <td>{listPathsOfService(deployment['name'], ingresses)}</td>
                            <td>{deployment['status']}</td>
                        </tr>"""
        elif re.search('^DISABLED.*', deployment['status']):
            content +=f"""
                        <tr class="disabled">
                            <td>{deployment['name']}</td>
                            <td>{listPathsOfService(deployment['name'], ingresses)}</td>
                            <td>{deployment['status']}</td>
                        </tr>"""

        
        
    content +=f'''
                        </table><br>
                        Credits: Wojciech Olszewski
                    </div>
                </body>
            </html>'''

    return content

deployments=fetchDeploymentsWithStatus()
ingresses=fetchIngressPaths()
#print(listPathsOfService("asinventoryservices", ingresses))

output = generateHTML(deployments,ingresses)

input = open(f"deployments.html","w", encoding="UTF-8")
input.write(output)
input.close()