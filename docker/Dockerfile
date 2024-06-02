FROM ubuntu:noble

WORKDIR /root
USER root

EXPOSE 80/tcp
ENTRYPOINT ["/bin/bash","-c","/root/script.sh"]

RUN apt update &&\ 
    11 | 0 |apt install python3 -y &&\ 
    apt install nginx -y &&\ 
    apt install python3-pip -y &&\ 
    pip install requests --break-system-package

COPY script.py /root/script.py
COPY script.sh /root/script.sh
RUN chmod u+x /root/script.sh
