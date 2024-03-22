FROM ubuntu:noble

RUN apt update && apt install python3 -y && apt install jq -y && apt install curl -y && apt install nginx -y && apt install git -y && apt install pip -y

EXPOSE 80/tcp
WORKDIR /root
CMD ["/bin/bash","-c","/root/script.sh"]
USER root

RUN git clone --recursive https://github.com/kubernetes-client/python.git
RUN cd python && python3 setup.py install

COPY script.py /root/script.py
COPY script.sh /root/script.sh
RUN chmod u+x /root/script.sh
