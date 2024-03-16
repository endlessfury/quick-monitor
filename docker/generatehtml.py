import json

# Check for the deployment status 0 - something wrong, 1 - all good, 2 - scaled to 0
def check_status(replicas, areplicas) -> int:
    if replicas == 0:
        return 2
    elif areplicas == 0:
        return 1
    elif areplicas % replicas == 0:
        # print(f"""{replicas} {areplicas} {areplicas % replicas}""")
        return 0
    else:
        return 1
    
def generateHTML(data) -> str:
    content: str = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>Deployments status: CFHD</title>
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
                width: 100%;
                display: grid;
                grid-template-rows: 1fr;
                grid-template-columns: 1fr;
                justify-items:center;
                margin-top: 1em;
                margin-bottom: 1em;
                overflow-x: auto;
                overflow-y: auto;
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
                width:33%;
                word-break: break-word;
                background-color: lightgray;
            }}
            table th
            {{
                background-color: darkgray;
            }}
        </style>
    </head>
    <body>
    <div class="tableDiv">
                            <table>
                                <tr>
                                    <th colspan="3">Deployments status</th>
                                </tr>
                                <tr>
                                    <th>Deployment name</th>
                                    <th>Deployment status</th>
                                </tr>
"""
    
    for deployment in data:
        if deployment['status'] == 0:
            status_info: str = "OK"
            content +=f"""
                        <tr>
                            <td style="background-color:lightgrey;">{deployment['name']}</td>
                            <td style="background-color:lightgreen;">{status_info}</td>
                        </tr>"""
        elif deployment['status'] == 1:
            status_info: str = "NOK (" + deployment['areplicas'] + "/" + deployment['replicas'] +")"
            content +=f"""
                        <tr>
                            <td style="background-color:lightgrey;">{deployment['name']}</td>
                            <td style="background-color:red;">{status_info}</td>
                        </tr>"""
        elif deployment['status'] == 2:
            status_info: str = "DISABLED"
            content +=f"""
                        <tr>
                            <td style="background-color:lightgrey;">{deployment['name']}</td>
                            <td style="background-color:darkorange;">{status_info}</td>
                        </tr>"""

        
        
    content +=f'''
                        </table>
                    </div>
                </body>
            </html>'''

    return content



input = open('/root/deployments.json')

deployments_json_data = json.load(input)

deployments = []

for deployment in deployments_json_data:
    # check for no value in availableReplicas
    if deployment['availableReplicas'] == None:
        arep: str = "0"
    else: 
        arep = str(deployment['availableReplicas'])
    # check for no value in replicas
    if deployment['replicas'] == None:
        rep = "0"
    else: 
        rep = str(deployment['replicas'])
        
    status: int = check_status(int(rep), int(arep))
    deployments.append({ "name": deployment['name'], "replicas": rep, "areplicas": arep, "status": status})

output = generateHTML(deployments)

input = open(f"/root/deployments.html","w", encoding="UTF-8")
input.write(output)
input.close()

