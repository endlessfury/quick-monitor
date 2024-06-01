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

object = ClusterObject("blabla","deployment",2,None,2,1,"image:321")
print(object.status)
